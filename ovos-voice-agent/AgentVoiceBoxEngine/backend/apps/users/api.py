"""
User Management API Endpoints
=============================

This module provides the primary, tenant-scoped API endpoints for user management.
It includes endpoints for users to manage their own profiles (`/me`) as well as
endpoints for tenant administrators to manage other users within their tenant.
"""

from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError
from apps.core.middleware.tenant import get_current_tenant

from .models import User
from .schemas import (
    CurrentUserResponse,
    UserCreate,
    UserListResponse,
    UserPreferencesUpdate,
    UserResponse,
    UserRoleChange,
    UserUpdate,
)
from .services import UserService

# Router for user management endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Users"])


@router.get("/me", response=CurrentUserResponse, summary="Get Current User Details")
def get_current_user(request):
    """
    Retrieves detailed information for the currently authenticated user.

    This endpoint provides a comprehensive view of the user's own profile,
    including their roles, permissions, and tenant information.

    **Permissions:** Available to any authenticated user.
    """
    user = request.user
    return CurrentUserResponse.from_orm(user)


@router.patch(
    "/me", response=CurrentUserResponse, summary="Update Current User's Profile"
)
def update_current_user(request, payload: UserUpdate):
    """
    Allows a user to update their own profile information.

    Users can update their first name, last name, and preferences. They are
    explicitly blocked from changing their own role or deactivating their own
    account via this endpoint.

    **Permissions:** Available to any authenticated user.
    """
    user = request.user

    # Security check: Users cannot change their own role via this endpoint.
    if payload.role is not None:
        raise PermissionDeniedError(
            "Cannot change your own role. Please contact an administrator."
        )

    # Security check: Users cannot deactivate themselves.
    if payload.is_active is False:
        raise PermissionDeniedError("Cannot deactivate your own account.")

    updated_user = UserService.update_user(
        user_id=user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        preferences=payload.preferences,
    )
    return CurrentUserResponse.from_orm(updated_user)


@router.patch(
    "/me/preferences",
    response=CurrentUserResponse,
    summary="Update Current User's Preferences",
)
def update_preferences(request, payload: UserPreferencesUpdate):
    """
    Allows a user to update their own UI preferences.

    This is a dedicated endpoint for updating the `preferences` JSON field.

    **Permissions:** Available to any authenticated user.
    """
    user = request.user
    preferences = payload.dict(exclude_none=True)
    updated_user = UserService.update_user(user_id=user.id, preferences=preferences)
    return CurrentUserResponse.from_orm(updated_user)


