"""
Pydantic schemas for Billing API.
"""
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID

from ninja import Schema


class UsageEventCreate(Schema):
    """Schema for creating a usage event."""
    event_type: str
    quantity: Decimal
    unit: str = "count"
    session_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    metadata: Dict[str, Any] = {}


class UsageEventResponse(Schema):
    """Schema for usage event response."""
    id: UUID
    tenant_id: UUID
    event_type: str
    quantity: Decimal
    unit: str
    session_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    synced_at: Optional[datetime] = None
    created_at: datetime

    @staticmethod
    def from_orm(event) -> "UsageEventResponse":
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
    """Schema for usage summary."""
    period_start: datetime
    period_end: datetime
    sessions: int
    api_calls: int
    audio_minutes: Decimal
    input_tokens: int
    output_tokens: int
    stt_minutes: Decimal
    tts_minutes: Decimal


class CurrentUsageResponse(Schema):
    """Schema for current usage response."""
    tenant_id: UUID
    period_start: datetime
    period_end: datetime
    usage: UsageSummary
    limits: Dict[str, int]
    percentage_used: Dict[str, float]


class ProjectedCostResponse(Schema):
    """Schema for projected cost response."""
    tenant_id: UUID
    current_month_cost: Decimal
    projected_month_cost: Decimal
    currency: str
    breakdown: Dict[str, Decimal]


class InvoiceResponse(Schema):
    """Schema for invoice response."""
    id: UUID
    tenant_id: UUID
    lago_invoice_id: str
    invoice_number: str
    amount: Decimal
    taxes_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    issuing_date: date
    payment_due_date: Optional[date] = None
    pdf_url: str
    created_at: datetime

    @staticmethod
    def from_orm(invoice) -> "InvoiceResponse":
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
    """Schema for paginated invoice list."""
    items: List[InvoiceResponse]
    total: int
    page: int
    page_size: int
    pages: int


class BillingAlertResponse(Schema):
    """Schema for billing alert response."""
    id: UUID
    tenant_id: UUID
    alert_type: str
    message: str
    resource_type: str
    current_value: Optional[Decimal] = None
    threshold_value: Optional[Decimal] = None
    acknowledged: bool
    acknowledged_at: Optional[datetime] = None
    created_at: datetime

    @staticmethod
    def from_orm(alert) -> "BillingAlertResponse":
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
    """Schema for billing alert list."""
    items: List[BillingAlertResponse]
    total: int


class SubscriptionResponse(Schema):
    """Schema for subscription response."""
    tenant_id: UUID
    tier: str
    status: str
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    lago_subscription_id: Optional[str] = None


class LagoWebhookPayload(Schema):
    """Schema for Lago webhook payload."""
    webhook_type: str
    object_type: str
    data: Dict[str, Any]
