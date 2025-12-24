"""
Billing API endpoints.

Public billing endpoints for tenant-scoped operations.
"""
from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError
from apps.core.middleware.tenant import get_current_tenant

from .schemas import (
    BillingAlertListResponse,
    BillingAlertResponse,
    CurrentUsageResponse,
    InvoiceListResponse,
    InvoiceResponse,
    LagoWebhookPayload,
    ProjectedCostResponse,
    UsageSummary,
)
from .services import BillingService, LagoService

router = Router()


@router.get("/usage", response=CurrentUsageResponse)
def get_current_usage(request):
    """
    Get current billing period usage.

    Requires at least BILLING role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view usage")

    usage_data = BillingService.get_current_usage(tenant)

    return CurrentUsageResponse(
        tenant_id=usage_data["tenant_id"],
        period_start=usage_data["period_start"],
        period_end=usage_data["period_end"],
        usage=UsageSummary(**usage_data["usage"]),
        limits=usage_data["limits"],
        percentage_used=usage_data["percentage_used"],
    )


@router.get("/projected", response=ProjectedCostResponse)
def get_projected_cost(request):
    """
    Get projected cost for current billing period.

    Requires at least BILLING role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view projected costs")

    cost_data = BillingService.get_projected_cost(tenant)

    return ProjectedCostResponse(
        tenant_id=cost_data["tenant_id"],
        current_month_cost=cost_data["current_month_cost"],
        projected_month_cost=cost_data["projected_month_cost"],
        currency=cost_data["currency"],
        breakdown=cost_data["breakdown"],
    )


@router.get("/invoices", response=InvoiceListResponse)
def list_invoices(
    request,
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List invoices.

    Requires at least BILLING role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view invoices")

    invoices, total = BillingService.list_invoices(
        tenant=tenant,
        status=status,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size

    return InvoiceListResponse(
        items=[InvoiceResponse.from_orm(i) for i in invoices],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/invoices/{invoice_id}", response=InvoiceResponse)
def get_invoice(request, invoice_id: UUID):
    """
    Get invoice by ID.

    Requires at least BILLING role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view invoices")

    invoice = BillingService.get_invoice(invoice_id)

    if invoice.tenant_id != tenant.id:
        raise PermissionDeniedError("Invoice not found in this tenant")

    return InvoiceResponse.from_orm(invoice)


@router.get("/alerts", response=BillingAlertListResponse)
def list_alerts(
    request,
    acknowledged: Optional[bool] = Query(None, description="Filter by acknowledged status"),
):
    """
    List billing alerts.

    Requires at least BILLING role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view alerts")

    alerts, total = BillingService.list_alerts(
        tenant=tenant,
        acknowledged=acknowledged,
    )

    return BillingAlertListResponse(
        items=[BillingAlertResponse.from_orm(a) for a in alerts],
        total=total,
    )


@router.post("/alerts/{alert_id}/acknowledge", response=BillingAlertResponse)
def acknowledge_alert(request, alert_id: UUID):
    """
    Acknowledge a billing alert.

    Requires at least BILLING role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to acknowledge alerts")

    alert = BillingService.acknowledge_alert(alert_id, user)

    if alert.tenant_id != tenant.id:
        raise PermissionDeniedError("Alert not found in this tenant")

    return BillingAlertResponse.from_orm(alert)


@router.post("/webhooks/lago", response={200: dict})
def lago_webhook(request, payload: LagoWebhookPayload):
    """
    Handle Lago webhook.

    This endpoint receives webhooks from Lago for billing events.
    """
    # TODO: Verify webhook signature
    LagoService.handle_webhook(payload.webhook_type, payload.data)
    return {"status": "ok"}
