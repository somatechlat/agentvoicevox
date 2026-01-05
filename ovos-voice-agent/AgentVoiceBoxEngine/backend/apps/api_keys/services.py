"""
API Key Service Layer
=====================

This module contains all the business logic for managing API keys. It provides
functionality for creating, retrieving, updating, revoking, and validating
API keys, ensuring secure and controlled programmatic access to the platform.
All operations are tenant-aware and enforce defined resource limits.
"""

from datetime import timedelta
from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
)
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService
from apps.users.models import User

from .models import APIKey


class APIKeyService:
    """A service class encapsulating all business logic for APIKey operations."""

    @staticmethod
    def get_by_id(key_id: UUID) -> APIKey:
        """
        Retrieves a single API key by its primary key (ID).

        Args:
            key_id: The UUID of the API key to retrieve.

        Returns:
            The APIKey instance.

        Raises:
            NotFoundError: If an API key with the specified ID does not exist.
        """
        try:
            return APIKey.objects.select_related("tenant", "project", "created_by").get(id=key_id)
        except APIKey.DoesNotExist:
            raise NotFoundError(f"API key {key_id} not found")

    @staticmethod
    def get_by_prefix(prefix: str) -> Optional[APIKey]:
        """
        Retrieves an API key by its unique prefix.

        This method uses the `all_objects` manager to perform a system-wide lookup
        by prefix, which is typically done during the authentication process
        before tenant context is fully established.

        Args:
            prefix: The unique prefix of the API key (e.g., 'avb_xxxx').

        Returns:
            The APIKey instance if found, otherwise None.
        """
        try:
            return APIKey.all_objects.select_related("tenant", "project").get(key_prefix=prefix)
        except APIKey.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def validate_key(api_key: str, ip_address: Optional[str] = None) -> dict[str, Any]:
        """
        Validates an API key and returns essential key data for authentication.

        This comprehensive validation process involves:
        1.  Checking the key's format and length.
        2.  Extracting the prefix and hashing the provided key.
        3.  Retrieving the APIKey record by prefix (using `all_objects` as tenant context may not be set yet).
        4.  Comparing the stored hash with the computed hash.
        5.  Checking if the key is revoked or expired.
        6.  Verifying the status of the associated tenant.
        7.  Recording key usage (last used time, IP, and count).

        Args:
            api_key: The full, plaintext API key string provided by the client.
            ip_address: (Optional) The client's IP address, for usage tracking.

        Returns:
            A dictionary containing validated API key details, including `tenant_id`,
            `project_id`, `scopes`, and `rate_limit_tier`.

        Raises:
            AuthenticationError: If the key is invalid, revoked, expired, or if the
                                 associated tenant is inactive. The `error_code`
                                 attribute provides specific failure reasons.
        """
        # 1. Check API key format and length.
        if not api_key.startswith("avb_") or len(api_key) != 68:
            raise AuthenticationError("Invalid API key format", error_code="invalid_api_key")

        # 2. Extract prefix and hash the full key.
        prefix = api_key[:12]
        key_hash = APIKey.hash_key(api_key)

        # 3. Find API key by prefix across all tenants.
        key = APIKeyService.get_by_prefix(prefix)
        if not key:
            raise AuthenticationError("Invalid API key", error_code="invalid_api_key")

        # 4. Verify the hash to ensure the key is correct.
        if key.key_hash != key_hash:
            raise AuthenticationError("Invalid API key", error_code="invalid_api_key")

        # 5. Check if the key has been explicitly revoked.
        if key.is_revoked:
            raise AuthenticationError("API key has been revoked", error_code="api_key_revoked")

        # 6. Check if the key has passed its expiration date.
        if key.is_expired:
            raise AuthenticationError("API key has expired", error_code="api_key_expired")

        # 7. Check the status of the tenant associated with the API key.
        if not key.tenant.is_active:
            raise AuthenticationError(
                "Associated tenant is not active",
                error_code="tenant_inactive",
            )

        # 8. Record successful API key usage.
        key.record_usage(ip_address)

        return {
            "api_key_id": key.id,
            "key_id": key.id,  # Alias for backwards compatibility.
            "tenant_id": key.tenant_id,
            "tenant": key.tenant,
            "project_id": key.project_id,
            "project": key.project,
            "scopes": key.scopes,
            "rate_limit_tier": key.rate_limit_tier,
            "rate_limit": key.get_rate_limit(),
        }

    @staticmethod
    def list_keys(
        tenant: Optional[Tenant] = None,
        project_id: Optional[UUID] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[QuerySet, int]:
        """
        Provides a paginated and filterable list of API keys.

        If a `tenant` is provided, it lists keys for that specific tenant
        (typically for admin views). If `tenant` is None, it lists keys for
        the current user's tenant (default tenant-scoped behavior).

        Args:
            tenant: (Optional) The Tenant for which to list API keys.
            project_id: (Optional) Filter keys associated with a specific project.
            is_active: (Optional) Filter keys by their active status (not revoked, not expired).
            search: (Optional) A search term for key name or prefix.
            page: The page number for pagination.
            page_size: The number of items per page.

        Returns:
            A tuple containing:
            - A queryset of APIKey instances for the requested page.
            - An integer representing the total count of keys matching the filters.
        """
        if tenant:
            # For admin views, filter by explicit tenant.
            qs = APIKey.all_objects.filter(tenant=tenant)
        else:
            # For tenant-scoped views, use the default manager.
            qs = APIKey.objects.all()

        qs = qs.select_related("tenant", "project", "created_by")

        if project_id:
            qs = qs.filter(project_id=project_id)
        if is_active is not None:
            now = timezone.now()
            if is_active:
                qs = qs.filter(revoked_at__isnull=True).exclude(expires_at__lt=now)
            else:
                # Keys are inactive if revoked OR expired.
                qs = qs.filter(Q(revoked_at__isnull=False) | Q(expires_at__lt=now))
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(key_prefix__icontains=search))

        total = qs.count()
        offset = (page - 1) * page_size
        paginated_qs = qs[offset : offset + page_size]

        return paginated_qs, total

    @staticmethod
    @transaction.atomic
    def create_key(
        tenant: Tenant,
        name: str,
        created_by: User,
        description: str = "",
        project_id: Optional[UUID] = None,
        scopes: Optional[list[str]] = None,
        rate_limit_tier: str = "standard",
        expires_in_days: Optional[int] = None,
    ) -> tuple[APIKey, str]:
        """
        Generates and creates a new API key for a tenant.

        This method ensures the new key adheres to tenant limits and has valid
        scopes and rate limit tiers. The full plaintext key is returned
        alongside the database object.

        Args:
            tenant: The Tenant for which the API key is being created.
            name: A human-readable name for the API key.
            created_by: The User who is creating the API key.
            description: (Optional) A description for the key.
            project_id: (Optional) The UUID of the project to associate the key with.
            scopes: (Optional) A list of scopes the key should have. Defaults to `['realtime']` if None.
            rate_limit_tier: The rate limit tier for the key.
            expires_in_days: (Optional) Number of days until the key expires.

        Returns:
            A tuple containing:
            - The newly created APIKey model instance.
            - The full plaintext API key string (should be stored securely by the caller).

        Raises:
            TenantLimitExceededError: If the tenant has reached its API key limit.
            ValidationError: If invalid scopes, rate limit tier, or project ID are provided.
        """
        # 1. Enforce tenant API key limit.
        TenantService.enforce_limit(tenant, "api_keys")

        # 2. Validate and normalize scopes.
        if scopes is None:
            scopes = ["realtime"]  # Default scope.
        valid_scopes = [s.value for s in APIKey.Scope]
        if not all(scope in valid_scopes for scope in scopes):
            invalid_scope = next((s for s in scopes if s not in valid_scopes), None)
            raise ValidationError(
                f"Invalid scope: {invalid_scope}. Valid scopes are: {', '.join(valid_scopes)}"
            )

        # 3. Validate rate limit tier.
        if rate_limit_tier not in APIKey.RateLimitTier.values:
            raise ValidationError(f"Invalid rate limit tier: {rate_limit_tier}")

        # 4. Validate project association if provided.
        project = None
        if project_id:
            from apps.projects.models import Project  # Local import to avoid circular dependency.

            try:
                # Use all_objects to check across tenants in case of admin action, but filter by tenant.
                project = Project.all_objects.get(id=project_id, tenant=tenant)
            except Project.DoesNotExist:
                raise ValidationError(f"Project {project_id} not found for this tenant.")

        # 5. Generate the key components.
        full_key, prefix, key_hash = APIKey.generate_key()

        # 6. Calculate expiration date if applicable.
        expires_at = None
        if expires_in_days is not None:
            if expires_in_days <= 0:
                raise ValidationError("Expiration days must be positive.")
            expires_at = timezone.now() + timedelta(days=expires_in_days)

        # 7. Create the APIKey record in the database.
        api_key = APIKey(
            tenant=tenant,
            name=name,
            description=description,
            key_prefix=prefix,
            key_hash=key_hash,
            project=project,
            scopes=scopes,
            rate_limit_tier=rate_limit_tier,
            expires_at=expires_at,
            created_by=created_by,
        )
        api_key.save()

        return api_key, full_key

    @staticmethod
    @transaction.atomic
    def update_key(
        key_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        scopes: Optional[list[str]] = None,
        rate_limit_tier: Optional[str] = None,
    ) -> APIKey:
        """
        Updates an existing API key's details.

        Args:
            key_id: The UUID of the API key to update.
            name: (Optional) The new name for the key.
            description: (Optional) The new description for the key.
            scopes: (Optional) A new list of scopes for the key.
            rate_limit_tier: (Optional) The new rate limit tier for the key.

        Returns:
            The updated APIKey instance.

        Raises:
            NotFoundError: If the API key is not found.
            ValidationError: If invalid scopes or rate limit tier are provided.
        """
        api_key = APIKeyService.get_by_id(key_id)

        if name is not None:
            api_key.name = name
        if description is not None:
            api_key.description = description
        if scopes is not None:
            valid_scopes = [s.value for s in APIKey.Scope]
            if not all(scope in valid_scopes for scope in scopes):
                invalid_scope = next((s for s in scopes if s not in valid_scopes), None)
                raise ValidationError(
                    f"Invalid scope: {invalid_scope}. Valid scopes are: {', '.join(valid_scopes)}"
                )
            api_key.scopes = scopes
        if rate_limit_tier is not None:
            if rate_limit_tier not in APIKey.RateLimitTier.values:
                raise ValidationError(f"Invalid rate limit tier: {rate_limit_tier}")
            api_key.rate_limit_tier = rate_limit_tier

        api_key.save()
        return api_key

    @staticmethod
    @transaction.atomic
    def revoke_key(key_id: UUID, user: User, reason: str = "") -> APIKey:
        """
        Revokes an API key, making it inactive immediately.

        Records the user who initiated the revocation and an optional reason.

        Args:
            key_id: The UUID of the API key to revoke.
            user: The User instance who initiated the revocation.
            reason: (Optional) A text description for the reason of revocation.

        Returns:
            The revoked APIKey instance.

        Raises:
            NotFoundError: If the API key is not found.
        """
        api_key = APIKeyService.get_by_id(key_id)
        api_key.revoke(user=user, reason=reason)
        return api_key

    @staticmethod
    @transaction.atomic
    def rotate_key(
        key_id: UUID,
        user: User,
        grace_period_hours: int = 0,
    ) -> tuple[APIKey, str, Optional[APIKey]]:
        """
        Rotates an existing API key by generating a new one with the same
        configuration and revoking the old one.

        Optionally, the old key can remain active for a specified grace period.
        This entire operation is atomic.

        Args:
            key_id: The UUID of the API key to rotate.
            user: The User instance who initiated the rotation.
            grace_period_hours: (Optional) Number of hours the old key remains active.

        Returns:
            A tuple containing:
            - `new_key` (APIKey): The newly created APIKey instance.
            - `full_key` (str): The full plaintext of the new API key.
            - `old_key_grace_period` (Optional[APIKey]): The old key instance if a grace period was applied, otherwise None.

        Raises:
            NotFoundError: If the API key to rotate is not found.
        """
        old_key = APIKeyService.get_by_id(key_id)

        # Create a new key with identical settings.
        new_key, full_new_key = APIKeyService.create_key(
            tenant=old_key.tenant,
            name=old_key.name,
            description=old_key.description,
            project_id=old_key.project_id,
            scopes=old_key.scopes,
            rate_limit_tier=old_key.rate_limit_tier,
            expires_in_days=None,  # New keys do not inherit expiration from old keys by default.
            created_by=user,
        )

        if grace_period_hours > 0:
            # If a grace period is specified, the old key is set to expire.
            old_key.expires_at = timezone.now() + timedelta(hours=grace_period_hours)
            old_key.save(update_fields=["expires_at", "updated_at"])
            return new_key, full_new_key, old_key
        else:
            # Otherwise, revoke the old key immediately.
            old_key.revoke(user=user, reason="Rotated (no grace period)")
            return new_key, full_new_key, None

    @staticmethod
    @transaction.atomic
    def delete_key(key_id: UUID) -> None:
        """
        Permanently deletes an API key from the database.

        Args:
            key_id: The UUID of the API key to delete.

        Raises:
            NotFoundError: If the API key is not found.
        """
        api_key = APIKeyService.get_by_id(key_id)
        api_key.delete()

    @staticmethod
    def count_active_keys(tenant: Tenant) -> int:
        """
        Counts the number of active API keys for a specific tenant.

        An active key is one that is not revoked and has not expired.

        Args:
            tenant: The Tenant for which to count active keys.

        Returns:
            An integer representing the count of active API keys.
        """
        return (
            APIKey.all_objects.filter(
                tenant=tenant,
                revoked_at__isnull=True,
            )
            .exclude(
                expires_at__lt=timezone.now(),
            )
            .count()
        )
