"""
Billing models for Lago integration.

Tracks usage events, subscriptions, and invoices synced from Lago.
"""
import uuid

from django.db import models
from django.utils import timezone

from apps.tenants.models import Tenant, TenantScopedManager, TenantScopedModel


class Subscription(TenantScopedModel):
    """
    Subscription model synced from Lago.

    Represents a tenant's billing subscription.
    """

    class Status(models.TextChoices):
        """Subscription status."""

        ACTIVE = "active", "Active"
        PENDING = "pending", "Pending"
        TERMINATED = "terminated", "Terminated"
        CANCELED = "canceled", "Canceled"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Lago IDs
    lago_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Lago subscription ID",
    )
    external_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="External subscription ID",
    )

    # Plan info
    plan_code = models.CharField(
        max_length=50,
        help_text="Lago plan code",
    )
    plan_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Plan display name",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # Timestamps
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Subscription start date",
    )
    ending_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Subscription end date",
    )
    canceled_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Cancellation date",
    )
    terminated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Termination date",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "subscriptions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["lago_id"]),
            models.Index(fields=["external_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.plan_code} ({self.status})"

    def is_active(self) -> bool:
        """Check if subscription is active."""
        return self.status == self.Status.ACTIVE


class Invoice(TenantScopedModel):
    """
    Invoice model synced from Lago.

    Represents billing invoices for a tenant.
    """

    class Status(models.TextChoices):
        """Invoice status."""

        DRAFT = "draft", "Draft"
        FINALIZED = "finalized", "Finalized"
        VOIDED = "voided", "Voided"

    class PaymentStatus(models.TextChoices):
        """Payment status."""

        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Lago IDs
    lago_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Lago invoice ID",
    )
    number = models.CharField(
        max_length=50,
        help_text="Invoice number",
    )
    sequential_id = models.PositiveIntegerField(
        help_text="Sequential invoice ID",
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    # Amounts (in cents)
    currency = models.CharField(
        max_length=3,
        default="USD",
        help_text="Currency code",
    )
    total_amount_cents = models.BigIntegerField(
        default=0,
        help_text="Total amount in cents",
    )
    taxes_amount_cents = models.BigIntegerField(
        default=0,
        help_text="Taxes amount in cents",
    )
    sub_total_cents = models.BigIntegerField(
        default=0,
        help_text="Subtotal excluding taxes in cents",
    )

    # Dates
    issuing_date = models.DateField(
        null=True,
        blank=True,
        help_text="Invoice issue date",
    )
    payment_due_date = models.DateField(
        null=True,
        blank=True,
        help_text="Payment due date",
    )

    # File
    file_url = models.URLField(
        blank=True,
        help_text="PDF download URL",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "invoices"
        ordering = ["-issuing_date", "-created_at"]
        indexes = [
            models.Index(fields=["lago_id"]),
            models.Index(fields=["number"]),
            models.Index(fields=["status"]),
            models.Index(fields=["issuing_date"]),
        ]

    def __str__(self) -> str:
        return f"Invoice {self.number} ({self.status})"

    @property
    def total_amount(self) -> float:
        """Get total amount in dollars."""
        return self.total_amount_cents / 100.0


class UsageRecord(TenantScopedModel):
    """
    Usage record for billing.

    Tracks usage events before they are synced to Lago.
    """

    class MetricCode(models.TextChoices):
        """Billable metric codes."""

        API_REQUESTS = "api_requests", "API Requests"
        AUDIO_MINUTES_INPUT = "audio_minutes_input", "Audio Input Minutes"
        AUDIO_MINUTES_OUTPUT = "audio_minutes_output", "Audio Output Minutes"
        LLM_TOKENS_INPUT = "llm_tokens_input", "LLM Input Tokens"
        LLM_TOKENS_OUTPUT = "llm_tokens_output", "LLM Output Tokens"
        CONCURRENT_CONNECTIONS = "concurrent_connections", "Concurrent Connections"
        CONNECTION_MINUTES = "connection_minutes", "Connection Minutes"

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Transaction ID (for idempotency)
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique transaction ID",
    )

    # Metric info
    metric_code = models.CharField(
        max_length=50,
        choices=MetricCode.choices,
        help_text="Billable metric code",
    )
    quantity = models.FloatField(
        default=1.0,
        help_text="Quantity of the metric",
    )
    properties = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional properties",
    )

    # Sync status
    synced_to_lago = models.BooleanField(
        default=False,
        help_text="Whether synced to Lago",
    )
    synced_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When synced to Lago",
    )

    # Timestamp
    recorded_at = models.DateTimeField(
        default=timezone.now,
        help_text="When the usage occurred",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    # Managers
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "usage_records"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["transaction_id"]),
            models.Index(fields=["metric_code"]),
            models.Index(fields=["synced_to_lago"]),
            models.Index(fields=["recorded_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.metric_code}: {self.quantity}"

    def mark_synced(self) -> None:
        """Mark record as synced to Lago."""
        self.synced_to_lago = True
        self.synced_at = timezone.now()
        self.save(update_fields=["synced_to_lago", "synced_at"])


class UsageSummary(TenantScopedModel):
    """
    Aggregated usage summary for a billing period.

    Pre-computed for dashboard display.
    """

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Period
    period_start = models.DateField(help_text="Period start date")
    period_end = models.DateField(help_text="Period end date")

    # Aggregated metrics
    api_requests = models.PositiveBigIntegerField(default=0)
    audio_input_minutes = models.FloatField(default=0.0)
    audio_output_minutes = models.FloatField(default=0.0)
    llm_input_tokens = models.PositiveBigIntegerField(default=0)
    llm_output_tokens = models.PositiveBigIntegerField(default=0)
    total_sessions = models.PositiveIntegerField(default=0)
    total_connection_minutes = models.FloatField(default=0.0)

    # Estimated cost (in cents)
    estimated_cost_cents = models.BigIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "usage_summaries"
        ordering = ["-period_start"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "period_start", "period_end"],
                name="unique_usage_summary_period",
            ),
        ]
        indexes = [
            models.Index(fields=["period_start", "period_end"]),
        ]

    def __str__(self) -> str:
        return f"Usage {self.period_start} - {self.period_end}"

    @property
    def estimated_cost(self) -> float:
        """Get estimated cost in dollars."""
        return self.estimated_cost_cents / 100.0
