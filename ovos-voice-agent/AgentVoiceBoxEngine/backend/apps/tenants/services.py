"""
Tenant service layer.

Contains all business logic for tenant operations.
Separates business logic from API endpoints.
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.db import transaction
from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
    TenantLimitExceededError,
)

from .models import Tenant, TenantSettings


class TenantService:
    """Service class for tenant operations."""

    @staticmethod
    def get_by_id(tenant_id: UUID) -> Tenant:
        """
        Get tenant by ID.

        Raises:
            NotFoundError: If tenant not found
        """
        try:
            return Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise NotFoundError(f"Tenant {tenant_id} not found")

    @staticmethod
    def get_by_slug(slug: str) -> Tenant:
        """
        Get tenant by slug.

        Raises:
            NotFoundError: If tenant not found
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
    ) -> Tuple[QuerySet, int]:
        """
        List tenants with filtering and pagination.

        Returns:
            Tuple of (queryset, total_count)
        """
        qs = Tenant.objects.all()

        # Apply filters
        if status:
            qs = qs.filter(status=status)
        if tier:
            qs = qs.filter(tier=tier)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))

        # Get total count before pagination
        total = qs.count()

        # Apply pagination
        offset = (page - 1) * page_size
        qs = qs[offset : offset + page_size]

        return qs, total

    @staticmethod
    @transaction.atomic
    def create_tenant(
        name: str,
        slug: str,
        tier: str = "free",
        settings: Optional[Dict[str, Any]] = None,
    ) -> Tenant:
        """
        Create a new tenant.

        Raises:
            ConflictError: If slug already exists
        """
        # Check for duplicate slug
        if Tenant.objects.filter(slug=slug).exists():
            raise ConflictError(f"Tenant with slug '{slug}' already exists")

        # Create tenant
        tenant = Tenant.objects.create(
            name=name,
            slug=slug,
            tier=tier,
            settings=settings or {},
            status=Tenant.Status.PENDING,
        )

        # Create default settings
        TenantSettings.objects.create(tenant=tenant)

        return tenant

    @staticmethod
    @transaction.atomic
    def update_tenant(
        tenant_id: UUID,
        name: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
    ) -> Tenant:
        """
        Update tenant details.

        Raises:
            NotFoundError: If tenant not found
        """
        tenant = TenantService.get_by_id(tenant_id)

        if name is not None:
            tenant.name = name
        if settings is not None:
            tenant.settings.update(settings)

        tenant.save()
        return tenant

    @staticmethod
    @transaction.atomic
    def activate_tenant(tenant_id: UUID) -> Tenant:
        """
        Activate a pending tenant.

        Raises:
            NotFoundError: If tenant not found
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.activate()
        return tenant

    @staticmethod
    @transaction.atomic
    def suspend_tenant(tenant_id: UUID, reason: str = "") -> Tenant:
        """
        Suspend a tenant.

        Raises:
            NotFoundError: If tenant not found
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.suspend(reason)
        return tenant

    @staticmethod
    @transaction.atomic
    def reactivate_tenant(tenant_id: UUID) -> Tenant:
        """
        Reactivate a suspended tenant.

        Raises:
            NotFoundError: If tenant not found
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
        Soft delete a tenant.

        Raises:
            NotFoundError: If tenant not found
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.soft_delete()
        return tenant

    @staticmethod
    @transaction.atomic
    def upgrade_tier(tenant_id: UUID, new_tier: str) -> Tenant:
        """
        Upgrade tenant to a new tier.

        Raises:
            NotFoundError: If tenant not found
            ValueError: If tier is invalid
        """
        tenant = TenantService.get_by_id(tenant_id)
        tenant.upgrade_tier(new_tier)
        return tenant

    @staticmethod
    def get_tenant_stats(tenant_id: UUID) -> Dict[str, Any]:
        """
        Get tenant statistics.

        Returns:
            Dictionary with tenant stats
        """
        tenant = TenantService.get_by_id(tenant_id)

        # Import here to avoid circular imports
        from apps.projects.models import Project
        from apps.api_keys.models import APIKey
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
    def check_limit(tenant: Tenant, resource_type: str, current_count: int) -> bool:
        """
        Check if tenant has reached a resource limit.

        Args:
            tenant: Tenant instance
            resource_type: Type of resource (users, projects, api_keys)
            current_count: Current count of resources

        Returns:
            True if within limits, False if limit exceeded
        """
        limit_map = {
            "users": tenant.max_users,
            "projects": tenant.max_projects,
            "api_keys": tenant.max_api_keys,
        }

        limit = limit_map.get(resource_type)
        if limit is None:
            return True

        return current_count < limit

    @staticmethod
    def enforce_limit(tenant: Tenant, resource_type: str, current_count: int) -> None:
        """
        Enforce tenant resource limit, raising exception if exceeded.

        Args:
            tenant: Tenant instance
            resource_type: Type of resource (users, projects, api_keys)
            current_count: Current count of resources

        Raises:
            TenantLimitExceededError: If limit is exceeded
        """
        limit_map = {
            "users": tenant.max_users,
            "projects": tenant.max_projects,
            "api_keys": tenant.max_api_keys,
        }

        limit = limit_map.get(resource_type)
        if limit is None:
            return

        if current_count >= limit:
            raise TenantLimitExceededError(
                f"Tenant {tenant.slug} has reached the {resource_type} limit ({limit})"
            )


class TenantSettingsService:
    """Service class for tenant settings operations."""

    @staticmethod
    def get_settings(tenant_id: UUID) -> TenantSettings:
        """
        Get tenant settings.

        Raises:
            NotFoundError: If tenant or settings not found
        """
        try:
            return TenantSettings.objects.select_related("tenant").get(tenant_id=tenant_id)
        except TenantSettings.DoesNotExist:
            raise NotFoundError(f"Settings for tenant {tenant_id} not found")

    @staticmethod
    @transaction.atomic
    def update_settings(tenant_id: UUID, **kwargs) -> TenantSettings:
        """
        Update tenant settings.

        Raises:
            NotFoundError: If tenant or settings not found
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
        Update tenant branding settings.

        Raises:
            NotFoundError: If tenant or settings not found
        """
        settings = TenantSettingsService.get_settings(tenant_id)

        if logo_url is not None:
            settings.logo_url = logo_url
        if favicon_url is not None:
            settings.favicon_url = favicon_url
        if primary_color is not None:
            settings.primary_color = primary_color
        if secondary_color is not None:
            settings.secondary_color = secondary_color

        settings.save(
            update_fields=[
                "logo_url",
                "favicon_url",
                "primary_color",
                "secondary_color",
                "updated_at",
            ]
        )
        return settings

    @staticmethod
    @transaction.atomic
    def update_voice_defaults(
        tenant_id: UUID,
        default_voice_id: Optional[str] = None,
        default_stt_model: Optional[str] = None,
        default_tts_model: Optional[str] = None,
        default_llm_provider: Optional[str] = None,
        default_llm_model: Optional[str] = None,
    ) -> TenantSettings:
        """
        Update tenant voice defaults.

        Raises:
            NotFoundError: If tenant or settings not found
        """
        settings = TenantSettingsService.get_settings(tenant_id)

        if default_voice_id is not None:
            settings.default_voice_id = default_voice_id
        if default_stt_model is not None:
            settings.default_stt_model = default_stt_model
        if default_tts_model is not None:
            settings.default_tts_model = default_tts_model
        if default_llm_provider is not None:
            settings.default_llm_provider = default_llm_provider
        if default_llm_model is not None:
            settings.default_llm_model = default_llm_model

        settings.save(
            update_fields=[
                "default_voice_id",
                "default_stt_model",
                "default_tts_model",
                "default_llm_provider",
                "default_llm_model",
                "updated_at",
            ]
        )
        return settings

    @staticmethod
    @transaction.atomic
    def update_security_settings(
        tenant_id: UUID,
        require_mfa: Optional[bool] = None,
        session_timeout_minutes: Optional[int] = None,
        allowed_ip_ranges: Optional[List[str]] = None,
        api_key_expiry_days: Optional[int] = None,
    ) -> TenantSettings:
        """
        Update tenant security settings.

        Raises:
            NotFoundError: If tenant or settings not found
        """
        settings = TenantSettingsService.get_settings(tenant_id)

        if require_mfa is not None:
            settings.require_mfa = require_mfa
        if session_timeout_minutes is not None:
            settings.session_timeout_minutes = session_timeout_minutes
        if allowed_ip_ranges is not None:
            settings.allowed_ip_ranges = allowed_ip_ranges
        if api_key_expiry_days is not None:
            settings.api_key_expiry_days = api_key_expiry_days

        settings.save(
            update_fields=[
                "require_mfa",
                "session_timeout_minutes",
                "allowed_ip_ranges",
                "api_key_expiry_days",
                "updated_at",
            ]
        )
        return settings
