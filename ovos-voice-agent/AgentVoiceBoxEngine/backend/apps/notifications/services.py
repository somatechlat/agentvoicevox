"""
Notification services.

Business logic for notification management and delivery.
"""
from datetime import time
from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from apps.notifications.models import Notification, NotificationPreference
from apps.tenants.models import Tenant
from apps.users.models import User


class NotificationService:
    """Service for managing notifications."""

    @staticmethod
    def list_notifications(
        user: User,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Notification], int, int]:
        """
        List notifications for a user.

        Returns tuple of (notifications, total_count, unread_count).
        """
        qs = Notification.objects.filter(user=user)

        unread_count = qs.filter(read_at__isnull=True).count()

        if unread_only:
            qs = qs.filter(read_at__isnull=True)

        total = qs.count()
        offset = (page - 1) * page_size
        notifications = list(qs.order_by("-created_at")[offset : offset + page_size])

        return notifications, total, unread_count

    @staticmethod
    def get_notification(notification_id: UUID) -> Optional[Notification]:
        """Get a notification by ID."""
        try:
            return Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:
            return None

    @staticmethod
    def get_counts(user: User) -> tuple[int, int]:
        """Get notification counts. Returns (unread_count, total_count)."""
        qs = Notification.objects.filter(user=user)
        total = qs.count()
        unread = qs.filter(read_at__isnull=True).count()
        return unread, total

    @staticmethod
    @transaction.atomic
    def create_notification(
        tenant: Tenant,
        notification_type: str,
        title: str,
        message: str,
        user: Optional[User] = None,
        data: Optional[dict[str, Any]] = None,
        action_url: str = "",
        action_label: str = "",
        channels: Optional[list[str]] = None,
    ) -> Notification:
        """Create a new notification."""
        notification = Notification.objects.create(
            tenant=tenant,
            user=user,
            type=notification_type,
            title=title,
            message=message,
            data=data or {},
            action_url=action_url,
            action_label=action_label,
            channels=channels or ["in_app"],
        )
        return notification

    @staticmethod
    def mark_as_read(notification: Notification) -> Notification:
        """Mark a notification as read."""
        notification.mark_read()
        return notification

    @staticmethod
    @transaction.atomic
    def mark_multiple_as_read(user: User, notification_ids: list[UUID]) -> int:
        """Mark multiple notifications as read. Returns count updated."""
        return Notification.objects.filter(
            user=user,
            id__in=notification_ids,
            read_at__isnull=True,
        ).update(read_at=timezone.now())

    @staticmethod
    @transaction.atomic
    def mark_all_as_read(user: User) -> int:
        """Mark all notifications as read for a user. Returns count updated."""
        return Notification.objects.filter(
            user=user,
            read_at__isnull=True,
        ).update(read_at=timezone.now())

    @staticmethod
    def dismiss_notification(notification: Notification) -> Notification:
        """Dismiss a notification."""
        notification.dismiss()
        return notification

    @staticmethod
    def delete_notification(notification: Notification) -> None:
        """Delete a notification."""
        notification.delete()


class NotificationPreferenceService:
    """Service for managing notification preferences."""

    @staticmethod
    def get_preferences(user: User) -> NotificationPreference:
        """Get or create notification preferences for a user."""
        prefs, _ = NotificationPreference.objects.get_or_create(
            user=user,
            tenant=user.tenant,
            defaults={
                "email_enabled": True,
                "in_app_enabled": True,
                "billing_notifications": True,
                "security_notifications": True,
                "system_notifications": True,
                "quiet_hours_enabled": False,
            },
        )
        return prefs

    @staticmethod
    def update_preferences(user: User, data: dict) -> NotificationPreference:
        """Update notification preferences."""
        prefs = NotificationPreferenceService.get_preferences(user)

        for key, value in data.items():
            if value is not None and hasattr(prefs, key):
                # Handle time fields
                if key in ("quiet_hours_start", "quiet_hours_end") and isinstance(value, str):
                    if value:
                        parts = value.split(":")
                        value = time(int(parts[0]), int(parts[1]))
                    else:
                        value = None
                setattr(prefs, key, value)

        prefs.save()
        return prefs

    @staticmethod
    def should_notify(user: User, notification_type: str, channel: str) -> bool:
        """Check if user should receive notification."""
        prefs = NotificationPreferenceService.get_preferences(user)
        return prefs.should_notify(notification_type, channel)
