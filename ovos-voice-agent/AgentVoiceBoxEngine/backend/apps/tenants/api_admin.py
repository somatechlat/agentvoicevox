"""
Admin API endpoints for tenant management.

These endpoints are restricted to SYSADMIN role only.
"""
from typing import Optional, List
from uuid import UUID
import math

from ninja import Router, Query
from django.http import HttpRequest

from apps.core.exceptions import PermissionDeniedError
from .schemas import (
    TenantCreateSchema,
    TenantResponseSchema,
    TenantListResponseSchema,
    TenantUpdateSchema,
    TenantUpgradeTierSchema,
    TenantSuspendSchema,
)
from .services import TenantService

router = Router()


def require_sysadmin(request: HttpRequest) -> None:
    """Check if user has SYSADMIN role."""
    roles = getattr(request, "jwt_roles", [])
    if "sysadmin" not in roles:
        raise PermissionDeniedError("SYSADMIN role required")


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
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    
    tenants, total = TenantService.list_tenants(
        status=status,
        tier=tier,
        search=search,
        page=page,
        page_size=page_size,
    )
    
    return {
        "items": list(tenants),
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total > 0 else 1,
    }


@router.post("/", response=TenantResponseSchema)
def create_tenant(request: HttpRequest, payload: TenantCreateSchema):
    """
    Create a new tenant.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    
    return TenantService.create_tenant(
        name=payload.name,
        slug=payload.slug,
        tier=payload.tier,
        settings=payload.settings,
    )


@router.get("/{tenant_id}", response=TenantResponseSchema)
def get_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Get tenant by ID.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    return TenantService.get_by_id(tenant_id)


@router.patch("/{tenant_id}", response=TenantResponseSchema)
def update_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantUpdateSchema):
    """
    Update tenant details.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    
    return TenantService.update_tenant(
        tenant_id=tenant_id,
        name=payload.name,
        settings=payload.settings,
    )


@router.post("/{tenant_id}/activate", response=TenantResponseSchema)
def activate_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Activate a pending tenant.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    return TenantService.activate_tenant(tenant_id)


@router.post("/{tenant_id}/suspend", response=TenantResponseSchema)
def suspend_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantSuspendSchema):
    """
    Suspend a tenant.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    return TenantService.suspend_tenant(tenant_id, payload.reason)


@router.post("/{tenant_id}/reactivate", response=TenantResponseSchema)
def reactivate_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Reactivate a suspended tenant.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    return TenantService.reactivate_tenant(tenant_id)


@router.delete("/{tenant_id}")
def delete_tenant(request: HttpRequest, tenant_id: UUID):
    """
    Soft delete a tenant.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    TenantService.delete_tenant(tenant_id)
    return {"status": "deleted"}


@router.post("/{tenant_id}/upgrade", response=TenantResponseSchema)
def upgrade_tenant_tier(request: HttpRequest, tenant_id: UUID, payload: TenantUpgradeTierSchema):
    """
    Upgrade tenant to a new tier.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    return TenantService.upgrade_tier(tenant_id, payload.tier)


@router.get("/{tenant_id}/usage")
def get_tenant_usage_admin(request: HttpRequest, tenant_id: UUID):
    """
    Get tenant usage statistics.
    
    SYSADMIN only.
    """
    require_sysadmin(request)
    return TenantService.get_usage_stats(tenant_id)
