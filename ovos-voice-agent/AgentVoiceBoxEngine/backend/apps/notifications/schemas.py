"""
Pydantic schemas for notifications API.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from ninja import Schema


# ==========================================================================
# NOTIFICATION SCHEMAS
# ==========================================================================
class NotificationCreate(Schema):
    """Schema for creating a notification (internal use)."""

    user_id: Optional[UUID] = None
    type: str = "info"
    title: str
    message: str
    data: dict[str, Any] = {}
    action_url: str = ""
    action_label: str = ""
    channels: list[str] = ["in_app"]


class NotificationOut(Schema):
    """Schema for notification response."""

    id: UUID
    tenant_id: UUID
    user_id: Optional[UUID] = None
    type: str
    title: str
    message: str
    data: dict[str, Any]
    action_url: str
    action_label: str
    channels: list[str]
    delivered_at: dict[str, str]
    read_at: Optional[datetime] = None
    dismissed_at: Optional[datetime] = None
    created_at: datetime
    expires_at: Optional[datetime] = None


class NotificationListOut(Schema):
    """Schema for paginated notification list."""

    items: list[NotificationOut]
    total: int
    unread_count: int
    page: int
    page_size: int


class NotificationCountOut(Schema):
    """Schema for notification count."""

    unread: int
    total: int
    by_type: dict[str, int] = {}


class NotificationBulkActionOut(Schema):
    """Schema for bulk action response."""

    affected_count: int


class MarkReadRequest(Schema):
    """Schema for marking notifications as read."""

    notification_ids: list[UUID]


class MarkReadResponse(Schema):
    """Schema for mark read response."""

    marked_count: int


# ==========================================================================
# NOTIFICATION PREFERENCE SCHEMAS
# ==========================================================================
class NotificationPreferenceOut(Schema):
    """Schema for notification preference response."""

    id: UUID
    user_id: UUID
    tenant_id: UUID
    email_enabled: bool
    in_app_enabled: bool
    billing_notifications: bool
    security_notifications: bool
    system_notifications: bool
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class NotificationPreferenceUpdate(Schema):
    """Schema for updating notification preferences."""

    email_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    billing_notifications: Optional[bool] = None
    security_notifications: Optional[bool] = None
    system_notifications: Optional[bool] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
