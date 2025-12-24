"""
Billing activities for Temporal workflows.

Handles usage tracking and billing sync with Lago.
"""
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class UsageEvent:
    """A usage event for billing."""

    tenant_id: str
    event_type: str  # session, api_call, audio_minutes, tokens
    quantity: float
    timestamp: datetime
    metadata: Dict[str, Any]


@dataclass
class UsageSummary:
    """Summary of usage for a tenant."""

    tenant_id: str
    period_start: datetime
    period_end: datetime
    sessions: int
    api_calls: int
    audio_minutes: float
    input_tokens: int
    output_tokens: int
    total_cost_cents: int


class BillingActivities:
    """
    Billing activities for usage tracking and sync.

    Activities:
    - record_usage: Record a usage event
    - sync_usage_to_lago: Sync usage to Lago billing
    - get_usage_summary: Get usage summary for tenant
    - check_limits: Check if tenant is within limits
    """

    @activity.defn(name="billing_record_usage")
    async def record_usage(
        self,
        event: UsageEvent,
    ) -> Dict[str, Any]:
        """
        Record a usage event.

        Args:
            event: UsageEvent to record

        Returns:
            Dict with recording result
        """
        try:
            from apps.billing.models import UsageRecord
            from apps.tenants.models import Tenant

            tenant = await Tenant.objects.aget(id=event.tenant_id)

            # Create usage record
            record = await UsageRecord.objects.acreate(
                tenant=tenant,
                event_type=event.event_type,
                quantity=event.quantity,
                timestamp=event.timestamp,
                metadata=event.metadata,
            )

            logger.info(
                f"Recorded usage for tenant {event.tenant_id}: "
                f"{event.event_type} = {event.quantity}"
            )

            return {
                "success": True,
                "record_id": str(record.id),
            }

        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @activity.defn(name="billing_sync_to_lago")
    async def sync_usage_to_lago(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """
        Sync usage events to Lago billing system.

        Args:
            tenant_id: Tenant to sync
            start_time: Start of sync period
            end_time: End of sync period

        Returns:
            Dict with sync result
        """
        try:
            from integrations.lago import lago_client
            from apps.billing.models import UsageRecord
            from apps.tenants.models import Tenant

            tenant = await Tenant.objects.aget(id=tenant_id)

            # Get unsynced usage records
            records = UsageRecord.objects.filter(
                tenant=tenant,
                timestamp__gte=start_time,
                timestamp__lt=end_time,
                synced_at__isnull=True,
            )

            synced_count = 0
            async for record in records:
                # Send to Lago
                await lago_client.send_usage_event(
                    external_customer_id=str(tenant.id),
                    event_type=record.event_type,
                    properties={
                        "quantity": record.quantity,
                        **record.metadata,
                    },
                    timestamp=record.timestamp,
                )

                # Mark as synced
                record.synced_at = datetime.utcnow()
                await record.asave()
                synced_count += 1

            logger.info(
                f"Synced {synced_count} usage records for tenant {tenant_id}"
            )

            return {
                "success": True,
                "synced_count": synced_count,
            }

        except Exception as e:
            logger.error(f"Failed to sync usage to Lago: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    @activity.defn(name="billing_get_usage_summary")
    async def get_usage_summary(
        self,
        tenant_id: str,
        start_time: datetime,
        end_time: datetime,
    ) -> UsageSummary:
        """
        Get usage summary for a tenant.

        Args:
            tenant_id: Tenant identifier
            start_time: Start of period
            end_time: End of period

        Returns:
            UsageSummary with aggregated usage
        """
        try:
            from django.db.models import Sum, Count
            from apps.billing.models import UsageRecord

            # Aggregate usage by type
            records = UsageRecord.objects.filter(
                tenant_id=tenant_id,
                timestamp__gte=start_time,
                timestamp__lt=end_time,
            )

            sessions = await records.filter(
                event_type="session"
            ).acount()

            api_calls = await records.filter(
                event_type="api_call"
            ).acount()

            audio_agg = await records.filter(
                event_type="audio_minutes"
            ).aaggregate(total=Sum("quantity"))
            audio_minutes = audio_agg.get("total") or 0.0

            input_agg = await records.filter(
                event_type="input_tokens"
            ).aaggregate(total=Sum("quantity"))
            input_tokens = int(input_agg.get("total") or 0)

            output_agg = await records.filter(
                event_type="output_tokens"
            ).aaggregate(total=Sum("quantity"))
            output_tokens = int(output_agg.get("total") or 0)

            # Calculate cost (simplified pricing)
            # Real implementation would use Lago pricing
            cost_cents = (
                sessions * 10 +  # $0.10 per session
                api_calls * 1 +  # $0.01 per API call
                int(audio_minutes * 5) +  # $0.05 per audio minute
                (input_tokens // 1000) * 1 +  # $0.01 per 1K input tokens
                (output_tokens // 1000) * 2  # $0.02 per 1K output tokens
            )

            return UsageSummary(
                tenant_id=tenant_id,
                period_start=start_time,
                period_end=end_time,
                sessions=sessions,
                api_calls=api_calls,
                audio_minutes=audio_minutes,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_cost_cents=cost_cents,
            )

        except Exception as e:
            logger.error(f"Failed to get usage summary: {e}")
            raise

    @activity.defn(name="billing_check_limits")
    async def check_limits(
        self,
        tenant_id: str,
    ) -> Dict[str, Any]:
        """
        Check if tenant is within their plan limits.

        Args:
            tenant_id: Tenant identifier

        Returns:
            Dict with limit check results
        """
        try:
            from apps.tenants.models import Tenant
            from apps.sessions.models import Session
            from datetime import datetime, timedelta

            tenant = await Tenant.objects.aget(id=tenant_id)

            # Get current month usage
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            sessions_this_month = await Session.objects.filter(
                tenant=tenant,
                created_at__gte=month_start,
            ).acount()

            # Check against limits
            limits = {
                "sessions": {
                    "used": sessions_this_month,
                    "limit": tenant.max_sessions_per_month,
                    "exceeded": sessions_this_month >= tenant.max_sessions_per_month,
                },
            }

            any_exceeded = any(l["exceeded"] for l in limits.values())

            if any_exceeded:
                logger.warning(
                    f"Tenant {tenant_id} has exceeded limits: {limits}"
                )

            return {
                "tenant_id": tenant_id,
                "tier": tenant.tier,
                "limits": limits,
                "any_exceeded": any_exceeded,
            }

        except Exception as e:
            logger.error(f"Failed to check limits: {e}")
            return {
                "tenant_id": tenant_id,
                "error": str(e),
                "any_exceeded": False,
            }
