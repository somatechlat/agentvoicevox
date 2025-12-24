"""
API Key endpoints.

Public API key endpoints for tenant-scoped operations.
"""
from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError
from apps.core.middleware.tenant import get_current_tenant

from .schemas import (
    APIKeyCreate,
    APIKeyCreateResponse,
    APIKeyListResponse,
    APIKeyResponse,
    APIKeyRevokeRequest,
    APIKeyRotateRequest,
    APIKeyRotateResponse,
    APIKeyUpdate,
)
from .services import APIKeyService

router = Router()


@router.get("", response=APIKeyListResponse)
def list_api_keys(
    request,
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or prefix"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List API keys in the current tenant.

    Requires at least DEVELOPER role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to list API keys")

    keys, total = APIKeyService.list_keys(
        tenant=tenant,
        project_id=project_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size

    return APIKeyListResponse(
        items=[APIKeyResponse.from_orm(k) for k in keys],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{key_id}", response=APIKeyResponse)
def get_api_key(request, key_id: UUID):
    """
    Get API key by ID.

    Requires at least DEVELOPER role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to view API keys")

    api_key = APIKeyService.get_by_id(key_id)

    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant")

    return APIKeyResponse.from_orm(api_key)


@router.post("", response=APIKeyCreateResponse)
def create_api_key(request, payload: APIKeyCreate):
    """
    Create a new API key.

    The full key is only returned once at creation time.
    Store it securely as it cannot be retrieved again.

    Requires at least DEVELOPER role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to create API keys")

    api_key, full_key = APIKeyService.create_key(
        tenant=tenant,
        name=payload.name,
        description=payload.description,
        project_id=payload.project_id,
        scopes=payload.scopes,
        rate_limit_tier=payload.rate_limit_tier,
        expires_in_days=payload.expires_in_days,
        created_by=user,
    )

    return APIKeyCreateResponse.from_orm(api_key, full_key)


@router.patch("/{key_id}", response=APIKeyResponse)
def update_api_key(request, key_id: UUID, payload: APIKeyUpdate):
    """
    Update an API key.

    Requires at least DEVELOPER role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to update API keys")

    api_key = APIKeyService.get_by_id(key_id)
    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant")

    updated_key = APIKeyService.update_key(
        key_id=key_id,
        name=payload.name,
        description=payload.description,
        scopes=payload.scopes,
        rate_limit_tier=payload.rate_limit_tier,
    )

    return APIKeyResponse.from_orm(updated_key)


@router.post("/{key_id}/revoke", response=APIKeyResponse)
def revoke_api_key(request, key_id: UUID, payload: APIKeyRevokeRequest = None):
    """
    Revoke an API key.

    Requires at least DEVELOPER role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to revoke API keys")

    api_key = APIKeyService.get_by_id(key_id)
    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant")

    reason = payload.reason if payload else ""
    revoked_key = APIKeyService.revoke_key(key_id, user, reason)

    return APIKeyResponse.from_orm(revoked_key)


@router.post("/{key_id}/rotate", response=APIKeyRotateResponse)
def rotate_api_key(request, key_id: UUID, payload: APIKeyRotateRequest = None):
    """
    Rotate an API key.

    Creates a new key and optionally keeps the old key active
    for a grace period.

    Requires at least DEVELOPER role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to rotate API keys")

    api_key = APIKeyService.get_by_id(key_id)
    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant")

    grace_period = payload.grace_period_hours if payload else 0
    new_key, full_key, old_key = APIKeyService.rotate_key(
        key_id=key_id,
        user=user,
        grace_period_hours=grace_period,
    )

    return APIKeyRotateResponse(
        new_key=APIKeyCreateResponse.from_orm(new_key, full_key),
        old_key_expires_at=old_key.expires_at if old_key else None,
    )


@router.delete("/{key_id}", response={204: None})
def delete_api_key(request, key_id: UUID):
    """
    Delete an API key permanently.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_admin:
        raise PermissionDeniedError("Admin role required to delete API keys")

    api_key = APIKeyService.get_by_id(key_id)
    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant")

    APIKeyService.delete_key(key_id)
    return 204, None
