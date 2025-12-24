"""
Pydantic schemas for User API.

All request/response validation for user endpoints.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ninja import Schema
from pydantic import EmailStr, Field


class UserBase(Schema):
    """Base user schema."""
    email: EmailStr
    first_name: str = ""
    last_name: str = ""
    role: str = "viewer"


class UserCreate(UserBase):
    """Schema for creating a user."""
    keycloak_id: Optional[str] = None


class UserUpdate(Schema):
    """Schema for updating a user."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(Schema):
    """Schema for user response."""
    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    is_active: bool
    avatar_url: str
    tenant_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None

    @staticmethod
    def from_orm(user) -> "UserResponse":
        return UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            avatar_url=user.avatar_url or "",
            tenant_id=user.tenant_id,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )


class UserListResponse(Schema):
    """Schema for paginated user list."""
    items: List[UserResponse]
    total: int
    page: int
    page_size: int
    pages: int


class UserPreferencesUpdate(Schema):
    """Schema for updating user preferences."""
    theme: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None


class UserRoleChange(Schema):
    """Schema for changing user role."""
    role: str = Field(..., description="New role for the user")


class UserInvite(Schema):
    """Schema for inviting a user."""
    email: EmailStr
    role: str = "viewer"
    send_email: bool = True


class UserInviteResponse(Schema):
    """Schema for user invite response."""
    id: UUID
    email: str
    role: str
    invited_at: datetime
    invite_expires_at: datetime


class CurrentUserResponse(Schema):
    """Schema for current user response with additional details."""
    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    is_active: bool
    is_sysadmin: bool
    is_admin: bool
    avatar_url: str
    tenant_id: Optional[UUID] = None
    tenant_name: Optional[str] = None
    tenant_slug: Optional[str] = None
    preferences: Dict[str, Any]
    created_at: datetime
    last_login_at: Optional[datetime] = None

    @staticmethod
    def from_orm(user) -> "CurrentUserResponse":
        return CurrentUserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_sysadmin=user.is_sysadmin,
            is_admin=user.is_admin,
            avatar_url=user.avatar_url or "",
            tenant_id=user.tenant_id,
            tenant_name=user.tenant.name if user.tenant else None,
            tenant_slug=user.tenant.slug if user.tenant else None,
            preferences=user.preferences,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
