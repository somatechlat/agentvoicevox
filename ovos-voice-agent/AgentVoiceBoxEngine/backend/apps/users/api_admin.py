"""
Admin User API endpoints.

SYSADMIN-only endpoints for cross-tenant user management.
"""
from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError

from .models import User
from .schemas import UserListResponse, UserResponse, UserUpdate
from .services import UserService

router = Router()


def require_sysadmin(request):
    """Check if user is SYSADMIN."""
    if not request.user.is_sysadmin:
        raise PermissionDeniedError("SYSADMIN role required")


@router.get("", response=UserListResponse)
def list_all_users(
    request,
    tenant_id: Optional[UUID] = Query(None, description="Filter by tenant"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List all users across all tenants.

    SYSADMIN only.
    """
    require_sysadmin(request)

    from django.db.models import Q

    qs = User.objects.select_related("tenant").all()

    # Apply filters
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
    users = qs[offset : offset + page_size]
    pages = (total + page_size - 1) // page_size

    return UserListResponse(
        items=[UserResponse.from_orm(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{user_id}", response=UserResponse)
def get_user_admin(request, user_id: UUID):
    """
    Get any user by ID.

    SYSADMIN only.
    """
    require_sysadmin(request)
    user = UserService.get_by_id(user_id)
    return UserResponse.from_orm(user)


@router.patch("/{user_id}", response=UserResponse)
def update_user_admin(request, user_id: UUID, payload: UserUpdate):
    """
    Update any user.

    SYSADMIN only.
    """
    require_sysadmin(request)

    updated_user = UserService.update_user(
        user_id=user_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        is_active=payload.is_active,
        preferences=payload.preferences,
    )

    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/deactivate", response=UserResponse)
def deactivate_user_admin(request, user_id: UUID):
    """
    Deactivate any user.

    SYSADMIN only.
    """
    require_sysadmin(request)
    updated_user = UserService.deactivate_user(user_id)
    return UserResponse.from_orm(updated_user)


@router.post("/{user_id}/activate", response=UserResponse)
def activate_user_admin(request, user_id: UUID):
    """
    Activate any user.

    SYSADMIN only.
    """
    require_sysadmin(request)
    updated_user = UserService.activate_user(user_id)
    return UserResponse.from_orm(updated_user)


@router.delete("/{user_id}", response={204: None})
def delete_user_admin(request, user_id: UUID):
    """
    Delete any user permanently.

    SYSADMIN only.
    """
    require_sysadmin(request)
    UserService.delete_user(user_id)
    return 204, None
