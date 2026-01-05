"""
System Administration API for Tenant Management
===============================================

This module provides a dedicated set of API endpoints for system-level
administration of tenants. All operations defined here are strictly limited
to users with the SYSADMIN role.

This API handles the full lifecycle of tenants, from creation to deletion,
and is separate from the tenant-facing management API.
"""

import math
from typing import Optional
from uuid import UUID

from django.http import HttpRequest
from ninja import Query, Router

from apps.core.exceptions import FeatureNotImplementedError, PermissionDeniedError

from .schemas import (
    TenantCreateSchema,
    TenantListResponseSchema,
    TenantResponseSchema,
    TenantSuspendSchema,
    TenantUpdateSchema,
    TenantUpgradeTierSchema,
)
from .services import TenantService

# Router for the admin-specific tenant endpoints.
router = Router(tags=["Admin - Tenants"])


def require_sysadmin(request: HttpRequest) -> None:
    """
    Checks if the requesting user has the 'sysadmin' role in their JWT.

    This function serves as a reusable permission check for all endpoints in this
    module, ensuring that only system administrators can perform these actions.

    Args:
        request: The incoming HttpRequest object.

    Raises:
        PermissionDeniedError: If 'sysadmin' is not in the user's roles.
    """
    roles = getattr(request, "jwt_roles", [])
    if "sysadmin" not in roles:
        raise PermissionDeniedError("SYSADMIN role required")


@router.get("/", response=TenantListResponseSchema, summary="List All Tenants (SysAdmin)")
def list_tenants(
    request: HttpRequest,
    status: Optional[str] = Query(None, description="Filter by tenant status."),
    tier: Optional[str] = Query(None, description="Filter by tenant tier."),
    search: Optional[str] = Query(None, description="Search term for name or slug."),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lists all tenants in the system with filtering and pagination.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    tenants, total = TenantService.list_tenants(
        status=status, tier=tier, search=search, page=page, page_size=page_size
    )
    return {
        "items": list(tenants),
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 1,
    }


@router.post("/", response=TenantResponseSchema, summary="Create a Tenant (SysAdmin)")
def create_tenant(request: HttpRequest, payload: TenantCreateSchema):
    """
    Creates a new tenant and its associated default settings.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    return TenantService.create_tenant(
        name=payload.name, slug=payload.slug, tier=payload.tier, settings=payload.settings
    )


@router.get("/{tenant_id}", response=TenantResponseSchema, summary="Get a Tenant by ID (SysAdmin)")
def get_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Retrieves complete details for a specific tenant by its ID.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    return TenantService.get_by_id(tenant_id)


@router.patch("/{tenant_id}", response=TenantResponseSchema, summary="Update a Tenant (SysAdmin)")
def update_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantUpdateSchema):
    """
    Updates a tenant's name or settings.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    return TenantService.update_tenant(
        tenant_id=tenant_id, name=payload.name, settings=payload.settings
    )


@router.post("/{tenant_id}/activate", response=TenantResponseSchema, summary="Activate a Tenant (SysAdmin)")
def activate_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Activates a tenant with a 'pending' status.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    return TenantService.activate_tenant(tenant_id)


@router.post("/{tenant_id}/suspend", response=TenantResponseSchema, summary="Suspend a Tenant (SysAdmin)")
def suspend_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantSuspendSchema):
    """
    Suspends an active tenant, preventing access and operations.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    return TenantService.suspend_tenant(tenant_id, payload.reason)


@router.post("/{tenant_id}/reactivate", response=TenantResponseSchema, summary="Reactivate a Tenant (SysAdmin)")
def reactivate_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Reactivates a suspended tenant, setting its status back to 'active'.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    return TenantService.reactivate_tenant(tenant_id)


@router.post("/{tenant_id}/unsuspend", response=TenantResponseSchema, summary="Unsuspend a Tenant (SysAdmin)")
def unsuspend_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Alias for the 'reactivate' endpoint. Reactivates a suspended tenant.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    return TenantService.reactivate_tenant(tenant_id)


@router.delete("/{tenant_id}", summary="Soft-Delete a Tenant (SysAdmin)")
def delete_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Soft-deletes a tenant by setting its status to 'deleted'.

    **Permissions:** SYSADMIN role required.

    *Note: This endpoint returns a JSON object `{"status": "deleted"}` instead
    of the more conventional empty 204 No Content response.*
    """
    require_sysadmin(request)
    TenantService.soft_delete_tenant(tenant_id)
    return {"status": "deleted"}


@router.post("/{tenant_id}/upgrade", response=TenantResponseSchema, summary="Upgrade Tenant Tier (SysAdmin)")
def upgrade_tenant_tier(request: HttpRequest, tenant_id: UUID, payload: TenantUpgradeTierSchema):
    """
    Upgrades or downgrades a tenant's subscription tier.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    return TenantService.upgrade_tier(tenant_id, payload.tier)


@router.get("/{tenant_id}/usage", summary="Get Tenant Usage (SysAdmin)")
def get_tenant_usage_admin(request: HttpRequest, tenant_id: UUID):
    """
    Get tenant usage statistics.

    **Permissions:** SYSADMIN role required.

    *Note: The current implementation calls `TenantService.get_usage_stats`,
    which may not exist. The correct method is likely `get_tenant_stats`.*
    """
    require_sysadmin(request)
    # This method call appears to be a bug, it should likely be get_tenant_stats
    return TenantService.get_usage_stats(tenant_id)


@router.post("/{tenant_id}/impersonate", summary="Impersonate a User (SysAdmin, Not Implemented)")
def impersonate_user(request: HttpRequest, tenant_id: UUID):
    """
    Issues an impersonation token for a user in the specified tenant.

    **Permissions:** SYSADMIN role required.

    *Note: This feature is a placeholder and is not currently implemented.*
    """
    require_sysadmin(request)
    raise FeatureNotImplementedError("Impersonation is not configured for this deployment")
