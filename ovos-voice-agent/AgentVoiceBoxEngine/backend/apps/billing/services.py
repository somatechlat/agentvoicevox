"""
Billing service layer.

Contains all business logic for billing operations and Lago integration.
"""
from datetime import timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.db import transaction
from django.db.models import Count, QuerySet, Sum
from django.utils import timezone

from apps.core.exceptions import NotFoundError, ValidationError
from apps.tenants.models import Tenant

from .models import BillingAlert, Invoice, UsageEvent


class BillingService:
    """Service class for billing operations."""

    @staticmethod
    def record_usage(
        tenant: Tenant,
        event_type: str,
        quantity: Decimal,
        unit: str = "count",
        session=None,
        project=None,
        api_key=None,
        metadata: Dict[str, Any] = None,
    ) -> UsageEvent:
        """
        Record a usage event.

        Args:
            tenant: Tenant for the usage
            event_type: Type of usage event
            quantity: Quantity of usage
            unit: Unit of measurement
            session: Associated session (optional)
            project: Associated project (optional)
            api_key: Associated API key (optional)
            metadata: Additional metadata (optional)

        Returns:
            Created UsageEvent
        """
        # Validate event type
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
            event_timestamp=timezone.now(),
        )
        event.save()

        # Check usage thresholds
        BillingService._check_usage_thresholds(tenant)

        return event

    @staticmethod
    def get_current_usage(tenant: Tenant) -> Dict[str, Any]:
        """
        Get current billing period usage.

        Returns:
            Dictionary with usage data
        """
        now = timezone.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        period_end = (period_start + timedelta(days=32)).replace(day=1)

        # Aggregate usage by type
        usage_qs = UsageEvent.all_objects.filter(
            tenant=tenant,
            event_timestamp__gte=period_start,
            event_timestamp__lt=period_end,
        )

        usage_by_type = usage_qs.values("event_type").annotate(
            total=Sum("quantity"),
            count=Count("id"),
        )

        usage_map = {u["event_type"]: u["total"] or Decimal("0") for u in usage_by_type}

        # Get session count
        from apps.sessions.models import Session
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

        # Calculate percentage used
        limits = {
            "sessions": tenant.max_sessions_per_month,
        }

        percentage_used = {
            "sessions": (session_count / tenant.max_sessions_per_month * 100)
            if tenant.max_sessions_per_month > 0
            else 0,
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
    def get_projected_cost(tenant: Tenant) -> Dict[str, Any]:
        """
        Get projected cost for current billing period.

        Returns:
            Dictionary with projected cost data
        """
        usage_data = BillingService.get_current_usage(tenant)
        usage = usage_data["usage"]

        # Pricing (example rates - should come from Lago/config)
        rates = {
            "session": Decimal("0.01"),  # $0.01 per session
            "audio_minute": Decimal("0.006"),  # $0.006 per audio minute
            "input_token": Decimal("0.00001"),  # $0.00001 per input token
            "output_token": Decimal("0.00003"),  # $0.00003 per output token
        }

        # Calculate current cost
        current_cost = (
            Decimal(usage["sessions"]) * rates["session"]
            + usage["audio_minutes"] * rates["audio_minute"]
            + Decimal(usage["input_tokens"]) * rates["input_token"]
            + Decimal(usage["output_tokens"]) * rates["output_token"]
        )

        # Project to end of month
        now = timezone.now()
        days_in_month = (usage_data["period_end"] - usage_data["period_start"]).days
        days_elapsed = (now - usage_data["period_start"]).days + 1

        if days_elapsed > 0:
            daily_rate = current_cost / days_elapsed
            projected_cost = daily_rate * days_in_month
        else:
            projected_cost = current_cost

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
    ) -> Tuple[QuerySet, int]:
        """
        List invoices for a tenant.

        Returns:
            Tuple of (queryset, total_count)
        """
        qs = Invoice.all_objects.filter(tenant=tenant)

        if status:
            qs = qs.filter(status=status)

        total = qs.count()
        offset = (page - 1) * page_size
        qs = qs[offset : offset + page_size]

        return qs, total

    @staticmethod
    def get_invoice(invoice_id: UUID) -> Invoice:
        """
        Get invoice by ID.

        Raises:
            NotFoundError: If invoice not found
        """
        try:
            return Invoice.objects.get(id=invoice_id)
        except Invoice.DoesNotExist:
            raise NotFoundError(f"Invoice {invoice_id} not found")

    @staticmethod
    def list_alerts(
        tenant: Tenant,
        acknowledged: Optional[bool] = None,
    ) -> Tuple[List[BillingAlert], int]:
        """
        List billing alerts for a tenant.

        Returns:
            Tuple of (alerts, total_count)
        """
        qs = BillingAlert.all_objects.filter(tenant=tenant)

        if acknowledged is not None:
            qs = qs.filter(acknowledged=acknowledged)

        total = qs.count()
        alerts = list(qs)

        return alerts, total

    @staticmethod
    @transaction.atomic
    def acknowledge_alert(alert_id: UUID, user) -> BillingAlert:
        """
        Acknowledge a billing alert.

        Raises:
            NotFoundError: If alert not found
        """
        try:
            alert = BillingAlert.objects.get(id=alert_id)
        except BillingAlert.DoesNotExist:
            raise NotFoundError(f"Alert {alert_id} not found")

        alert.acknowledge(user)
        return alert

    @staticmethod
    def _check_usage_thresholds(tenant: Tenant) -> None:
        """Check usage thresholds and create alerts if needed."""
        usage_data = BillingService.get_current_usage(tenant)
        percentage = usage_data["percentage_used"].get("sessions", 0)

        # Check for 80% warning
        if 80 <= percentage < 90:
            BillingService._create_alert_if_not_exists(
                tenant=tenant,
                alert_type=BillingAlert.AlertType.USAGE_WARNING,
                resource_type="sessions",
                current_value=Decimal(usage_data["usage"]["sessions"]),
                threshold_value=Decimal(tenant.max_sessions_per_month * 0.8),
                message=f"Session usage at {percentage:.1f}% of monthly limit",
            )

        # Check for 90% critical
        elif 90 <= percentage < 100:
            BillingService._create_alert_if_not_exists(
                tenant=tenant,
                alert_type=BillingAlert.AlertType.USAGE_CRITICAL,
                resource_type="sessions",
                current_value=Decimal(usage_data["usage"]["sessions"]),
                threshold_value=Decimal(tenant.max_sessions_per_month * 0.9),
                message=f"Session usage at {percentage:.1f}% of monthly limit",
            )

        # Check for limit exceeded
        elif percentage >= 100:
            BillingService._create_alert_if_not_exists(
                tenant=tenant,
                alert_type=BillingAlert.AlertType.LIMIT_EXCEEDED,
                resource_type="sessions",
                current_value=Decimal(usage_data["usage"]["sessions"]),
                threshold_value=Decimal(tenant.max_sessions_per_month),
                message="Monthly session limit exceeded",
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
        """Create alert if one doesn't exist for this period."""
        now = timezone.now()
        period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Check if alert already exists for this period
        existing = BillingAlert.all_objects.filter(
            tenant=tenant,
            alert_type=alert_type,
            resource_type=resource_type,
            created_at__gte=period_start,
        ).exists()

        if existing:
            return None

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
    """Service class for Lago integration."""

    @staticmethod
    def sync_customer(tenant: Tenant) -> str:
        """
        Sync tenant as customer to Lago.

        Returns:
            Lago customer ID
        """
        from django.conf import settings
        import httpx

        lago_url = settings.LAGO_API_URL
        lago_key = settings.LAGO_API_KEY

        payload = {
            "customer": {
                "external_id": str(tenant.id),
                "name": tenant.name,
                "email": "",  # Would come from tenant settings
                "metadata": [
                    {"key": "tier", "value": tenant.tier},
                    {"key": "slug", "value": tenant.slug},
                ],
            }
        }

        response = httpx.post(
            f"{lago_url}/api/v1/customers",
            json=payload,
            headers={
                "Authorization": f"Bearer {lago_key}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if response.status_code in [200, 201]:
            data = response.json()
            lago_id = data["customer"]["lago_id"]
            tenant.billing_id = lago_id
            tenant.save(update_fields=["billing_id", "updated_at"])
            return lago_id
        else:
            raise Exception(f"Lago sync failed: {response.text}")

    @staticmethod
    def send_usage_events(events: List[UsageEvent]) -> int:
        """
        Send usage events to Lago.

        Returns:
            Number of events synced
        """
        from django.conf import settings
        import httpx

        lago_url = settings.LAGO_API_URL
        lago_key = settings.LAGO_API_KEY

        synced = 0
        for event in events:
            payload = {
                "event": {
                    "transaction_id": str(event.id),
                    "external_customer_id": str(event.tenant_id),
                    "code": event.event_type,
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
                    event.mark_synced(data.get("event", {}).get("lago_id", ""))
                    synced += 1
                else:
                    event.mark_sync_error(response.text)
            except Exception as e:
                event.mark_sync_error(str(e))

        return synced

    @staticmethod
    def handle_webhook(webhook_type: str, data: Dict[str, Any]) -> None:
        """
        Handle Lago webhook.

        Args:
            webhook_type: Type of webhook event
            data: Webhook payload data
        """
        if webhook_type == "invoice.created":
            LagoService._handle_invoice_created(data)
        elif webhook_type == "invoice.finalized":
            LagoService._handle_invoice_finalized(data)
        elif webhook_type == "invoice.payment_status_updated":
            LagoService._handle_payment_status_updated(data)

    @staticmethod
    def _handle_invoice_created(data: Dict[str, Any]) -> None:
        """Handle invoice.created webhook."""
        invoice_data = data.get("invoice", {})
        customer_id = invoice_data.get("customer", {}).get("external_id")

        if not customer_id:
            return

        try:
            tenant = Tenant.objects.get(id=customer_id)
        except Tenant.DoesNotExist:
            return

        Invoice.objects.update_or_create(
            lago_invoice_id=invoice_data.get("lago_id"),
            defaults={
                "tenant": tenant,
                "invoice_number": invoice_data.get("number", ""),
                "amount_cents": invoice_data.get("amount_cents", 0),
                "taxes_amount_cents": invoice_data.get("taxes_amount_cents", 0),
                "total_amount_cents": invoice_data.get("total_amount_cents", 0),
                "currency": invoice_data.get("currency", "USD"),
                "status": Invoice.Status.DRAFT,
                "issuing_date": invoice_data.get("issuing_date"),
                "payment_due_date": invoice_data.get("payment_due_date"),
                "metadata": invoice_data,
            },
        )

    @staticmethod
    def _handle_invoice_finalized(data: Dict[str, Any]) -> None:
        """Handle invoice.finalized webhook."""
        invoice_data = data.get("invoice", {})
        lago_id = invoice_data.get("lago_id")

        try:
            invoice = Invoice.objects.get(lago_invoice_id=lago_id)
            invoice.status = Invoice.Status.FINALIZED
            invoice.pdf_url = invoice_data.get("file_url", "")
            invoice.save(update_fields=["status", "pdf_url", "updated_at"])
        except Invoice.DoesNotExist:
            pass

    @staticmethod
    def _handle_payment_status_updated(data: Dict[str, Any]) -> None:
        """Handle invoice.payment_status_updated webhook."""
        invoice_data = data.get("invoice", {})
        lago_id = invoice_data.get("lago_id")
        payment_status = invoice_data.get("payment_status")

        status_map = {
            "succeeded": Invoice.Status.PAID,
            "failed": Invoice.Status.FAILED,
        }

        try:
            invoice = Invoice.objects.get(lago_invoice_id=lago_id)
            if payment_status in status_map:
                invoice.status = status_map[payment_status]
                invoice.save(update_fields=["status", "updated_at"])

                # Create alert for failed payment
                if payment_status == "failed":
                    BillingAlert.objects.create(
                        tenant=invoice.tenant,
                        alert_type=BillingAlert.AlertType.PAYMENT_FAILED,
                        message=f"Payment failed for invoice {invoice.invoice_number}",
                        metadata={"invoice_id": str(invoice.id)},
                    )
        except Invoice.DoesNotExist:
            pass
