"""
Pydantic Schemas for Billing API
=================================

This module defines the Pydantic schemas for data validation and serialization
in the Billing API endpoints. These schemas provide the structured data
contracts for managing usage events, viewing aggregated usage, projected costs,
invoices, and billing alerts, as well as handling webhooks from external billing
providers like Lago.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from ninja import Schema


class UsageEventCreate(Schema):
    """
    Defines the request payload for creating a new usage event.
    """

    event_type: str  # The type of usage event (e.g., 'api_call', 'audio_minutes').
    quantity: Decimal  # The quantity of usage for this event (e.g., 1 for an API call, 0.5 for half an audio minute).
    unit: str = "count"  # The unit of measurement (e.g., 'count', 'minutes', 'tokens').
    session_id: Optional[UUID] = (
        None  # (Optional) The UUID of the session associated with this event.
    )
    project_id: Optional[UUID] = (
        None  # (Optional) The UUID of the project associated with this event.
    )
    metadata: dict[str, Any] = {}  # (Optional) Additional, unstructured event metadata.


class UsageEventResponse(Schema):
    """
    Defines the response structure for a single usage event object.
    """

    id: UUID  # The unique identifier for the usage event.
    tenant_id: UUID  # The ID of the tenant associated with this event.
    event_type: str
    quantity: Decimal
    unit: str
    session_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    synced_at: Optional[datetime] = None  # Timestamp when the event was synced to Lago.
    created_at: datetime  # Timestamp when the event record was created.

    @staticmethod
    def from_orm(event) -> "UsageEventResponse":
        """
        Creates a `UsageEventResponse` instance from a Django `UsageEvent` model.

        Args:
            event: The Django `UsageEvent` model instance.

        Returns:
            An instance of `UsageEventResponse`.
        """
        return UsageEventResponse(
            id=event.id,
            tenant_id=event.tenant_id,
            event_type=event.event_type,
            quantity=event.quantity,
            unit=event.unit,
            session_id=event.session_id,
            project_id=event.project_id,
            synced_at=event.synced_at,
            created_at=event.created_at,
        )


class UsageSummary(Schema):
    """
    Defines the structure for an aggregated summary of usage data.
    """

    period_start: datetime  # The start date of the billing period.
    period_end: datetime  # The end date of the billing period.
    sessions: int  # Total number of voice sessions.
    api_calls: int  # Total number of API calls.
    audio_minutes: Decimal  # Total audio minutes consumed.
    input_tokens: int  # Total input tokens used.
    output_tokens: int  # Total output tokens generated.
    stt_minutes: Decimal  # Total Speech-to-Text minutes.
    tts_minutes: Decimal  # Total Text-to-Speech minutes.


class CurrentUsageResponse(Schema):
    """
    Defines the response structure for the current month's usage.
    Combines usage summary, tenant limits, and percentage used.
    """

    tenant_id: UUID  # The ID of the tenant.
    period_start: datetime
    period_end: datetime
    usage: UsageSummary  # Detailed usage breakdown.
    limits: dict[
        str, int
    ]  # Current limits for the tenant (e.g., max_sessions_per_month).
    percentage_used: dict[
        str, float
    ]  # Percentage of limits used (e.g., {'sessions': 75.5}).


class ProjectedCostResponse(Schema):
    """
    Defines the response structure for projected billing costs.
    """

    tenant_id: UUID  # The ID of the tenant.
    current_month_cost: Decimal  # The accumulated cost so far this month.
    projected_month_cost: Decimal  # The estimated total cost for the entire month.
    currency: str  # The currency code (e.g., 'USD').
    breakdown: dict[str, Decimal]  # Cost breakdown by usage type.


class InvoiceResponse(Schema):
    """
    Defines the response structure for a single invoice object.
    """

    id: UUID  # The unique identifier for the local invoice record.
    tenant_id: UUID  # The ID of the tenant for whom the invoice was issued.
    lago_invoice_id: str  # The unique ID of the invoice in the Lago billing system.
    invoice_number: str  # The human-readable invoice number.
    amount: Decimal  # The subtotal amount of the invoice (in major currency units).
    taxes_amount: Decimal  # The tax amount of the invoice (in major currency units).
    total_amount: Decimal  # The total amount of the invoice (in major currency units).
    currency: str  # The currency code (e.g., 'USD').
    status: str  # The status of the invoice (e.g., 'paid', 'finalized').
    issuing_date: date  # The date when the invoice was issued.
    payment_due_date: Optional[date] = None  # The date by which payment is due.
    pdf_url: str  # URL to the downloadable PDF version of the invoice.
    created_at: datetime  # Timestamp when the invoice record was created.

    @staticmethod
    def from_orm(invoice) -> "InvoiceResponse":
        """
        Creates an `InvoiceResponse` instance from a Django `Invoice` model.

        Args:
            invoice: The Django `Invoice` model instance.

        Returns:
            An instance of `InvoiceResponse`.
        """
        return InvoiceResponse(
            id=invoice.id,
            tenant_id=invoice.tenant_id,
            lago_invoice_id=invoice.lago_invoice_id,
            invoice_number=invoice.invoice_number,
            amount=invoice.amount,
            taxes_amount=invoice.taxes_amount,
            total_amount=invoice.total_amount,
            currency=invoice.currency,
            status=invoice.status,
            issuing_date=invoice.issuing_date,
            payment_due_date=invoice.payment_due_date,
            pdf_url=invoice.pdf_url or "",
            created_at=invoice.created_at,
        )


class InvoiceListResponse(Schema):
    """
    Defines the response structure for a paginated list of invoices.
    """

    items: list[InvoiceResponse]  # The list of invoices on the current page.
    total: int  # The total number of invoices matching the query.
    page: int  # The current page number.
    page_size: int  # The number of items per page.
    pages: int  # The total number of pages.


class BillingAlertResponse(Schema):
    """
    Defines the response structure for a single billing alert object.
    """

    id: UUID  # The unique identifier for the alert.
    tenant_id: UUID  # The ID of the tenant this alert belongs to.
    alert_type: str  # The type of billing alert (e.g., 'usage_warning').
    message: str  # A human-readable message describing the alert.
    resource_type: str  # The resource type related to the alert (e.g., 'sessions').
    current_value: Optional[Decimal] = (
        None  # The current usage or value that triggered the alert.
    )
    threshold_value: Optional[Decimal] = (
        None  # The threshold value that was met or exceeded.
    )
    acknowledged: bool  # True if the alert has been acknowledged.
    acknowledged_at: Optional[datetime] = (
        None  # Timestamp when the alert was acknowledged.
    )
    created_at: datetime  # Timestamp when the alert was created.

    @staticmethod
    def from_orm(alert) -> "BillingAlertResponse":
        """
        Creates a `BillingAlertResponse` instance from a Django `BillingAlert` model.

        Args:
            alert: The Django `BillingAlert` model instance.

        Returns:
            An instance of `BillingAlertResponse`.
        """
        return BillingAlertResponse(
            id=alert.id,
            tenant_id=alert.tenant_id,
            alert_type=alert.alert_type,
            message=alert.message,
            resource_type=alert.resource_type,
            current_value=alert.current_value,
            threshold_value=alert.threshold_value,
            acknowledged=alert.acknowledged,
            acknowledged_at=alert.acknowledged_at,
            created_at=alert.created_at,
        )


class BillingAlertListResponse(Schema):
    """
    Defines the response structure for a list of billing alerts.
    """

    items: list[BillingAlertResponse]  # The list of billing alerts.
    total: int  # The total number of alerts matching the query.


class SubscriptionResponse(Schema):
    """
    Defines the response structure for a tenant's subscription information.
    This data is typically derived from the `Tenant` model's tier and Lago integration.
    """

    tenant_id: UUID  # The ID of the tenant.
    tier: str  # The tenant's current subscription tier.
    status: str  # The status of the subscription (e.g., 'active', 'canceled').
    current_period_start: Optional[datetime] = (
        None  # Start date of the current billing period.
    )
    current_period_end: Optional[datetime] = (
        None  # End date of the current billing period.
    )
    lago_subscription_id: Optional[str] = None  # The ID of the subscription in Lago.


class LagoWebhookPayload(Schema):
    """
    Defines the expected structure of an incoming webhook payload from Lago.
    """

    webhook_type: (
        str  # The type of webhook event (e.g., 'invoice.created', 'payment.failed').
    )
    object_type: (
        str  # The type of object related to the webhook (e.g., 'invoice', 'customer').
    )
    data: dict[str, Any]  # The actual data payload of the webhook event.
