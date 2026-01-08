"""
Pydantic Schemas for the User API
===================================

This module defines the Pydantic schemas used for data validation, serialization,
and deserialization in the User and Profile API endpoints. These schemas form the
public data contract for interacting with user resources.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from ninja import Schema
from pydantic import EmailStr, Field


class UserBase(Schema):
    """A base schema containing common user fields."""

    email: EmailStr  # The user's unique email address.
    first_name: str = ""  # The user's first name.
    last_name: str = ""  # The user's last name.
    role: str = "viewer"  # The user's role within their tenant.


class UserCreate(UserBase):
    """
    Defines the request payload for creating a new user.
    Used by tenant admins to add users to their tenant.
    """

    keycloak_id: Optional[str] = (
        None  # The user's ID from the external identity provider (Keycloak).
    )


class UserUpdate(Schema):
    """
    Defines the request payload for updating a user's details.
    All fields are optional to allow for partial updates.
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None  # The user's new role (e.g., 'admin', 'developer').
    is_active: Optional[bool] = None  # Set the user's account to active or inactive.
    preferences: Optional[dict[str, Any]] = (
        None  # A dictionary of user-specific UI preferences.
    )


class UserResponse(Schema):
    """
    Defines the standard response structure for a single user object.
    """

    id: UUID  # The user's unique internal ID.
    email: str
    first_name: str
    last_name: str
    full_name: str  # A combination of first and last names.
    role: str  # The user's role within the tenant.
    is_active: bool  # Whether the user's account is currently active.
    avatar_url: str  # A URL to the user's profile picture.
    tenant_id: Optional[UUID] = None  # The ID of the tenant this user belongs to.
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None  # Timestamp of the user's last login.

    @staticmethod
    def from_orm(user) -> "UserResponse":
        """
        Creates a `UserResponse` instance from a Django `User` model instance.

        This method provides controlled serialization from the ORM model to the
        Pydantic schema.

        Args:
            user: The Django `User` model instance.

        Returns:
            An instance of `UserResponse`.
        """
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
    """
    Defines the response structure for a paginated list of users.
    """

    items: list[UserResponse]  # The list of users on the current page.
    total: int  # The total number of users matching the query.
    page: int  # The current page number.
    page_size: int  # The number of items per page.
    pages: int  # The total number of pages.


class UserPreferencesUpdate(Schema):
    """
    Defines the request payload for updating a user's own preferences.
    """

    theme: Optional[str] = None  # The UI theme (e.g., 'light', 'dark').
    language: Optional[str] = None  # The preferred UI language (e.g., 'en', 'es').
    timezone: Optional[str] = (
        None  # The user's timezone (e.g., 'UTC', 'America/New_York').
    )
    notifications_enabled: Optional[bool] = None  # Master switch for all notifications.
    email_notifications: Optional[bool] = (
        None  # Specific switch for email notifications.
    )


class UserRoleChange(Schema):
    """
    Defines the request payload for changing a user's role.
    """

    role: str = Field(..., description="The new role to assign to the user.")


class UserInvite(Schema):
    """
    Defines the request payload for inviting a new user to a tenant.
    """

    email: EmailStr  # The email address of the user to invite.
    role: str = "viewer"  # The role to assign to the user upon accepting the invite.
    send_email: bool = True  # If true, the system will send an invitation email.


class UserInviteResponse(Schema):
    """
    Defines the response structure after successfully creating a user invitation.
    """

    id: UUID  # The unique ID of the invitation record.
    email: str
    role: str
    invited_at: datetime  # Timestamp when the invitation was sent.
    invite_expires_at: datetime  # Timestamp when the invitation will expire.


class CurrentUserResponse(Schema):
    """

    Defines the response for the '/users/me' endpoint, providing a comprehensive
    view of the currently authenticated user's data, including permissions and
    tenant information.
    """

    # Core user info
    id: UUID
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str  # The user's role within their tenant.
    is_active: bool
    avatar_url: str

    # Permission flags (derived from role)
    is_sysadmin: bool
    is_admin: bool

    # Tenant info
    tenant_id: Optional[UUID] = None
    tenant_name: Optional[str] = None
    tenant_slug: Optional[str] = None

    # Settings and timestamps
    preferences: dict[str, Any]
    created_at: datetime
    last_login_at: Optional[datetime] = None

    @staticmethod
    def from_orm(user) -> "CurrentUserResponse":
        """
        Creates a `CurrentUserResponse` instance from a Django `User` model instance.

        This method populates the schema with user data and derived properties
        like permissions and tenant details.

        Args:
            user: The authenticated Django `User` model instance.

        Returns:
            An instance of `CurrentUserResponse`.
        """
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
