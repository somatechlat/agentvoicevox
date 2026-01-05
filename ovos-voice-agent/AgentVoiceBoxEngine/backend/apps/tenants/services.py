"""
Tenant Service Layer
====================

This module contains all the business logic for tenant and tenant settings
operations. It acts as an intermediary between the API layer (views/endpoints)
and the data layer (models), ensuring that business rules, data consistency,
and transactional integrity are maintained.
"""

from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet

from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
    TenantLimitExceededError,
)

from .models import Tenant, TenantSettings


class TenantService:
    """A service class encapsulating all business logic for Tenant operations."""

    @staticmethod
    def get_by_id(tenant_id: UUID) -> Tenant:
        """
        Retrieves a single tenant by its primary key (ID).

        Args:
            tenant_id: The UUID of the tenant to retrieve.

        Returns:
            The Tenant instance.

        Raises:
            NotFoundError: If a tenant with the specified ID does not exist.
        """
        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise NotFoundError(f"Tenant {tenant_id} not found")

    @staticmethod
    def get_by_slug(slug: str) -> Tenant:
        """
        Retrieves a single tenant by its unique slug.

        Args:
            slug: The URL-friendly slug of the tenant.

        Returns:
            The Tenant instance.

        Raises:
            NotFoundError: If a tenant with the specified slug does not exist.
        """
        try:
            return Tenant.objects.get(slug=slug)
        except Tenant.DoesNotExist:
            raise NotFoundError(f"Tenant with slug '{slug}' not found")

    @staticmethod
    def list_tenants(
        status: Optional[str] = None,
        tier: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[QuerySet, int]:
        """
        Provides a paginated and filterable list of all tenants.

        This method is intended for administrative use, as it queries across
        all tenants.

        Args:
            status: (Optional) Filter tenants by their status (e.g., 'active', 'suspended').
            tier: (Optional) Filter tenants by their billing tier (e.g., 'free', 'pro').
            search: (Optional) A search term to filter tenants by name or slug.
            page: The page number for pagination.
            page_size: The number of items per page.

        Returns:
            A tuple containing:
            - A queryset of Tenant instances for the requested page.
            - An integer representing the total count of tenants matching the filters.
        """
        qs = Tenant.objects.all()

        # Apply filters if provided.
        if status:
            qs = qs.filter(status=status)
        if tier:
            qs = qs.filter(tier=tier)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))

        total = qs.count()

        offset = (page - 1) * page_size
        paginated_qs = qs[offset : offset + page_size]

        return paginated_qs, total

    @staticmethod
    @transaction.atomic
    def create_tenant(
        name: str,
        slug: str,
        tier: str = "free",
        settings: Optional[dict[str, Any]] = None,
    ) -> Tenant:
        """
        Creates a new tenant and its associated default settings in a single transaction.

        This method ensures atomicity for the creation of a Tenant and its
        corresponding TenantSettings object. It also prevents the creation of
        tenants with duplicate slugs.

        Args:
            name: The display name of the new tenant.
            slug: The URL-friendly slug for the new tenant.
            tier: The initial billing tier for the tenant.
            settings: (Optional) A dictionary of initial values for the tenant's JSON settings field.

        Returns:
            The newly created Tenant instance.

        Raises:
            ConflictError: If a tenant with the given slug already exists.
        """
        if Tenant.objects.filter(slug=slug).exists():
            raise ConflictError(f"Tenant with slug '{slug}' already exists")

        # Create the core Tenant object. The `save` method override will set tier limits.
        tenant = Tenant.objects.create(
            name=name,
            slug=slug,
            tier=tier,
            settings=settings or {},
            status=Tenant.Status.PENDING,
        )

        # Automatically create the associated settings record.
        TenantSettings.objects.create(tenant=tenant)

        return tenant

    @staticmethod
    @transaction.atomic
    def update_tenant(
        tenant_id: UUID,
        name: Optional[str] = None,
        settings: Optional[dict[str, Any]] = None,
    ) -> Tenant:
        """
        Updates the name or settings of an existing tenant.

        Args:
            tenant_id: The ID of the tenant to update.
            name: (Optional) The new name for the tenant.
            settings: (Optional) A dictionary of settings to update/add in the JSON field.

        Returns:
            The updated Tenant instance.
        """
        tenant = TenantService.get_by_id(tenant_id)

        if name is not None:
            tenant.name = name
        if settings is not None:
            # `update` provides a safe way to modify the JSON field.
            tenant.settings.update(settings)

        tenant.save()
        return tenant

    @staticmethod
    @transaction.atomic
    def activate_tenant(tenant_id: UUID) -> Tenant:
        """
        Activates a tenant with a 'pending' status.

        This delegates to the `activate` method on the Tenant model.

        Args:
            tenant_id: The ID of the tenant to activate.

        Returns:
            The activated Tenant instance with status 'active'.
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.activate()
        return tenant

    @staticmethod
    @transaction.atomic
    def suspend_tenant(tenant_id: UUID, reason: str = "") -> Tenant:
        """
        Suspends an active tenant, preventing access.

        This delegates to the `suspend` method on the Tenant model.

        Args:
            tenant_id: The ID of the tenant to suspend.
            reason: (Optional) A reason for the suspension, stored in the tenant's settings.

        Returns:
            The suspended Tenant instance with status 'suspended'.
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.suspend(reason)
        return tenant

    @staticmethod
    @transaction.atomic
    def reactivate_tenant(tenant_id: UUID) -> Tenant:
        """
        Reactivates a suspended tenant.

        Sets the status back to 'active' and clears suspension-related data.

        Args:
            tenant_id: The ID of the suspended tenant to reactivate.

        Returns:
            The reactivated Tenant instance.
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.status = Tenant.Status.ACTIVE
        tenant.suspended_at = None
        if "suspension_reason" in tenant.settings:
            del tenant.settings["suspension_reason"]
        tenant.save(update_fields=["status", "suspended_at", "settings", "updated_at"])
        return tenant

    @staticmethod
    @transaction.atomic
    def soft_delete_tenant(tenant_id: UUID) -> Tenant:
        """
        Soft-deletes a tenant by setting its status to 'deleted'.

        This delegates to the `soft_delete` method on the Tenant model.

        Args:
            tenant_id: The ID of the tenant to soft-delete.

        Returns:
            The soft-deleted Tenant instance with status 'deleted'.
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.soft_delete()
        return tenant

    @staticmethod
    @transaction.atomic
    def upgrade_tier(tenant_id: UUID, new_tier: str) -> Tenant:
        """
        Upgrades or downgrades a tenant's subscription tier.

        This delegates to the `upgrade_tier` method on the Tenant model, which also
        handles updating the resource limits.

        Args:
            tenant_id: The ID of the tenant to upgrade.
            new_tier: The target tier (e.g., 'pro', 'enterprise').

        Returns:
            The updated Tenant instance with the new tier.
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.upgrade_tier(new_tier)
        return tenant

    @staticmethod
    def get_tenant_stats(tenant_id: UUID) -> dict[str, Any]:
        """
        Gathers and returns usage and limit statistics for a given tenant.

        This is useful for dashboards and monitoring to see how a tenant's current
        usage compares to their subscription limits.

        Args:
            tenant_id: The ID of the tenant for which to gather stats.

        Returns:
            A dictionary containing the tenant's limits and current usage counts.
        """
        tenant = TenantService.get_by_id(tenant_id)

        # Import here to avoid circular dependency issues at the module level.
        from apps.api_keys.models import APIKey
        from apps.projects.models import Project
        from apps.users.models import User

        stats = {
            "tenant_id": str(tenant.id),
            "tier": tenant.tier,
            "status": tenant.status,
            "limits": {
                "max_users": tenant.max_users,
                "max_projects": tenant.max_projects,
                "max_api_keys": tenant.max_api_keys,
                "max_sessions_per_month": tenant.max_sessions_per_month,
            },
            "usage": {
                "users": User.objects.filter(tenant=tenant).count(),
                "projects": Project.objects.filter(tenant=tenant).count(),
                "api_keys": APIKey.objects.filter(tenant=tenant, revoked_at__isnull=True).count(),
            },
        }

        return stats

    @staticmethod
    def enforce_limit(tenant: Tenant, resource_type: str) -> None:
        """
        Checks if creating a new resource would exceed the tenant's limit.

        This is the primary method to be called before creating a new resource
        (e.g., a User, Project, or APIKey).

        Args:
            tenant: The Tenant instance to check against.
            resource_type: The type of resource being created ('users', 'projects', 'api_keys').

        Raises:
            TenantLimitExceededError: If creating one more resource would exceed the limit.
        """
        # Import locally to avoid circular dependencies.
        from apps.api_keys.models import APIKey
        from apps.projects.models import Project
        from apps.users.models import User

        limit_map = {
            "users": (tenant.max_users, User.objects.filter(tenant=tenant).count()),
            "projects": (tenant.max_projects, Project.objects.filter(tenant=tenant).count()),
            "api_keys": (tenant.max_api_keys, APIKey.objects.filter(tenant=tenant, revoked_at__isnull=True).count()),
        }

        if resource_type not in limit_map:
            return  # No limit defined for this resource type.

        limit, current_count = limit_map[resource_type]

        if current_count >= limit:
            raise TenantLimitExceededError(
                f"Tenant {tenant.slug} has reached the {resource_type} limit of {limit}."
            )


class TenantSettingsService:
    """A service class for operations related to TenantSettings."""

    @staticmethod
    def get_settings(tenant_id: UUID) -> TenantSettings:
        """
        Retrieves the extended settings for a given tenant.

        Args:
            tenant_id: The ID of the tenant whose settings are being requested.

        Returns:
            The TenantSettings instance.

        Raises:
            NotFoundError: If the settings for the specified tenant do not exist.
        """
        try:
            # Use `select_related` to optimize the query by fetching the related Tenant object in the same DB call.
            return TenantSettings.objects.select_related("tenant").get(tenant_id=tenant_id)
        except TenantSettings.DoesNotExist:
            raise NotFoundError(f"Settings for tenant {tenant_id} not found")

    @staticmethod
    @transaction.atomic
    def update_settings(tenant_id: UUID, **kwargs) -> TenantSettings:
        """
        Updates tenant settings from a dictionary of key-value pairs.

        This is a generic update method. For more type-safe updates, prefer
        using specific methods like `update_branding` or `update_security_settings`.

        Args:
            tenant_id: The ID of the tenant to update.
            **kwargs: Key-value pairs of settings to update.

        Returns:
            The updated TenantSettings instance.
        """
        settings = TenantSettingsService.get_settings(tenant_id)

        for key, value in kwargs.items():
            if hasattr(settings, key) and value is not None:
                setattr(settings, key, value)

        settings.save()
        return settings

    @staticmethod
    @transaction.atomic
    def update_branding(
        tenant_id: UUID,
        logo_url: Optional[str] = None,
        favicon_url: Optional[str] = None,
        primary_color: Optional[str] = None,
        secondary_color: Optional[str] = None,
    ) -> TenantSettings:
        """
        Updates the branding-related settings for a tenant.

        This method provides a type-safe way to update only the branding fields
        and uses `update_fields` for an efficient query.

        Args:
            tenant_id: The ID of the tenant to update.
            logo_url: (Optional) The new logo URL.
            favicon_url: (Optional) The new favicon URL.
            primary_color: (Optional) The new primary hex color.
            secondary_color: (Optional) The new secondary hex color.

        Returns:
            The updated TenantSettings instance.
        """
        settings = TenantSettingsService.get_settings(tenant_id)
        update_fields = ["updated_at"]

        if logo_url is not None:
            settings.logo_url = logo_url
            update_fields.append("logo_url")
        if favicon_url is not None:
            settings.favicon_url = favicon_url
            update_fields.append("favicon_url")
        if primary_color is not None:
            settings.primary_color = primary_color
            update_fields.append("primary_color")
        if secondary_color is not None:
            settings.secondary_color = secondary_color
            update_fields.append("secondary_color")

        settings.save(update_fields=update_fields)
        return settings

    # Note: The other update methods (update_voice_defaults, update_security_settings)
    # follow a similar pattern and are omitted here for brevity, but would be
    # documented in the same comprehensive style.
    @staticmethod
    @transaction.atomic
    def update_voice_defaults(
        tenant_id: UUID,
        **kwargs: Any,
    ) -> TenantSettings:
        """
        Updates the tenant's default settings for voice features.

        Args:
            tenant_id: The ID of the tenant to update.
            **kwargs: Key-value pairs of voice settings to update.

        Returns:
            The updated TenantSettings instance.
        """
        settings = TenantSettingsService.get_settings(tenant_id)
        update_fields = ["updated_at"]
        voice_fields = [
            "default_voice_id", "default_stt_model", "default_stt_language",
            "stt_vad_enabled", "stt_beam_size", "default_tts_model",
            "default_llm_provider", "default_llm_model",
            "default_llm_temperature", "default_llm_max_tokens"
        ]
        for key, value in kwargs.items():
            if key in voice_fields and value is not None:
                setattr(settings, key, value)
                update_fields.append(key)
        settings.save(update_fields=update_fields)
        return settings

    @staticmethod
    @transaction.atomic
    def update_security_settings(
        tenant_id: UUID,
        **kwargs: Any,
    ) -> TenantSettings:
        """
        Updates the tenant's security-related settings.

        Args:
            tenant_id: The ID of the tenant to update.
            **kwargs: Key-value pairs of security settings to update.

        Returns:
            The updated TenantSettings instance.
        """
        settings = TenantSettingsService.get_settings(tenant_id)
        update_fields = ["updated_at"]
        security_fields = [
            "require_mfa", "session_timeout_minutes",
            "allowed_ip_ranges", "api_key_expiry_days"
        ]
        for key, value in kwargs.items():
            if key in security_fields and value is not None:
                setattr(settings, key, value)
                update_fields.append(key)
        settings.save(update_fields=update_fields)
        return settings
