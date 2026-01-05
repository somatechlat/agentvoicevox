"""
Billing Service Layer
=====================

This module contains all the business logic for billing operations, usage
tracking, and integration with the Lago external billing provider. It handles
recording usage events, calculating current and projected costs, managing
billing alerts, and synchronizing customer and usage data with Lago.
"""

from datetime import timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Count, QuerySet, Sum
from django.utils import timezone

from apps.core.exceptions import NotFoundError, ValidationError
from apps.tenants.models import Tenant
from apps.users.models import User

from .models import BillingAlert, Invoice, UsageEvent


class BillingService:
    """A service class encapsulating all business logic for billing operations."""

    @staticmethod
    @transaction.atomic
    def record_usage(
        tenant: Tenant,
        event_type: str,
        quantity: Decimal,
        unit: str = "count",
        session=None,
        project=None,
        api_key=None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> UsageEvent:
        """
        Records a single usage event in the database and triggers usage threshold checks.

        This method is the primary entry point for tracking billable activity
        within the application.

        Args:
            tenant: The Tenant associated with this usage event.
            event_type: The type of usage event (e.g., 'api_call', 'audio_minutes').
            quantity: The quantity of usage for this event.
            unit: The unit of measurement (e.g., 'count', 'minutes', 'tokens').
            session: (Optional) The Session associated with this event.
            project: (Optional) The Project associated with this event.
            api_key: (Optional) The APIKey associated with this event.
            metadata: (Optional) Additional, unstructured metadata for the event.

        Returns:
            The newly created UsageEvent instance.

        Raises:
            ValidationError: If an invalid `event_type` is provided.
        """
        if event_type not in UsageEvent.EventType.values:
            raise ValidationError(f"Invalid event type: {event_type}")

        event = UsageEvent(
            tenant=tenant,
            event_type=event_type,
            quantity=quantity,
            unit=unit,
            session=session,
            project=project,
            api_key=api_key,
            metadata=metadata or {},
            event_timestamp=timezone.now(),  # Record the actual time of usage.
        )
        event.save()

        # After recording usage, check if any billing alerts need to be triggered.
        BillingService._check_usage_thresholds(tenant)

        return event

    @staticmethod
    def get_current_usage(tenant: Tenant) -> dict[str, Any]:
        """
        Calculates and retrieves aggregated usage data for the current billing period
        (month-to-date) for a specific tenant.

        This provides a snapshot of the tenant's consumption across various metrics.

        Args:
            tenant: The Tenant for whom to retrieve usage data.

        Returns:
            A dictionary containing the current billing period's usage for the tenant,
            including raw usage counts, percentage used against limits, and period dates.
        """
        now = timezone.now()
        # Define the start and end of the current billing period (month).
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # Calculate end of month, handling month rollovers.
        period_end = (period_start + timedelta(days=32)).replace(day=1)

        # Aggregate usage by event type.
        usage_qs = UsageEvent.all_objects.filter(
            tenant=tenant,
            event_timestamp__gte=period_start,
            event_timestamp__lt=period_end,
        )

        usage_by_type = usage_qs.values("event_type").annotate(
            total=Sum("quantity"),
            count=Count("id"),
        )

        # Map aggregated results to a more accessible dictionary.
        usage_map = {u["event_type"]: u["total"] or Decimal("0") for u in usage_by_type}

        # Get session count separately (as it's tracked on the Session model).
        from apps.sessions.models import Session  # Local import to avoid circular dependency.

        session_count = Session.all_objects.filter(
            tenant=tenant,
            created_at__gte=period_start,
            created_at__lt=period_end,
        ).count()

        usage = {
            "period_start": period_start,
            "period_end": period_end,
            "sessions": session_count,
            "api_calls": int(usage_map.get(UsageEvent.EventType.API_CALL, 0)),
            "audio_minutes": usage_map.get(UsageEvent.EventType.AUDIO_MINUTES, Decimal("0")),
            "input_tokens": int(usage_map.get(UsageEvent.EventType.INPUT_TOKENS, 0)),
            "output_tokens": int(usage_map.get(UsageEvent.EventType.OUTPUT_TOKENS, 0)),
            "stt_minutes": usage_map.get(UsageEvent.EventType.STT_MINUTES, Decimal("0")),
            "tts_minutes": usage_map.get(UsageEvent.EventType.TTS_MINUTES, Decimal("0")),
        }

        # Define limits for comparison.
        limits = {
            "sessions": tenant.max_sessions_per_month,
        }

        # Calculate percentage used against defined limits.
        percentage_used = {
            "sessions": (
                (session_count / tenant.max_sessions_per_month * 100)
                if tenant.max_sessions_per_month and tenant.max_sessions_per_month > 0
                else 0
            ),
        }

        return {
            "tenant_id": tenant.id,
            "period_start": period_start,
            "period_end": period_end,
            "usage": usage,
            "limits": limits,
            "percentage_used": percentage_used,
        }

    @staticmethod
    def get_projected_cost(tenant: Tenant) -> dict[str, Any]:
        """
        Calculates the current month-to-date cost and projects the total cost
        to the end of the current billing period for a specific tenant.

        This projection assumes a linear consumption rate based on elapsed days.

        Args:
            tenant: The Tenant for whom to calculate projected costs.

        Returns:
            A dictionary containing current and projected costs, along with a
            breakdown of costs by usage type.
        """
        usage_data = BillingService.get_current_usage(tenant)
        usage = usage_data["usage"]

        # Example pricing rates. In a production system, these should be dynamically
        # retrieved from a configuration or the billing provider (Lago).
        rates = {
            "session": Decimal("0.01"),  # $0.01 per session
            "audio_minute": Decimal("0.006"),  # $0.006 per audio minute
            "input_token": Decimal("0.00001"),  # $0.00001 per input token
            "output_token": Decimal("0.00003"),  # $0.00003 per output token
            # Add other event types as needed.
        }

        # Calculate current cost based on actual usage so far.
        current_cost = (
            Decimal(usage["sessions"]) * rates["session"]
            + usage["audio_minutes"] * rates["audio_minute"]
            + Decimal(usage["input_tokens"]) * rates["input_token"]
            + Decimal(usage["output_tokens"]) * rates["output_token"]
        )

        # Project to the end of the month.
        now = timezone.now()
        period_start = usage_data["period_start"]
        period_end = usage_data["period_end"]

        days_in_month = (period_end - period_start).days
        days_elapsed = (now - period_start).days + 1

        if days_elapsed > 0 and days_in_month > 0:
            daily_rate = current_cost / days_elapsed
            projected_cost = daily_rate * days_in_month
        else:
            projected_cost = current_cost

        # Breakdown of current cost by usage type.
        breakdown = {
            "sessions": Decimal(usage["sessions"]) * rates["session"],
            "audio": usage["audio_minutes"] * rates["audio_minute"],
            "input_tokens": Decimal(usage["input_tokens"]) * rates["input_token"],
            "output_tokens": Decimal(usage["output_tokens"]) * rates["output_token"],
        }

        return {
            "tenant_id": tenant.id,
            "current_month_cost": current_cost,
            "projected_month_cost": projected_cost,
            "currency": "USD",
            "breakdown": breakdown,
        }

    @staticmethod
    def list_invoices(
        tenant: Tenant,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[QuerySet, int]:
        """
        Retrieves a paginated list of invoices for a specific tenant.

        Args:
            tenant: The Tenant for whom to list invoices.
            status: (Optional) Filter invoices by their status (e.g., 'paid', 'finalized').
            page: The page number for pagination.
            page_size: The number of items per page.

        Returns:
            A tuple containing:
            - A queryset of `Invoice` instances for the requested page.
            - An integer representing the total count of matching invoices.
        """
        qs = Invoice.all_objects.filter(tenant=tenant)

        if status:
            qs = qs.filter(status=status)

        total = qs.count()
        offset = (page - 1) * page_size
        paginated_qs = qs[offset : offset + page_size]

        return paginated_qs, total

    @staticmethod
    def get_invoice(invoice_id: UUID) -> Invoice:
        """
        Retrieves a single invoice by its primary key (ID).

        Args:
            invoice_id: The UUID of the invoice to retrieve.

        Returns:
            The `Invoice` instance.

        Raises:
            NotFoundError: If an invoice with the specified ID does not exist.
        """
        try:
            return Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            raise NotFoundError(f"Invoice {invoice_id} not found")

    @staticmethod
    def list_alerts(
        tenant: Tenant,
        acknowledged: Optional[bool] = None,
    ) -> tuple[list[BillingAlert], int]:
        """
        Retrieves a list of billing alerts for a specific tenant.

        Args:
            tenant: The Tenant for whom to list alerts.
            acknowledged: (Optional) Filter alerts by their acknowledgment status.

        Returns:
            A tuple containing:
            - A list of `BillingAlert` instances.
            - An integer representing the total count of matching alerts.
        """
        qs = BillingAlert.all_objects.filter(tenant=tenant)

        if acknowledged is not None:
            qs = qs.filter(acknowledged=acknowledged)

        total = qs.count()
        alerts = list(qs)

        return alerts, total

    @staticmethod
    @transaction.atomic
    def acknowledge_alert(alert_id: UUID, user: User) -> BillingAlert:
        """
        Marks a specific billing alert as acknowledged by a user.

        Args:
            alert_id: The UUID of the billing alert to acknowledge.
            user: The `User` instance who acknowledged the alert.

        Returns:
            The updated `BillingAlert` instance.

        Raises:
            NotFoundError: If the billing alert does not exist.
        """
        try:
            alert = BillingAlert.objects.get(id=alert_id)
        except BillingAlert.DoesNotExist:
            raise NotFoundError(f"Alert {alert_id} not found")

        alert.acknowledge(user)
        return alert

    @staticmethod
    def _check_usage_thresholds(tenant: Tenant) -> None:
        """
        Internal method to check a tenant's current usage against predefined
        thresholds and create `BillingAlert`s if necessary.

        This method is typically called after a new `UsageEvent` is recorded.
        """
        usage_data = BillingService.get_current_usage(tenant)
        percentage = usage_data["percentage_used"].get("sessions", 0)

        # Check for 80% warning threshold.
        if 80 <= percentage < 90:
            BillingService._create_alert_if_not_exists(
                tenant=tenant,
                alert_type=BillingAlert.AlertType.USAGE_WARNING,
                resource_type="sessions",
                current_value=Decimal(usage_data["usage"]["sessions"]),
                threshold_value=Decimal(tenant.max_sessions_per_month * 0.8),
                message=f"Session usage at {percentage:.1f}% of monthly limit.",
            )
        # Check for 90% critical threshold.
        elif 90 <= percentage < 100:
            BillingService._create_alert_if_not_exists(
                tenant=tenant,
                alert_type=BillingAlert.AlertType.USAGE_CRITICAL,
                resource_type="sessions",
                current_value=Decimal(usage_data["usage"]["sessions"]),
                threshold_value=Decimal(tenant.max_sessions_per_month * 0.9),
                message=f"Session usage at {percentage:.1f}% of monthly limit.",
            )
        # Check for 100% (limit exceeded) threshold.
        elif percentage >= 100:
            BillingService._create_alert_if_not_exists(
                tenant=tenant,
                alert_type=BillingAlert.AlertType.LIMIT_EXCEEDED,
                resource_type="sessions",
                current_value=Decimal(usage_data["usage"]["sessions"]),
                threshold_value=Decimal(tenant.max_sessions_per_month),
                message="Monthly session limit exceeded.",
            )

    @staticmethod
    def _create_alert_if_not_exists(
        tenant: Tenant,
        alert_type: str,
        resource_type: str,
        current_value: Decimal,
        threshold_value: Decimal,
        message: str,
    ) -> Optional[BillingAlert]:
        """
        Internal method to create a new `BillingAlert` only if a similar
        unacknowledged alert for the current billing period does not already exist.
        """
        now = timezone.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Check if an alert of this type for this resource already exists and is unacknowledged.
        existing = BillingAlert.all_objects.filter(
            tenant=tenant,
            alert_type=alert_type,
            resource_type=resource_type,
            created_at__gte=period_start,
            acknowledged=False,
        ).exists()

        if existing:
            return None  # Do not create duplicate alerts.

        alert = BillingAlert(
            tenant=tenant,
            alert_type=alert_type,
            message=message,
            resource_type=resource_type,
            current_value=current_value,
            threshold_value=threshold_value,
        )
        alert.save()
        return alert


class LagoService:
    """
    A service class dedicated to handling interactions with the Lago billing API.
    """

    @staticmethod
    @transaction.atomic
    def sync_customer(tenant: Tenant) -> str:
        """
        Synchronizes a `Tenant` record with Lago, creating or updating a customer
        entry in the Lago system.

        If successful, it updates the `Tenant`'s `billing_id` with the Lago customer ID.

        Args:
            tenant: The `Tenant` instance to synchronize.

        Returns:
            The Lago customer ID (`lago_id`).

        Raises:
            Exception: If the Lago API call fails.
        """
        import httpx
        from django.conf import settings  # Local import to avoid circular dependency.

        lago_url = getattr(settings, "LAGO_API_URL", None)
        lago_key = getattr(settings, "LAGO_API_KEY", None)

        if not lago_url or not lago_key:
            raise Exception("Lago API URL or Key not configured.")

        # Construct the payload for Lago customer creation/update.
        payload = {
            "customer": {
                "external_id": str(tenant.id),  # Our internal tenant ID as Lago's external ID.
                "name": tenant.name,
                "email": "billing@example.com",  # Placeholder; ideally from TenantSettings or primary user.
                "metadata": [
                    {"key": "tier", "value": tenant.tier},
                    {"key": "slug", "value": tenant.slug},
                ],
            }
        }

        response = httpx.post(
            f"{lago_url}/api/v1/customers",
            json=payload,
            headers={"Authorization": f"Bearer {lago_key}", "Content-Type": "application/json"},
            timeout=30,
        )

        if response.status_code in [200, 201]:
            data = response.json()
            lago_id = data["customer"]["lago_id"]
            tenant.billing_id = lago_id
            tenant.save(update_fields=["billing_id", "updated_at"])
            return lago_id
        else:
            raise Exception(f"Lago customer sync failed: {response.text}")

    @staticmethod
    @transaction.atomic
    def send_usage_events(events: list[UsageEvent]) -> int:
        """
        Sends a list of `UsageEvent`s to the Lago API for billing purposes.

        Each event is sent individually, and its sync status is updated accordingly.

        Args:
            events: A list of `UsageEvent` instances to send.

        Returns:
            The number of `UsageEvent`s successfully synchronized.
        """
        import httpx
        from django.conf import settings  # Local import.

        lago_url = getattr(settings, "LAGO_API_URL", None)
        lago_key = getattr(settings, "LAGO_API_KEY", None)

        if not lago_url or not lago_key:
            # Mark all events with error if Lago is not configured
            for event in events:
                event.mark_sync_error("Lago API URL or Key not configured.")
            return 0

        synced = 0
        for event in events:
            # Construct the payload for a single Lago usage event.
            payload = {
                "event": {
                    "transaction_id": str(event.id),  # Unique ID for the event in Lago.
                    "external_customer_id": str(event.tenant_id),  # Link to the Lago customer.
                    "code": event.event_type,  # The billing metric code in Lago.
                    "timestamp": int(event.event_timestamp.timestamp()),
                    "properties": {
                        "quantity": str(event.quantity),
                        "unit": event.unit,
                        **event.metadata,
                    },
                }
            }

            try:
                response = httpx.post(
                    f"{lago_url}/api/v1/events",
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {lago_key}",
                        "Content-Type": "application/json",
                    },
                    timeout=30,
                )

                if response.status_code in [200, 201]:
                    data = response.json()
                    lago_event_id = data.get("event", {}).get("lago_id", "")
                    event.mark_synced(lago_event_id)
                    synced += 1
                else:
                    # Record error for the event if Lago returns a non-success status.
                    event.mark_sync_error(response.text)
            except Exception as e:
                # Record any network or other exceptions during the API call.
                event.mark_sync_error(str(e))
        return synced

    @staticmethod
    @transaction.atomic
    def handle_webhook(webhook_type: str, data: dict[str, Any]) -> None:
        """
        Processes incoming webhooks from Lago to update local billing data.

        This method acts as a dispatcher to specific handlers based on the
        `webhook_type`.

        Args:
            webhook_type: The type of webhook event (e.g., 'invoice.created').
            data: The full payload of the webhook event from Lago.
        """
        if webhook_type == "invoice.created":
            LagoService._handle_invoice_created(data)
        elif webhook_type == "invoice.finalized":
            LagoService._handle_invoice_finalized(data)
        elif webhook_type == "invoice.payment_status_updated":
            LagoService._handle_payment_status_updated(data)
        # Add more webhook types as needed.

    @staticmethod
    def _handle_invoice_created(data: dict[str, Any]) -> None:
        """
        Internal handler for the `invoice.created` webhook from Lago.

        Creates a new `Invoice` record in the local database or updates an
        existing one if it's a re-creation.
        """
        invoice_data = data.get("invoice", {})
        customer_id = invoice_data.get("customer", {}).get("external_id")

        if not customer_id:
            return  # Cannot process without a customer ID.

        try:
            tenant = Tenant.objects.get(id=customer_id)
        except Tenant.DoesNotExist:
            return  # Tenant not found locally.

        # Create or update the local Invoice record.
        Invoice.objects.update_or_create(
            lago_invoice_id=invoice_data.get("lago_id"),
            defaults={
                "tenant": tenant,
                "invoice_number": invoice_data.get("number", ""),
                "amount_cents": invoice_data.get("amount_cents", 0),
                "taxes_amount_cents": invoice_data.get("taxes_amount_cents", 0),
                "total_amount_cents": invoice_data.get("total_amount_cents", 0),
                "currency": invoice_data.get("currency", "USD"),
                "status": Invoice.Status.DRAFT,  # Newly created invoices from Lago are often in draft.
                "issuing_date": invoice_data.get("issuing_date"),
                "payment_due_date": invoice_data.get("payment_due_date"),
                "metadata": invoice_data,  # Store full Lago payload as metadata.
            },
        )

    @staticmethod
    def _handle_invoice_finalized(data: dict[str, Any]) -> None:
        """
        Internal handler for the `invoice.finalized` webhook from Lago.

        Updates the status of a local `Invoice` record to 'FINALIZED' and
        stores the URL to the invoice PDF.
        """
        invoice_data = data.get("invoice", {})
        lago_id = invoice_data.get("lago_id")

        try:
            invoice = Invoice.objects.get(lago_invoice_id=lago_id)
            invoice.status = Invoice.Status.FINALIZED
            invoice.pdf_url = invoice_data.get("file_url", "")
            invoice.save(update_fields=["status", "pdf_url", "updated_at"])
        except Invoice.DoesNotExist:
            pass  # Invoice not found locally, might be an old event or out of sync.

    @staticmethod
    def _handle_payment_status_updated(data: dict[str, Any]) -> None:
        """
        Internal handler for the `invoice.payment_status_updated` webhook from Lago.

        Updates the status of a local `Invoice` record based on payment outcome
        and creates a `PAYMENT_FAILED` alert if payment fails.
        """
        invoice_data = data.get("invoice", {})
        lago_id = invoice_data.get("lago_id")
        payment_status = invoice_data.get("payment_status")

        status_map = {
            "succeeded": Invoice.Status.PAID,
            "failed": Invoice.Status.FAILED,
            # Add other Lago payment statuses if necessary.
        }

        try:
            invoice = Invoice.objects.get(lago_invoice_id=lago_id)
            if payment_status in status_map:
                invoice.status = status_map[payment_status]
                invoice.save(update_fields=["status", "updated_at"])

                # If payment failed, create a billing alert for the tenant.
                if payment_status == "failed":
                    BillingAlert.objects.create(
                        tenant=invoice.tenant,
                        alert_type=BillingAlert.AlertType.PAYMENT_FAILED,
                        message=f"Payment failed for invoice {invoice.invoice_number}",
                        metadata={"invoice_id": str(invoice.id)},
                    )
        except Invoice.DoesNotExist:
            pass  # Invoice not found locally.
