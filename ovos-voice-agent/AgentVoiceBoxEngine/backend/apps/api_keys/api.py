"""
API Key Management Endpoints
============================

This module provides API endpoints for managing API keys, which are used to
authenticate programmatic access to the platform. It includes functionality
for creating, listing, retrieving, updating, revoking, rotating, and deleting
API keys, all within the context of a tenant's permissions.
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

# Router for API key management endpoints, tagged for OpenAPI documentation.
router = Router(tags=["API Keys"])


@router.get("", response=APIKeyListResponse, summary="List API Keys in Tenant")
def list_api_keys(
    request,
    project_id: Optional[UUID] = Query(
        None, description="Filter API keys by a specific project ID."
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter API keys by active status."
    ),
    search: Optional[str] = Query(
        None, description="Search term for API key name or prefix."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lists all API keys belonging to the current user's tenant.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to list API keys.")

    keys, total = APIKeyService.list_keys(
        tenant=tenant,
        project_id=project_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return APIKeyListResponse(
        items=[APIKeyResponse.from_orm(k) for k in keys],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{key_id}", response=APIKeyResponse, summary="Get an API Key by ID")
def get_api_key(request, key_id: UUID):
    """
    Retrieves details for a specific API key by its ID.

    The API key must belong to the current user's tenant.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to view API keys.")

    api_key = APIKeyService.get_by_id(key_id)

    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant.")

    return APIKeyResponse.from_orm(api_key)


@router.post("", response=APIKeyCreateResponse, summary="Create a New API Key")
def create_api_key(request, payload: APIKeyCreate):
    """
    Creates a new API key for the current user's tenant.

    **Security Note:** The full plaintext API key is returned **only once**
    at the time of creation. It is crucial to store this key securely, as it
    cannot be retrieved again.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to create API keys.")

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


@router.patch("/{key_id}", response=APIKeyResponse, summary="Update an API Key")
def update_api_key(request, key_id: UUID, payload: APIKeyUpdate):
    """
    Updates an existing API key's details (name, description, scopes, rate limit tier).

    The API key must belong to the current user's tenant.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to update API keys.")

    api_key = APIKeyService.get_by_id(key_id)
    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant.")

    updated_key = APIKeyService.update_key(
        key_id=key_id,
        name=payload.name,
        description=payload.description,
        scopes=payload.scopes,
        rate_limit_tier=payload.rate_limit_tier,
    )

    return APIKeyResponse.from_orm(updated_key)


@router.post("/{key_id}/revoke", response=APIKeyResponse, summary="Revoke an API Key")
def revoke_api_key(
    request, key_id: UUID, payload: Optional[APIKeyRevokeRequest] = None
):
    """
    Revokes an API key, immediately rendering it inactive.

    The API key must belong to the current user's tenant.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to revoke API keys.")

    api_key = APIKeyService.get_by_id(key_id)
    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant.")

    reason = payload.reason if payload else ""
    revoked_key = APIKeyService.revoke_key(key_id, user, reason)

    return APIKeyResponse.from_orm(revoked_key)


@router.post(
    "/{key_id}/rotate", response=APIKeyRotateResponse, summary="Rotate an API Key"
)
def rotate_api_key(
    request, key_id: UUID, payload: Optional[APIKeyRotateRequest] = None
):
    """
    Rotates an existing API key by generating a new one and optionally
    revoking the old key after a grace period.

    The API key must belong to the current user's tenant.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to rotate API keys.")

    api_key = APIKeyService.get_by_id(key_id)
    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant.")

    grace_period = payload.grace_period_hours if payload else 0
    new_key, full_key, old_key_grace_period_instance = APIKeyService.rotate_key(
        key_id=key_id,
        user=user,
        grace_period_hours=grace_period,
    )

    return APIKeyRotateResponse(
        new_key=APIKeyCreateResponse.from_orm(new_key, full_key),
        old_key_expires_at=(
            old_key_grace_period_instance.expires_at
            if old_key_grace_period_instance
            else None
        ),
    )


@router.delete("/{key_id}", response={204: None}, summary="Delete an API Key")
def delete_api_key(request, key_id: UUID):
    """
    Permanently deletes an API key.

    The API key must belong to the current user's tenant.

    **Permissions:** Requires ADMIN role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_admin:
        raise PermissionDeniedError("Admin role required to delete API keys.")

    api_key = APIKeyService.get_by_id(key_id)
    if api_key.tenant_id != tenant.id:
        raise PermissionDeniedError("API key not found in this tenant.")

    APIKeyService.delete_key(key_id)
    return 204, None