@router.get("", response=UserListResponse, summary="List Users in Tenant")
def list_users(
    request,
    role: Optional[str] = Query(
        None, description="Filter users by role (e.g., 'admin')."
    ),
    is_active: Optional[bool] = Query(
        None, description="Filter users by active status."
    ),
    search: Optional[str] = Query(None, description="Search term for name or email."),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lists all users within the current user's tenant, with filtering and pagination.

    **Permissions:** Requires OPERATOR, ADMIN, or SYSADMIN role.
    """
    tenant = get_current_tenant(request)
    current_user = request.user

    if not current_user.is_operator:
        raise PermissionDeniedError("Operator role or higher required to list users.")

    users, total = UserService.list_users(
        tenant=tenant,
        role=role,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size

    return UserListResponse(
        items=[UserResponse.from_orm(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{user_id}", response=UserResponse, summary="Get a User by ID")
def get_user(request, user_id: UUID):
    """
    Retrieves details for a specific user within the tenant.

    **Permissions:** Requires OPERATOR, ADMIN, or SYSADMIN role.
    """
    tenant = get_current_tenant(request)
    current_user = request.user

    if not current_user.is_operator:
        raise PermissionDeniedError(
            "Operator role or higher required to view user details."
        )

    user = UserService.get_by_id(user_id)
    if user.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant.")

    return UserResponse.from_orm(user)


@router.post("", response=UserResponse, summary="Create a User in Tenant")
def create_user(request, payload: UserCreate):
    """
    Creates a new user within the current user's tenant.

    **Permissions:** Requires ADMIN or SYSADMIN role.
    """
    tenant = get_current_tenant(request)
    current_user = request.user

    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to create users.")

    user = UserService.create_user(
        tenant=tenant,
        email=payload.email,
        role=payload.role,
        first_name=payload.first_name,
        last_name=payload.last_name,
        keycloak_id=payload.keycloak_id,
    )
    return UserResponse.from_orm(user)


@router.patch("/{user_id}", response=UserResponse, summary="Update a User")
def update_user(request, user_id: UUID, payload: UserUpdate):
    """
    Updates a user's details within the tenant.

    **Permissions:** Requires ADMIN or SYSADMIN role.
    """
    tenant = get_current_tenant(request)
    current_user = request.user

    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to update users.")

    user_to_update = UserService.get_by_id(user_id)
    if user_to_update.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant.")

    # Security check: Prevent an admin from changing their own role.
    if user_to_update.id == current_user.id and payload.role is not None:
        raise PermissionDeniedError("Cannot change your own role via this endpoint.")

    updated_user = UserService.update_user(
        user_id=user_id, **payload.dict(exclude_unset=True)
    )
    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/role", response=UserResponse, summary="Change a User's Role")
def change_user_role(request, user_id: UUID, payload: UserRoleChange):
    """
    Changes a specific user's role within the tenant.

    **Permissions:** Requires ADMIN or SYSADMIN role.
    """
    tenant = get_current_tenant(request)
    current_user = request.user

    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to change user roles.")

    user_to_update = UserService.get_by_id(user_id)
    if user_to_update.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant.")

    # Security check: Prevent changing your own role.
    if user_to_update.id == current_user.id:
        raise PermissionDeniedError("Cannot change your own role.")

    # Security check: Only a SysAdmin can grant the SysAdmin role.
    if payload.role == User.Role.SYSADMIN and not current_user.is_sysadmin:
        raise PermissionDeniedError(
            "Only a System Administrator can grant the SYSADMIN role."
        )

    updated_user = UserService.change_role(user_id, payload.role)
    return UserResponse.from_orm(updated_user)


@router.post(
    "/{user_id}/deactivate", response=UserResponse, summary="Deactivate a User"
)
def deactivate_user(request, user_id: UUID):
    """
    Deactivates a user's account, preventing them from logging in.

    **Permissions:** Requires ADMIN or SYSADMIN role.
    """
    tenant = get_current_tenant(request)
    current_user = request.user

    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to deactivate users.")

    user_to_deactivate = UserService.get_by_id(user_id)
    if user_to_deactivate.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant.")

    # Security check: Prevent deactivating yourself.
    if user_to_deactivate.id == current_user.id:
        raise PermissionDeniedError("Cannot deactivate your own account.")

    updated_user = UserService.deactivate_user(user_id)
    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/activate", response=UserResponse, summary="Activate a User")
def activate_user(request, user_id: UUID):
    """
    Activates an inactive user's account.

    **Permissions:** Requires ADMIN or SYSADMIN role.
    """
    tenant = get_current_tenant(request)
    current_user = request.user

    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to activate users.")

    user_to_activate = UserService.get_by_id(user_id)
    if user_to_activate.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant.")

    updated_user = UserService.activate_user(user_id)
    return UserResponse.from_orm(updated_user)


@router.delete("/{user_id}", response={204: None}, summary="Delete a User")
def delete_user(request, user_id: UUID):
    """
    Permanently deletes a user from the tenant.

    **Permissions:** Requires ADMIN or SYSADMIN role.

    Returns:
        A 204 No Content response on success.
    """
    tenant = get_current_tenant(request)
    current_user = request.user

    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to delete users.")

    user_to_delete = UserService.get_by_id(user_id)
    if user_to_delete.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant.")

    # Security check: Prevent deleting yourself.
    if user_to_delete.id == current_user.id:
        raise PermissionDeniedError("Cannot delete your own account.")

    UserService.delete_user(user_id)
    return 204, None
