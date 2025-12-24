"""
Billing models for usage tracking and Lago integration.

Tracks usage events and billing-related data.
"""
import uuid

from django.db import models
from django.utils import timezone

from apps.tenants.models import TenantScopedManager, TenantScopedModel


class UsageEventManager(TenantScopedManager):
    """Manager for UsageEvent model."""

    def for_period(self, start_date, end_date):
        """Get events within a date range."""
        return self.filter(
            created_at__gte=start_date,
            created_at__lt=end_date,
        )

    def unsynced(self):
        """Get events not yet synced to Lago."""
        return self.filter(synced_at__isnull=True)


class UsageEvent(TenantScopedModel):
    """
    Usage event for billing.

    Tracks billable events that are synced to Lago.
    """

    class EventType(models.TextChoices):
        """Usage event types."""
        SESSION = "session", "Voice Session"
        API_CALL = "api_call", "API Call"
        AUDIO_MINUTES = "audio_minutes", "Audio Minutes"
        INPUT_TOKENS = "input_tokens", "Input Tokens"
        OUTPUT_TOKENS = "output_tokens", "Output Tokens"
        STT_MINUTES = "stt_minutes", "STT Minutes"
        TTS_MINUTES = "tts_minutes", "TTS Minutes"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Event data
    event_type = models.CharField(
        max_length=50,
        choices=EventType.choices,
        help_text="Type of usage event",
    )
    quantity = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        help_text="Quantity of usage",
    )
    unit = models.CharField(
        max_length=50,
        default="count",
        help_text="Unit of measurement",
    )

    # Associations
    session = models.ForeignKey(
        "sessions.Session",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_events",
        help_text="Associated session",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_events",
        help_text="Associated project",
    )
    api_key = models.ForeignKey(
        "api_keys.APIKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="usage_events",
        help_text="Associated API key",
    )

    # Lago sync
    lago_event_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Lago event ID after sync",
    )
    synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When event was synced to Lago",
    )
    sync_error = models.TextField(
        blank=True,
        help_text="Error message if sync failed",
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional event metadata",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    event_timestamp = models.DateTimeField(
        default=timezone.now,
        help_text="When the usage actually occurred",
    )

    # Manager
    objects = UsageEventManager()

    class Meta:
        db_table = "usage_events"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["event_type"]),
            models.Index(fields=["synced_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["tenant", "event_type"]),
            models.Index(fields=["tenant", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.event_type}: {self.quantity} {self.unit}"

    def mark_synced(self, lago_event_id: str) -> None:
        """Mark event as synced to Lago."""
        self.lago_event_id = lago_event_id
        self.synced_at = timezone.now()
        self.sync_error = ""
        self.save(update_fields=["lago_event_id", "synced_at", "sync_error"])

    def mark_sync_error(self, error: str) -> None:
        """Mark sync error."""
        self.sync_error = error
        self.save(update_fields=["sync_error"])


class BillingAlert(TenantScopedModel):
    """
    Billing alert for usage thresholds.

    Tracks when tenants exceed usage thresholds.
    """

    class AlertType(models.TextChoices):
        """Alert types."""
        USAGE_WARNING = "usage_warning", "Usage Warning (80%)"
        USAGE_CRITICAL = "usage_critical", "Usage Critical (90%)"
        LIMIT_EXCEEDED = "limit_exceeded", "Limit Exceeded"
        PAYMENT_FAILED = "payment_failed", "Payment Failed"
        SUBSCRIPTION_EXPIRING = "subscription_expiring", "Subscription Expiring"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Alert data
    alert_type = models.CharField(
        max_length=50,
        choices=AlertType.choices,
        help_text="Type of alert",
    )
    message = models.TextField(
        help_text="Alert message",
    )
    resource_type = models.CharField(
        max_length=50,
        blank=True,
        help_text="Resource type (sessions, tokens, etc.)",
    )
    current_value = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Current usage value",
    )
    threshold_value = models.DecimalField(
        max_digits=20,
        decimal_places=6,
        null=True,
        blank=True,
        help_text="Threshold value",
    )

    # Status
    acknowledged = models.BooleanField(
        default=False,
        help_text="Whether alert has been acknowledged",
    )
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When alert was acknowledged",
    )
    acknowledged_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_alerts",
        help_text="User who acknowledged the alert",
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional alert metadata",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_alerts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["alert_type"]),
            models.Index(fields=["acknowledged"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["tenant", "acknowledged"]),
        ]

    def __str__(self) -> str:
        return f"{self.alert_type}: {self.message[:50]}"

    def acknowledge(self, user) -> None:
        """Acknowledge the alert."""
        self.acknowledged = True
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save(update_fields=["acknowledged", "acknowledged_at", "acknowledged_by"])


class Invoice(TenantScopedModel):
    """
    Invoice record synced from Lago.

    Stores invoice data for display in the portal.
    """

    class Status(models.TextChoices):
        """Invoice status."""
        DRAFT = "draft", "Draft"
        FINALIZED = "finalized", "Finalized"
        PAID = "paid", "Paid"
        VOIDED = "voided", "Voided"
        FAILED = "failed", "Payment Failed"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Lago data
    lago_invoice_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Lago invoice ID",
    )
    invoice_number = models.CharField(
        max_length=100,
        help_text="Invoice number",
    )

    # Amounts (in cents)
    amount_cents = models.BigIntegerField(
        help_text="Total amount in cents",
    )
    taxes_amount_cents = models.BigIntegerField(
        default=0,
        help_text="Tax amount in cents",
    )
    total_amount_cents = models.BigIntegerField(
        help_text="Total amount including taxes in cents",
    )
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Currency code",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        help_text="Invoice status",
    )

    # Dates
    issuing_date = models.DateField(
        help_text="Invoice issue date",
    )
    payment_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Payment due date",
    )

    # PDF
    pdf_url = models.URLField(
        blank=True,
        help_text="URL to invoice PDF",
    )

    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional invoice metadata",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices"
        ordering = ["-issuing_date"]
        indexes = [
            models.Index(fields=["lago_invoice_id"]),
            models.Index(fields=["status"]),
            models.Index(fields=["issuing_date"]),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self) -> str:
        return f"Invoice {self.invoice_number} - {self.status}"

    @property
    def amount(self) -> float:
        """Get amount in dollars."""
        return self.amount_cents / 100

    @property
    def taxes_amount(self) -> float:
        """Get tax amount in dollars."""
        return self.taxes_amount_cents / 100

    @property
    def total_amount(self) -> float:
        """Get total amount in dollars."""
        return self.total_amount_cents / 100
