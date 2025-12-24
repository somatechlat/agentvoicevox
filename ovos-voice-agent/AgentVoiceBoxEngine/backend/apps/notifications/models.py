"""
Notification models.

Stores notifications for users and tenants.
"""
import uuid

from django.db import models
from django.utils import timezone

from apps.tenants.models import TenantScopedManager, TenantScopedModel


class Notification(TenantScopedModel):
    """
    Notification model.

    Stores notifications for users within a tenant.
    """

    class Type(models.TextChoices):
        """Notification types."""

        INFO = "info", "Information"
        SUCCESS = "success", "Success"
        WARNING = "warning", "Warning"
        ERROR = "error", "Error"
        BILLING = "billing", "Billing"
        SECURITY = "security", "Security"
        SYSTEM = "system", "System"

    class Channel(models.TextChoices):
        """Notification channels."""

        IN_APP = "in_app", "In-App"
        EMAIL = "email", "Email"
        WEBHOOK = "webhook", "Webhook"
        SLACK = "slack", "Slack"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Target user (nullable for tenant-wide notifications)
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notifications",
        help_text="Target user (null for tenant-wide)",
    )

    # Notification content
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.INFO,
        help_text="Notification type",
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification title",
    )
    message = models.TextField(
        help_text="Notification message",
    )
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data payload",
    )

    # Action
    action_url = models.URLField(
        blank=True,
        help_text="Action URL",
    )
    action_label = models.CharField(
        max_length=100,
        blank=True,
        help_text="Action button label",
    )

    # Delivery
    channels = models.JSONField(
        default=list,
        help_text="Delivery channels",
    )
    delivered_at = models.JSONField(
        default=dict,
        blank=True,
        help_text="Delivery timestamps per channel",
    )

    # Status
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was read",
    )
    dismissed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the notification was dismissed",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Notification expiration",
    )

    # Managers
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "read_at"]),
            models.Index(fields=["type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.type}: {self.title}"

    def mark_read(self) -> None:
        """Mark notification as read."""
        if not self.read_at:
            self.read_at = timezone.now()
            self.save(update_fields=["read_at"])

    def dismiss(self) -> None:
        """Dismiss the notification."""
        if not self.dismissed_at:
            self.dismissed_at = timezone.now()
            self.save(update_fields=["dismissed_at"])

    def is_read(self) -> bool:
        """Check if notification is read."""
        return self.read_at is not None

    def is_expired(self) -> bool:
        """Check if notification is expired."""
        if not self.expires_at:
            return False
        return self.expires_at < timezone.now()

    def record_delivery(self, channel: str) -> None:
        """Record delivery to a channel."""
        self.delivered_at[channel] = timezone.now().isoformat()
        self.save(update_fields=["delivered_at"])


class NotificationPreference(TenantScopedModel):
    """
    User notification preferences.

    Controls which notifications a user receives and how.
    """

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # User
    user = models.OneToOneField(
        "users.User",
        on_delete=models.CASCADE,
        related_name="notification_preferences",
        help_text="User these preferences belong to",
    )

    # Channel preferences
    email_enabled = models.BooleanField(
        default=True,
        help_text="Enable email notifications",
    )
    in_app_enabled = models.BooleanField(
        default=True,
        help_text="Enable in-app notifications",
    )

    # Type preferences
    billing_notifications = models.BooleanField(
        default=True,
        help_text="Receive billing notifications",
    )
    security_notifications = models.BooleanField(
        default=True,
        help_text="Receive security notifications",
    )
    system_notifications = models.BooleanField(
        default=True,
        help_text="Receive system notifications",
    )

    # Quiet hours
    quiet_hours_enabled = models.BooleanField(
        default=False,
        help_text="Enable quiet hours",
    )
    quiet_hours_start = models.TimeField(
        null=True,
        blank=True,
        help_text="Quiet hours start time",
    )
    quiet_hours_end = models.TimeField(
        null=True,
        blank=True,
        help_text="Quiet hours end time",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "notification_preferences"

    def __str__(self) -> str:
        return f"Preferences for {self.user.email}"

    def should_notify(self, notification_type: str, channel: str) -> bool:
        """Check if user should receive notification."""
        # Check channel
        if channel == "email" and not self.email_enabled:
            return False
        if channel == "in_app" and not self.in_app_enabled:
            return False

        # Check type
        type_map = {
            "billing": self.billing_notifications,
            "security": self.security_notifications,
            "system": self.system_notifications,
        }
        if notification_type in type_map:
            return type_map[notification_type]

        return True
