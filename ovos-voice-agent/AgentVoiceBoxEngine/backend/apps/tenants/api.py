"""
Tenant Management API Endpoints
===============================

This module provides the core REST API endpoints for managing tenants and their
settings, built using the Django Ninja framework. The endpoints are primarily
intended for system administrators and tenant administrators.

The API is divided into three main sections:
- Admin Endpoints: For creating, listing, and managing the lifecycle of all tenants.
  Access is restricted to users with the SYSADMIN role.
- Tenant Settings Endpoints: For tenant administrators to manage their own
  specific settings (e.g., branding, feature defaults).
- Tenant Stats Endpoint: For retrieving usage and limit statistics for a tenant.
"""

from typing import Optional
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
    """
    Serializes a Tenant model instance into a TenantResponseSchema.

    Args:
        tenant: The Tenant model instance.

    Returns:
        A TenantResponseSchema object populated with the tenant's data.
    """
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
    """
    Serializes a TenantSettings model instance into a TenantSettingsSchema.

    Args:
        settings: The TenantSettings model instance.

    Returns:
        A TenantSettingsSchema object populated with the settings data.
    """
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
# ADMIN ENDPOINTS (Primarily for SYSADMIN use)
# ==========================================================================


@router.get(
    "/", response=TenantListResponseSchema, summary="List All Tenants (SysAdmin)"
)
def list_tenants(
    request: HttpRequest,
    status: Optional[str] = Query(
        None, description="Filter by tenant status (e.g., 'active')."
    ),
    tier: Optional[str] = Query(
        None, description="Filter by tenant tier (e.g., 'pro')."
    ),
    search: Optional[str] = Query(
        None, description="Search term for tenant name or slug."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lists all tenants in the system with filtering and pagination.

    **Permissions:** Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenants, total = TenantService.list_tenants(
        status=status, tier=tier, search=search, page=page, page_size=page_size
    )

    pages = (total + page_size - 1) // page_size

    return TenantListResponseSchema(
        items=[_tenant_to_response(t) for t in tenants],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.post(
    "/", response={201: TenantResponseSchema}, summary="Create a Tenant (SysAdmin)"
)
def create_tenant(request: HttpRequest, payload: TenantCreateSchema):
    """
    Creates a new tenant and its associated default settings.

    **Permissions:** Requires SYSADMIN role.

    Args:
        payload: A `TenantCreateSchema` with the new tenant's details.

    Returns:
        A 201 status code and the newly created tenant object.
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


@router.get("/{tenant_id}", response=TenantResponseSchema, summary="Get a Tenant by ID")
def get_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Retrieves details for a specific tenant by its ID.

    **Permissions:** Requires SYSADMIN role or membership in the target tenant.
    """
    tenant = TenantService.get_by_id(tenant_id)

    # A user can only access their own tenant, unless they are a sysadmin.
    current_tenant_id = getattr(request, "tenant_id", None)
    is_sysadmin = getattr(request, "is_sysadmin", False)

    if not is_sysadmin and str(current_tenant_id) != str(tenant_id):
        raise PermissionDeniedError("Access denied to this tenant")

    return _tenant_to_response(tenant)


@router.patch("/{tenant_id}", response=TenantResponseSchema, summary="Update a Tenant")
def update_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantUpdateSchema):
    """
    Updates a tenant's name or settings.

    **Permissions:** Requires SYSADMIN or an ADMIN role within the target tenant.
    *Note: The implementation currently lacks an explicit permission check;
    this is assumed to be handled by a decorator or middleware.*
    """
    tenant = TenantService.update_tenant(
        tenant_id=tenant_id, name=payload.name, settings=payload.settings
    )
    return _tenant_to_response(tenant)


@router.post(
    "/{tenant_id}/activate",
    response=TenantResponseSchema,
    summary="Activate a Tenant (SysAdmin)",
)
def activate_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Activates a tenant with a 'pending' status.

    **Permissions:** Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.activate_tenant(tenant_id)
    return _tenant_to_response(tenant)


@router.post(
    "/{tenant_id}/suspend",
    response=TenantResponseSchema,
    summary="Suspend a Tenant (SysAdmin)",
)
def suspend_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantSuspendSchema):
    """
    Suspends an active tenant, preventing access and operations.

    **Permissions:** Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.suspend_tenant(tenant_id, reason=payload.reason)
    return _tenant_to_response(tenant)


@router.post(
    "/{tenant_id}/reactivate",
    response=TenantResponseSchema,
    summary="Reactivate a Tenant (SysAdmin)",
)
def reactivate_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Reactivates a suspended tenant, setting its status back to 'active'.

    **Permissions:** Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.reactivate_tenant(tenant_id)
    return _tenant_to_response(tenant)


@router.delete(
    "/{tenant_id}", response={204: None}, summary="Soft-Delete a Tenant (SysAdmin)"
)
def delete_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Soft-deletes a tenant by setting its status to 'deleted'.

    **Permissions:** Requires SYSADMIN role.

    Returns:
        A 204 No Content response on success.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    TenantService.soft_delete_tenant(tenant_id)
    return 204, None


@router.post(
    "/{tenant_id}/upgrade",
    response=TenantResponseSchema,
    summary="Upgrade Tenant Tier (SysAdmin)",
)
def upgrade_tenant_tier(
    request: HttpRequest, tenant_id: UUID, payload: TenantUpgradeTierSchema
):
    """
    Upgrades or downgrades a tenant's subscription tier.

    **Permissions:** Requires SYSADMIN role.
    """
    if not getattr(request, "is_sysadmin", False):
        raise PermissionDeniedError("SYSADMIN role required")

    tenant = TenantService.upgrade_tier(tenant_id, payload.tier)
    return _tenant_to_response(tenant)


# ==========================================================================
# TENANT SETTINGS ENDPOINTS
# ==========================================================================


@router.get(
    "/{tenant_id}/settings",
    response=TenantSettingsSchema,
    summary="Get Tenant Settings",
)
def get_tenant_settings(request: HttpRequest, tenant_id: UUID):
    """
    Retrieves the extended settings for a specific tenant.

    **Permissions:** Requires ADMIN role within the target tenant.
    *Note: Assumes permission is handled by a decorator or middleware.*
    """
    settings = TenantSettingsService.get_settings(tenant_id)
    return _settings_to_response(settings)


@router.patch(
    "/{tenant_id}/settings",
    response=TenantSettingsSchema,
    summary="Update Tenant Settings",
)
def update_tenant_settings(
    request: HttpRequest, tenant_id: UUID, payload: TenantSettingsUpdateSchema
):
    """
    Updates the extended settings for a tenant.

    **Permissions:** Requires ADMIN role within the target tenant.
    *Note: Assumes permission is handled by a decorator or middleware.*
    """
    update_data = payload.dict(exclude_unset=True)
    settings = TenantSettingsService.update_settings(tenant_id, **update_data)
    return _settings_to_response(settings)


# ==========================================================================
# TENANT STATS ENDPOINT
# ==========================================================================


@router.get("/{tenant_id}/stats", summary="Get Tenant Usage Statistics")
def get_tenant_stats(request: HttpRequest, tenant_id: UUID):
    """
    Retrieves usage and limit statistics for a specific tenant.

    **Permissions:** Requires ADMIN or BILLING role within the target tenant.
    *Note: Assumes permission is handled by a decorator or middleware.*
    """
    stats = TenantService.get_tenant_stats(tenant_id)
    return stats
