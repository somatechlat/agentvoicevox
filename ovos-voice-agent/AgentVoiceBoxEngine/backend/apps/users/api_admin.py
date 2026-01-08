"""
System-Level Admin API for User Management
==========================================

This module provides API endpoints for system-level administration of all users
across all tenants. Access to these endpoints is strictly limited to users with
the SYSADMIN role.
"""

from typing import Optional
from uuid import UUID

from django.db.models import Q
from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError

from .models import User
from .schemas import UserListResponse, UserResponse, UserUpdate
from .services import UserService

# Router for the admin-specific user endpoints.
router = Router(tags=["Admin - Users"])


def require_sysadmin(request):
    """
    A dependency function that checks if the requesting user has SYSADMIN privileges.

    It inspects the `request.user` object provided by the authentication backend.

    Raises:
        PermissionDeniedError: If the user is not a system administrator.
    """
    if not request.user.is_sysadmin:
        raise PermissionDeniedError("SYSADMIN role required")


@router.get("", response=UserListResponse, summary="List All Users (SysAdmin)")
def list_all_users(
    request,
    tenant_id: Optional[UUID] = Query(
        None, description="Filter users by a specific tenant ID."
    ),
    role: Optional[str] = Query(None, description="Filter users by role."),
    is_active: Optional[bool] = Query(
        None, description="Filter users by active status."
    ),
    search: Optional[str] = Query(
        None, description="Search term for user name or email."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lists all users across all tenants with filtering and pagination.

    This provides a system-wide view of all user accounts.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)

    # Start with a non-tenant-scoped queryset.
    qs = User.objects.select_related("tenant").all()

    # Apply filters if provided.
    if tenant_id:
        qs = qs.filter(tenant_id=tenant_id)
    if role:
        qs = qs.filter(role=role)
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    if search:
        qs = qs.filter(
            Q(email__icontains=search)
            | Q(first_name__icontains=search)
            | Q(last_name__icontains=search)
        )

    total = qs.count()
    offset = (page - 1) * page_size
    users = qs.order_by("-created_at")[offset : offset + page_size]
    pages = (total + page_size - 1) // page_size

    return UserListResponse(
        items=[UserResponse.from_orm(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/{user_id}", response=UserResponse, summary="Get Any User by ID (SysAdmin)"
)
def get_user_admin(request, user_id: UUID):
    """
    Retrieves details for any user in the system by their ID.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    user = UserService.get_by_id(user_id)
    return UserResponse.from_orm(user)


@router.patch("/{user_id}", response=UserResponse, summary="Update Any User (SysAdmin)")
def update_user_admin(request, user_id: UUID, payload: UserUpdate):
    """
    Updates any user's details in the system.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    updated_user = UserService.update_user(
        user_id=user_id, **payload.dict(exclude_unset=True)
    )
    return UserResponse.from_orm(updated_user)


@router.post(
    "/{user_id}/deactivate",
    response=UserResponse,
    summary="Deactivate Any User (SysAdmin)",
)
def deactivate_user_admin(request, user_id: UUID):
    """
    Deactivates any user's account in the system.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    updated_user = UserService.deactivate_user(user_id)
    return UserResponse.from_orm(updated_user)


@router.post(
    "/{user_id}/activate", response=UserResponse, summary="Activate Any User (SysAdmin)"
)
def activate_user_admin(request, user_id: UUID):
    """
    Activates any user's account in the system.

    **Permissions:** SYSADMIN role required.
    """
    require_sysadmin(request)
    updated_user = UserService.activate_user(user_id)
    return UserResponse.from_orm(updated_user)


@router.delete("/{user_id}", response={204: None}, summary="Delete Any User (SysAdmin)")
def delete_user_admin(request, user_id: UUID):
    """
    Permanently deletes any user from the system.

    **Permissions:** SYSADMIN role required.

    Returns:
        A 204 No Content response on success.
    """
    require_sysadmin(request)
    UserService.delete_user(user_id)
    return 204, None
