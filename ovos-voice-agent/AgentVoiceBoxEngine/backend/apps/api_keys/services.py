"""
API Key service layer.

Contains all business logic for API key operations.
"""
from datetime import timedelta
from typing import Any, Dict, Optional, Tuple
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    TenantLimitExceededError,
    ValidationError,
)
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService
from apps.users.models import User

from .models import APIKey


class APIKeyService:
    """Service class for API key operations."""

    @staticmethod
    def get_by_id(key_id: UUID) -> APIKey:
        """
        Get API key by ID.

        Raises:
            NotFoundError: If key not found
        """
        try:
            return APIKey.objects.select_related(
                "tenant", "project", "created_by"
            ).get(id=key_id)
        except APIKey.DoesNotExist:
            raise NotFoundError(f"API key {key_id} not found")

    @staticmethod
    def get_by_prefix(prefix: str) -> Optional[APIKey]:
        """
        Get API key by prefix.

        Returns:
            APIKey or None if not found
        """
        try:
            return APIKey.all_objects.select_related(
                "tenant", "project"
            ).get(key_prefix=prefix)
        except APIKey.DoesNotExist:
            return None

    @staticmethod
    def validate_key(api_key: str, ip_address: str = None) -> Dict[str, Any]:
        """
        Validate an API key and return key data.

        Args:
            api_key: The full API key string
            ip_address: Client IP address for usage tracking

        Returns:
            Dictionary with key data

        Raises:
            AuthenticationError: If key is invalid, expired, or revoked
        """
        # Check format
        if not api_key.startswith("avb_") or len(api_key) != 68:
            raise AuthenticationError("Invalid API key format", error_code="invalid_api_key")

        # Get prefix and hash
        prefix = api_key[:12]
        key_hash = APIKey.hash_key(api_key)

        # Find key by prefix
        key = APIKeyService.get_by_prefix(prefix)
        if not key:
            raise AuthenticationError("Invalid API key", error_code="invalid_api_key")

        # Verify hash
        if key.key_hash != key_hash:
            raise AuthenticationError("Invalid API key", error_code="invalid_api_key")

        # Check if revoked
        if key.is_revoked:
            raise AuthenticationError("API key has been revoked", error_code="api_key_revoked")

        # Check if expired
        if key.is_expired:
            raise AuthenticationError("API key has expired", error_code="api_key_expired")

        # Check tenant status
        if not key.tenant.is_active:
            raise AuthenticationError(
                "Tenant is not active",
                error_code="tenant_inactive",
            )

        # Record usage
        key.record_usage(ip_address)

        return {
            "api_key_id": key.id,
            "key_id": key.id,  # Alias for backwards compatibility
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
    ) -> Tuple[QuerySet, int]:
        """
        List API keys with filtering and pagination.

        Returns:
            Tuple of (queryset, total_count)
        """
        if tenant:
            qs = APIKey.all_objects.filter(tenant=tenant)
        else:
            qs = APIKey.objects.all()

        qs = qs.select_related("tenant", "project", "created_by")

        # Apply filters
        if project_id:
            qs = qs.filter(project_id=project_id)
        if is_active is not None:
            now = timezone.now()
            if is_active:
                qs = qs.filter(revoked_at__isnull=True).exclude(expires_at__lt=now)
            else:
                qs = qs.filter(Q(revoked_at__isnull=False) | Q(expires_at__lt=now))
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(key_prefix__icontains=search))

        # Get total count before pagination
        total = qs.count()

        # Apply pagination
        offset = (page - 1) * page_size
        qs = qs[offset : offset + page_size]

        return qs, total

    @staticmethod
    @transaction.atomic
    def create_key(
        tenant: Tenant,
        name: str,
        created_by: User,
        description: str = "",
        project_id: Optional[UUID] = None,
        scopes: list = None,
        rate_limit_tier: str = "standard",
        expires_in_days: Optional[int] = None,
    ) -> Tuple[APIKey, str]:
        """
        Create a new API key.

        Returns:
            Tuple of (APIKey, full_key)

        Raises:
            TenantLimitExceededError: If tenant API key limit reached
            ValidationError: If invalid parameters
        """
        # Check tenant API key limit
        current_count = APIKey.all_objects.filter(
            tenant=tenant,
            revoked_at__isnull=True,
        ).count()
        TenantService.enforce_limit(tenant, "api_keys", current_count)

        # Validate scopes
        if scopes is None:
            scopes = ["realtime"]
        valid_scopes = [s.value for s in APIKey.Scope]
        for scope in scopes:
            if scope not in valid_scopes:
                raise ValidationError(f"Invalid scope: {scope}")

        # Validate rate limit tier
        if rate_limit_tier not in APIKey.RateLimitTier.values:
            raise ValidationError(f"Invalid rate limit tier: {rate_limit_tier}")

        # Validate project if provided
        project = None
        if project_id:
            from apps.projects.models import Project
            try:
                project = Project.all_objects.get(id=project_id, tenant=tenant)
            except Project.DoesNotExist:
                raise ValidationError(f"Project {project_id} not found")

        # Generate key
        full_key, prefix, key_hash = APIKey.generate_key()

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = timezone.now() + timedelta(days=expires_in_days)

        # Create key
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
        scopes: Optional[list] = None,
        rate_limit_tier: Optional[str] = None,
    ) -> APIKey:
        """
        Update API key details.

        Raises:
            NotFoundError: If key not found
            ValidationError: If invalid parameters
        """
        api_key = APIKeyService.get_by_id(key_id)

        if name is not None:
            api_key.name = name
        if description is not None:
            api_key.description = description
        if scopes is not None:
            valid_scopes = [s.value for s in APIKey.Scope]
            for scope in scopes:
                if scope not in valid_scopes:
                    raise ValidationError(f"Invalid scope: {scope}")
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
        Revoke an API key.

        Raises:
            NotFoundError: If key not found
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
    ) -> Tuple[APIKey, str, Optional[APIKey]]:
        """
        Rotate an API key.

        Creates a new key and optionally keeps the old key active
        for a grace period.

        Returns:
            Tuple of (new_key, full_key, old_key_if_grace_period)

        Raises:
            NotFoundError: If key not found
        """
        old_key = APIKeyService.get_by_id(key_id)

        # Create new key with same settings
        new_key, full_key = APIKeyService.create_key(
            tenant=old_key.tenant,
            name=old_key.name,
            description=old_key.description,
            project_id=old_key.project_id,
            scopes=old_key.scopes,
            rate_limit_tier=old_key.rate_limit_tier,
            expires_in_days=None,  # New key doesn't inherit expiration
            created_by=user,
        )

        if grace_period_hours > 0:
            # Set old key to expire after grace period
            old_key.expires_at = timezone.now() + timedelta(hours=grace_period_hours)
            old_key.save(update_fields=["expires_at", "updated_at"])
            return new_key, full_key, old_key
        else:
            # Revoke old key immediately
            old_key.revoke(user=user, reason="Rotated")
            return new_key, full_key, None

    @staticmethod
    @transaction.atomic
    def delete_key(key_id: UUID) -> None:
        """
        Delete an API key permanently.

        Raises:
            NotFoundError: If key not found
        """
        api_key = APIKeyService.get_by_id(key_id)
        api_key.delete()

    @staticmethod
    def count_active_keys(tenant: Tenant) -> int:
        """
        Count active API keys in a tenant.
        """
        return APIKey.all_objects.filter(
            tenant=tenant,
            revoked_at__isnull=True,
        ).exclude(
            expires_at__lt=timezone.now(),
        ).count()
