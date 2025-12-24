"""
Tenant API endpoints using Django Ninja.

Provides REST API for tenant management operations.
"""
from typing import List, Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError

from .models import Tenant, TenantSettings
from .schemas import (
    TenantCreateSchema,
    TenantListResponseSchema,
    TenantResponseSchema,
    TenantSettingsSchema,
    TenantSettingsUpdateSchema,
    TenantSuspendSchema,
    TenantUpdateSchema,
    TenantUpgradeTierSchema,
)
from .services import TenantService, TenantSettingsService

router = Router(tags=["Tenants"])


def _tenant_to_response(tenant: Tenant) -> TenantResponseSchema:
    """Convert Tenant model to response schema."""
    return TenantResponseSchema(
        id=tenant.id,
        name=tenant.name,
        slug=tenant.slug,
        tier=tenant.tier,
        status=tenant.status,
        billing_id=tenant.billing_id,
        settings=tenant.settings,
        max_users=tenant.max_users,
        max_projects=tenant.max_projects,
        max_api_keys=tenant.max_api_keys,
        max_sessions_per_month=tenant.max_sessions_per_month,
        created_at=tenant.created_at,
        updated_at=tenant.updated_at,
        activated_at=tenant.activated_at,
        suspended_at=tenant.suspended_at,
    )


def _settings_to_response(settings: TenantSettings) -> TenantSettingsSchema:
    """Convert TenantSettings model to response schema."""
    return TenantSettingsSchema(
        logo_url=settings.logo_url,
        favicon_url=settings.favicon_url,
        primary_color=settings.primary_color,
        secondary_color=settings.secondary_color,
        default_voice_id=settings.default_voice_id,
        default_stt_model=settings.default_stt_model,
        default_tts_model=settings.default_tts_model,
        default_llm_provider=settings.default_llm_provider,
        default_llm_model=settings.default_llm_model,
        webhook_url=settings.webhook_url,
        email_notifications=settings.email_notifications,
        slack_webhook_url=settings.slack_webhook_url,
        require_mfa=settings.require_mfa,
        session_timeout_minutes=settings.session_timeout_minutes,
        allowed_ip_ranges=settings.allowed_ip_ranges,
        api_key_expiry_days=settings.api_key_expiry_days,
    )


# ==========================================================================
# ADMIN ENDPOINTS (SYSADMIN only)
# ==========================================================================


@router.get("/", response=TenantListResponseSchema)
def list_tenants(
    request: HttpRequest,
    status: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    List all tenants with filtering and pagination.

    Requires SYSADMIN role.
    """
    # Check SYSADMIN permission (will be enforced by SpiceDB decorator later)
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenants, total = TenantService.list_tenants(
        status=status,
        tier=tier,
        search=search,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size

    return TenantListResponseSchema(
        items=[_tenant_to_response(t) for t in tenants],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post("/", response={201: TenantResponseSchema})
def create_tenant(request: HttpRequest, payload: TenantCreateSchema):
    """
    Create a new tenant.

    Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.create_tenant(
        name=payload.name,
        slug=payload.slug,
        tier=payload.tier,
        settings=payload.settings,
    )

    return 201, _tenant_to_response(tenant)


@router.get("/{tenant_id}", response=TenantResponseSchema)
def get_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Get tenant by ID.

    Requires SYSADMIN role or membership in the tenant.
    """
    tenant = TenantService.get_by_id(tenant_id)

    # Check permission: SYSADMIN or tenant member
    current_tenant_id = getattr(request, "tenant_id", None)
    is_sysadmin = getattr(request, "is_sysadmin", False)

    if not is_sysadmin and str(current_tenant_id) != str(tenant_id):
        raise PermissionDeniedError("Access denied to this tenant")

    return _tenant_to_response(tenant)


@router.patch("/{tenant_id}", response=TenantResponseSchema)
def update_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantUpdateSchema):
    """
    Update tenant details.

    Requires SYSADMIN or ADMIN role in the tenant.
    """
    # Permission check will be enforced by SpiceDB decorator
    tenant = TenantService.update_tenant(
        tenant_id=tenant_id,
        name=payload.name,
        settings=payload.settings,
    )

    return _tenant_to_response(tenant)


@router.post("/{tenant_id}/activate", response=TenantResponseSchema)
def activate_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Activate a pending tenant.

    Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.activate_tenant(tenant_id)
    return _tenant_to_response(tenant)


@router.post("/{tenant_id}/suspend", response=TenantResponseSchema)
def suspend_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantSuspendSchema):
    """
    Suspend a tenant.

    Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.suspend_tenant(tenant_id, reason=payload.reason)
    return _tenant_to_response(tenant)


@router.post("/{tenant_id}/reactivate", response=TenantResponseSchema)
def reactivate_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Reactivate a suspended tenant.

    Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.reactivate_tenant(tenant_id)
    return _tenant_to_response(tenant)


@router.delete("/{tenant_id}", response={204: None})
def delete_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Soft delete a tenant.

    Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    TenantService.soft_delete_tenant(tenant_id)
    return 204, None


@router.post("/{tenant_id}/upgrade", response=TenantResponseSchema)
def upgrade_tenant_tier(
    request: HttpRequest, tenant_id: UUID, payload: TenantUpgradeTierSchema
):
    """
    Upgrade tenant to a new tier.

    Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.upgrade_tier(tenant_id, payload.tier)
    return _tenant_to_response(tenant)


# ==========================================================================
# TENANT SETTINGS ENDPOINTS
# ==========================================================================


@router.get("/{tenant_id}/settings", response=TenantSettingsSchema)
def get_tenant_settings(request: HttpRequest, tenant_id: UUID):
    """
    Get tenant settings.

    Requires ADMIN role in the tenant.
    """
    settings = TenantSettingsService.get_settings(tenant_id)
    return _settings_to_response(settings)


@router.patch("/{tenant_id}/settings", response=TenantSettingsSchema)
def update_tenant_settings(
    request: HttpRequest, tenant_id: UUID, payload: TenantSettingsUpdateSchema
):
    """
    Update tenant settings.

    Requires ADMIN role in the tenant.
    """
    update_data = payload.dict(exclude_unset=True)
    settings = TenantSettingsService.update_settings(tenant_id, **update_data)
    return _settings_to_response(settings)


# ==========================================================================
# TENANT STATS ENDPOINT
# ==========================================================================


@router.get("/{tenant_id}/stats")
def get_tenant_stats(request: HttpRequest, tenant_id: UUID):
    """
    Get tenant statistics and usage.

    Requires ADMIN or BILLING role in the tenant.
    """
    stats = TenantService.get_tenant_stats(tenant_id)
    return stats
