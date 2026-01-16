"""
Billing Management API Endpoints
================================

This module provides API endpoints for managing and retrieving billing-related
information. It allows users with appropriate permissions to view current usage,
projected costs, past invoices, and billing alerts. It also includes a webhook
endpoint for integration with external billing providers like Lago.
"""

import hashlib
import hmac
from typing import Optional
from uuid import UUID

from django.conf import settings
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

# Router for billing management endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Billing"])


def verify_lago_webhook_signature(request, payload: dict) -> bool:
    """
    Verify Lago webhook signature using HMAC-SHA256.

    Validates the X-Lago-Signature header against the request payload
    using the configured webhook secret.

    Args:
        request: The HTTP request object
        payload: The parsed JSON payload

    Returns:
        True if signature is valid, False otherwise

    **Implements: SEC-001**
    """
    signature = request.headers.get("X-Lago-Signature")
    if not signature:
        return False

    webhook_secret = settings.LAGO.get("WEBHOOK_SECRET")
    if not webhook_secret:
        return False

    # Get raw request body for signature verification
    try:
        body = request.body
        expected_signature = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        logger.warning(f"Signature verification failed: {e}")
        return False


@router.get(
    "/usage", response=CurrentUsageResponse, summary="Get Current Billing Period Usage"
)
def get_current_usage(request):
    """
    Retrieves aggregated usage data for the current billing period (month-to-date)
    for the current tenant.

    This provides insights into consumption across various metrics (sessions, API calls, tokens, etc.)
    and indicates percentage used against tenant limits.

    **Permissions:** Requires BILLING role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view usage data.")

    usage_data = BillingService.get_current_usage(tenant)

    # Manually construct response from service output.
    return CurrentUsageResponse(
        tenant_id=usage_data["tenant_id"],
        period_start=usage_data["period_start"],
        period_end=usage_data["period_end"],
        usage=UsageSummary(**usage_data["usage"]),
        limits=usage_data["limits"],
        percentage_used=usage_data["percentage_used"],
    )


@router.get(
    "/projected", response=ProjectedCostResponse, summary="Get Projected Monthly Cost"
)
def get_projected_cost(request):
    """
    Retrieves the current month-to-date cost and a projection of the total cost
    to the end of the current billing period for the current tenant.

    **Permissions:** Requires BILLING role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view projected costs.")

    cost_data = BillingService.get_projected_cost(tenant)

    # Manually construct response from service output.
    return ProjectedCostResponse(
        tenant_id=cost_data["tenant_id"],
        current_month_cost=cost_data["current_month_cost"],
        projected_month_cost=cost_data["projected_month_cost"],
        currency=cost_data["currency"],
        breakdown=cost_data["breakdown"],
    )


@router.get("/invoices", response=InvoiceListResponse, summary="List Tenant Invoices")
def list_invoices(
    request,
    status: Optional[str] = Query(
        None, description="Filter invoices by status (e.g., 'paid', 'finalized')."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lists all invoices for the current tenant.

    This endpoint supports filtering by invoice status and pagination.

    **Permissions:** Requires BILLING role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view invoices.")

    invoices, total = BillingService.list_invoices(
        tenant=tenant,
        status=status,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return InvoiceListResponse(
        items=[InvoiceResponse.from_orm(i) for i in invoices],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get(
    "/invoices/{invoice_id}", response=InvoiceResponse, summary="Get an Invoice by ID"
)
def get_invoice(request, invoice_id: UUID):
    """
    Retrieves details for a specific invoice by its ID.

    The invoice must belong to the current user's tenant.

    **Permissions:** Requires BILLING role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view invoices.")

    invoice = BillingService.get_invoice(invoice_id)

    if invoice.tenant_id != tenant.id:
        raise PermissionDeniedError("Invoice not found in this tenant.")

    return InvoiceResponse.from_orm(invoice)


@router.get(
    "/alerts", response=BillingAlertListResponse, summary="List Tenant Billing Alerts"
)
def list_alerts(
    request,
    acknowledged: Optional[bool] = Query(
        None, description="Filter alerts by acknowledgment status."
    ),
):
    """
    Lists all billing alerts for the current tenant.

    This endpoint supports filtering alerts by their acknowledgment status.

    **Permissions:** Requires BILLING role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to view alerts.")

    alerts, total = BillingService.list_alerts(
        tenant=tenant,
        acknowledged=acknowledged,
    )

    return BillingAlertListResponse(
        items=[BillingAlertResponse.from_orm(a) for a in alerts],
        total=total,
    )


@router.post(
    "/alerts/{alert_id}/acknowledge",
    response=BillingAlertResponse,
    summary="Acknowledge a Billing Alert",
)
def acknowledge_alert(request, alert_id: UUID):
    """
    Marks a specific billing alert as acknowledged.

    The alert must belong to the current user's tenant.

    **Permissions:** Requires BILLING role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_billing_user:
        raise PermissionDeniedError("Billing role required to acknowledge alerts.")

    alert = BillingService.acknowledge_alert(alert_id, user)

    if alert.tenant_id != tenant.id:
        raise PermissionDeniedError("Alert not found in this tenant.")

    return BillingAlertResponse.from_orm(alert)


@router.post("/webhooks/lago", response={200: dict}, summary="Handle Lago Webhooks")
async def lago_webhook(request, payload: LagoWebhookPayload):
    """
    Receives and processes webhook events from the Lago billing system.

    This endpoint acts as the integration point for Lago to notify the platform
    about billing-related events (e.g., invoice creation, payment status updates).

    **Security:** Implements HMAC-SHA256 signature verification to ensure
    webhook authenticity and prevent injection attacks.

    **Permissions:** This endpoint does not require user authentication
    as it's called by an external system (Lago).

    **Implements: SEC-001**
    """
    # Verify webhook signature for security
    if not verify_lago_webhook_signature(request, payload.dict()):
        logger.warning(
            f"Invalid webhook signature from {request.META.get('REMOTE_ADDR')}"
        )
        # Return 401 for invalid signature but don't expose details
        return 401, {"status": "unauthorized"}

    # Process the verified webhook
    LagoService.handle_webhook(payload.webhook_type, payload.data)
    return {"status": "ok"}


# Import logger
import logging
logger = logging.getLogger(__name__)
