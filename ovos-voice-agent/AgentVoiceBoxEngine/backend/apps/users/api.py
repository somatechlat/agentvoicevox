"""
User API endpoints.

Public user endpoints for tenant-scoped operations.
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

router = Router()


@router.get("/me", response=CurrentUserResponse)
def get_current_user(request):
    """
    Get current authenticated user.

    Returns the currently authenticated user with full details.
    """
    user = request.user
    return CurrentUserResponse.from_orm(user)


@router.patch("/me", response=CurrentUserResponse)
def update_current_user(request, payload: UserUpdate):
    """
    Update current user profile.

    Users can update their own profile (name, preferences).
    Role changes require admin permissions.
    """
    user = request.user

    # Users cannot change their own role
    if payload.role is not None:
        raise PermissionDeniedError("Cannot change your own role")

    # Users cannot deactivate themselves
    if payload.is_active is False:
        raise PermissionDeniedError("Cannot deactivate your own account")

    updated_user = UserService.update_user(
        user_id=user.id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        preferences=payload.preferences,
    )
    return CurrentUserResponse.from_orm(updated_user)


@router.patch("/me/preferences", response=CurrentUserResponse)
def update_preferences(request, payload: UserPreferencesUpdate):
    """
    Update current user preferences.
    """
    user = request.user
    preferences = payload.dict(exclude_none=True)
    updated_user = UserService.update_preferences(user.id, preferences)
    return CurrentUserResponse.from_orm(updated_user)


@router.get("", response=UserListResponse)
def list_users(
    request,
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List users in the current tenant.

    Requires at least OPERATOR role.
    """
    tenant = get_current_tenant()
    user = request.user

    # Check permission - at least operator
    if not user.is_operator:
        raise PermissionDeniedError("Insufficient permissions to list users")

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


@router.get("/{user_id}", response=UserResponse)
def get_user(request, user_id: UUID):
    """
    Get user by ID.

    Requires at least OPERATOR role.
    """
    tenant = get_current_tenant()
    current_user = request.user

    # Check permission
    if not current_user.is_operator:
        raise PermissionDeniedError("Insufficient permissions to view user")

    user = UserService.get_by_id(user_id)

    # Ensure user belongs to current tenant
    if user.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant")

    return UserResponse.from_orm(user)


@router.post("", response=UserResponse)
def create_user(request, payload: UserCreate):
    """
    Create a new user in the current tenant.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    current_user = request.user

    # Check permission - admin only
    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to create users")

    user = UserService.create_user(
        tenant=tenant,
        email=payload.email,
        role=payload.role,
        first_name=payload.first_name,
        last_name=payload.last_name,
        keycloak_id=payload.keycloak_id,
    )

    return UserResponse.from_orm(user)


@router.patch("/{user_id}", response=UserResponse)
def update_user(request, user_id: UUID, payload: UserUpdate):
    """
    Update a user.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    current_user = request.user

    # Check permission - admin only
    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to update users")

    # Get user and verify tenant
    user = UserService.get_by_id(user_id)
    if user.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant")

    # Prevent demoting yourself
    if user.id == current_user.id and payload.role is not None:
        raise PermissionDeniedError("Cannot change your own role")

    updated_user = UserService.update_user(
        user_id=user_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        is_active=payload.is_active,
        preferences=payload.preferences,
    )

    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/role", response=UserResponse)
def change_user_role(request, user_id: UUID, payload: UserRoleChange):
    """
    Change user role.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    current_user = request.user

    # Check permission - admin only
    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to change roles")

    # Get user and verify tenant
    user = UserService.get_by_id(user_id)
    if user.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant")

    # Prevent changing your own role
    if user.id == current_user.id:
        raise PermissionDeniedError("Cannot change your own role")

    # Only SYSADMIN can assign SYSADMIN role
    if payload.role == User.Role.SYSADMIN and not current_user.is_sysadmin:
        raise PermissionDeniedError("Only system administrators can assign SYSADMIN role")

    updated_user = UserService.change_role(user_id, payload.role)
    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/deactivate", response=UserResponse)
def deactivate_user(request, user_id: UUID):
    """
    Deactivate a user.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    current_user = request.user

    # Check permission - admin only
    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to deactivate users")

    # Get user and verify tenant
    user = UserService.get_by_id(user_id)
    if user.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant")

    # Prevent deactivating yourself
    if user.id == current_user.id:
        raise PermissionDeniedError("Cannot deactivate your own account")

    updated_user = UserService.deactivate_user(user_id)
    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/activate", response=UserResponse)
def activate_user(request, user_id: UUID):
    """
    Activate a user.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    current_user = request.user

    # Check permission - admin only
    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to activate users")

    # Get user and verify tenant
    user = UserService.get_by_id(user_id)
    if user.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant")

    updated_user = UserService.activate_user(user_id)
    return UserResponse.from_orm(updated_user)


@router.delete("/{user_id}", response={204: None})
def delete_user(request, user_id: UUID):
    """
    Delete a user permanently.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    current_user = request.user

    # Check permission - admin only
    if not current_user.is_admin:
        raise PermissionDeniedError("Admin role required to delete users")

    # Get user and verify tenant
    user = UserService.get_by_id(user_id)
    if user.tenant_id != tenant.id:
        raise PermissionDeniedError("User not found in this tenant")

    # Prevent deleting yourself
    if user.id == current_user.id:
        raise PermissionDeniedError("Cannot delete your own account")

    UserService.delete_user(user_id)
    return 204, None
