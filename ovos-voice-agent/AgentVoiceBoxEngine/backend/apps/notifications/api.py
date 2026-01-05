"""
Notifications API endpoints.

Provides REST API for notification management.
"""

from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import NotFoundError

from .schemas import (
    NotificationBulkActionOut,
    NotificationCountOut,
    NotificationCreate,
    NotificationListOut,
    NotificationOut,
    NotificationPreferenceOut,
    NotificationPreferenceUpdate,
)
from .services import NotificationPreferenceService, NotificationService

router = Router()


def _notification_to_out(n) -> NotificationOut:
    """Convert Notification model to output schema."""
    return NotificationOut(
        id=n.id,
        tenant_id=n.tenant_id,
        user_id=n.user_id,
        type=n.type,
        title=n.title,
        message=n.message,
        data=n.data,
        action_url=n.action_url,
        action_label=n.action_label,
        channels=n.channels,
        delivered_at=n.delivered_at,
        read_at=n.read_at,
        dismissed_at=n.dismissed_at,
        created_at=n.created_at,
        expires_at=n.expires_at,
    )


def _preference_to_out(p) -> NotificationPreferenceOut:
    """Convert NotificationPreference model to output schema."""
    return NotificationPreferenceOut(
        id=p.id,
        user_id=p.user_id,
        tenant_id=p.tenant_id,
        email_enabled=p.email_enabled,
        in_app_enabled=p.in_app_enabled,
        billing_notifications=p.billing_notifications,
        security_notifications=p.security_notifications,
        system_notifications=p.system_notifications,
        quiet_hours_enabled=p.quiet_hours_enabled,
        quiet_hours_start=p.quiet_hours_start,
        quiet_hours_end=p.quiet_hours_end,
        created_at=p.created_at,
        updated_at=p.updated_at,
    )


# ==========================================================================
# NOTIFICATION ENDPOINTS
# ==========================================================================
@router.get("", response=NotificationListOut)
def list_notifications(
    request,
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List notifications for current user."""
    user = request.user
    notifications, total, unread_count = NotificationService.list_notifications(
        user=user,
        unread_only=unread_only,
        page=page,
        page_size=page_size,
    )
    return NotificationListOut(
        items=[_notification_to_out(n) for n in notifications],
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
    )


@router.get("/count", response=NotificationCountOut)
def get_notification_count(request):
    """Get notification counts for current user."""
    user = request.user
    unread, total = NotificationService.get_counts(user)
    return NotificationCountOut(
        total=total,
        unread=unread,
        by_type={},
    )


@router.post("", response={201: NotificationOut})
def create_notification(request, payload: NotificationCreate):
    """Create a new notification."""
    tenant = request.tenant
    user = None
    if payload.user_id:
        from apps.users.models import User

        try:
            user = User.objects.get(id=payload.user_id, tenant=tenant)
        except User.DoesNotExist:
            raise NotFoundError(f"User {payload.user_id} not found")

    notification = NotificationService.create_notification(
        tenant=tenant,
        notification_type=payload.type,
        title=payload.title,
        message=payload.message,
        user=user,
        data=payload.data,
        action_url=payload.action_url,
        action_label=payload.action_label,
        channels=payload.channels,
    )
    return 201, _notification_to_out(notification)


@router.post("/mark-all-read", response=NotificationBulkActionOut)
def mark_all_as_read(request):
    """Mark all notifications as read for current user."""
    user = request.user
    count = NotificationService.mark_all_as_read(user)
    return NotificationBulkActionOut(affected_count=count)


@router.post("/mark-read", response=NotificationBulkActionOut)
def mark_multiple_as_read(request, notification_ids: list[UUID]):
    """Mark multiple notifications as read."""
    user = request.user
    count = NotificationService.mark_multiple_as_read(user, notification_ids)
    return NotificationBulkActionOut(affected_count=count)


@router.get("/{notification_id}", response=NotificationOut)
def get_notification(request, notification_id: UUID):
    """Get a notification by ID."""
    notification = NotificationService.get_notification(notification_id)
    if not notification:
        raise NotFoundError(f"Notification {notification_id} not found")
    return _notification_to_out(notification)


@router.post("/{notification_id}/read", response=NotificationOut)
def mark_as_read(request, notification_id: UUID):
    """Mark a notification as read."""
    notification = NotificationService.get_notification(notification_id)
    if not notification:
        raise NotFoundError(f"Notification {notification_id} not found")
    notification = NotificationService.mark_as_read(notification)
    return _notification_to_out(notification)


@router.post("/{notification_id}/dismiss", response=NotificationOut)
def dismiss_notification(request, notification_id: UUID):
    """Dismiss a notification."""
    notification = NotificationService.get_notification(notification_id)
    if not notification:
        raise NotFoundError(f"Notification {notification_id} not found")
    notification = NotificationService.dismiss_notification(notification)
    return _notification_to_out(notification)


@router.delete("/{notification_id}", response={204: None})
def delete_notification(request, notification_id: UUID):
    """Delete a notification."""
    notification = NotificationService.get_notification(notification_id)
    if not notification:
        raise NotFoundError(f"Notification {notification_id} not found")
    NotificationService.delete_notification(notification)
    return 204, None


# ==========================================================================
# NOTIFICATION PREFERENCE ENDPOINTS
# ==========================================================================
@router.get("/preferences", response=NotificationPreferenceOut)
def get_preferences(request):
    """Get notification preferences for current user."""
    user = request.user
    preferences = NotificationPreferenceService.get_preferences(user)
    return _preference_to_out(preferences)


@router.patch("/preferences", response=NotificationPreferenceOut)
def update_preferences(request, payload: NotificationPreferenceUpdate):
    """Update notification preferences for current user."""
    user = request.user
    preferences = NotificationPreferenceService.update_preferences(
        user=user,
        data=payload.dict(exclude_unset=True),
    )
    return _preference_to_out(preferences)
