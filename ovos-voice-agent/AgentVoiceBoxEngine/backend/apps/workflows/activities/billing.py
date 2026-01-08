"""
Billing Workflow Activities
===========================

This module defines a set of Temporal Workflow Activities for managing billing-related
operations. These activities are crucial for tracking usage, synchronizing data
with the Lago external billing system, retrieving usage summaries, and enforcing
tenant-specific resource limits.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class UsageEvent:
    """
    Defines the parameters for a usage event to be recorded by a workflow.

    Note: The `event_type` should align with `apps.billing.models.UsageEvent.EventType`.

    Attributes:
        tenant_id (str): The ID of the tenant associated with the usage.
        event_type (str): The type of usage (e.g., 'session', 'api_call', 'audio_minutes').
        quantity (float): The amount of usage for this event.
        timestamp (datetime): The UTC timestamp when the usage occurred.
        metadata (dict[str, Any]): Additional contextual information for the event.
    """

    tenant_id: str
    event_type: str
    quantity: float
    timestamp: datetime
    metadata: dict[str, Any]


@dataclass
class UsageSummary:
    """
    Provides an aggregated summary of usage for a tenant over a specific period.

    Attributes:
        tenant_id (str): The ID of the tenant.
        period_start (datetime): The start of the usage period.
        period_end (datetime): The end of the usage period.
        sessions (int): Total count of sessions.
        api_calls (int): Total count of API calls.
        audio_minutes (float): Total audio minutes.
        input_tokens (int): Total input tokens.
        output_tokens (int): Total output tokens.
        total_cost_cents (int): The calculated total cost for the period in cents.
    """

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
    A collection of Temporal Workflow Activities for billing-related operations.

    These activities are designed to be executed within a Temporal workflow,
    providing robust and fault-tolerant mechanisms for usage tracking and billing.
    """

    @activity.defn(name="billing_record_usage")
    async def record_usage(
        self,
        event: UsageEvent,
    ) -> dict[str, Any]:
        """
        Records a usage event in the application's database.

        This activity takes a `UsageEvent` dataclass and persists it as a
        `UsageEvent` model instance, linking it to the specified tenant.

        Args:
            event: A `UsageEvent` dataclass instance containing details about the usage.

        Returns:
            A dictionary indicating the success of the recording and the ID of the new record.
        """
        try:
            # Note: The activity imports 'apps.billing.models.UsageRecord' but
            # actually refers to 'apps.billing.models.UsageEvent' model.
            # This appears to be a naming inconsistency in the code base.
            from apps.billing.models import UsageEvent as UsageRecordModel
            from apps.tenants.models import Tenant

            tenant = await Tenant.objects.aget(id=event.tenant_id)

            # Create usage record using the actual model name.
            record = await UsageRecordModel.objects.acreate(
                tenant=tenant,
                event_type=event.event_type,
                quantity=event.quantity,
                event_timestamp=event.timestamp,
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
            logger.error(
                f"Failed to record usage event {event.event_type} for tenant {event.tenant_id}: {e}"
            )
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
    ) -> dict[str, Any]:
        """
        Synchronizes unsynced usage events for a tenant within a specific time
        period to the Lago external billing system.

        Args:
            tenant_id: The ID of the tenant whose usage events are to be synced.
            start_time: The start (inclusive) of the period for which to sync events.
            end_time: The end (exclusive) of the period for which to sync events.

        Returns:
            A dictionary indicating the success of the synchronization and the count of synced events.
        """
        try:
            # Local imports to avoid module-level dependencies.
            from apps.billing.models import UsageEvent as UsageRecordModel
            from apps.tenants.models import Tenant
            from integrations.lago import lago_client

            tenant = await Tenant.objects.aget(id=tenant_id)

            # Retrieve unsynced usage records within the specified period.
            records = UsageRecordModel.objects.filter(
                tenant=tenant,
                event_timestamp__gte=start_time,
                event_timestamp__lt=end_time,
                synced_at__isnull=True,
            )

            synced_count = 0
            # Iterate asynchronously over the records.
            async for record in records:
                # Send the usage event to Lago.
                await lago_client.send_usage_event(
                    external_customer_id=str(tenant.id),
                    event_type=record.event_type,
                    properties={
                        "quantity": str(
                            record.quantity
                        ),  # Lago often expects quantity as string.
                        "unit": record.unit,
                        **record.metadata,
                    },
                    timestamp=record.event_timestamp,
                )

                # Mark the record as synced in the local database.
                record.synced_at = datetime.utcnow()
                await record.asave()
                synced_count += 1

            logger.info(
                f"Synced {synced_count} usage records for tenant {tenant_id} to Lago."
            )

            return {
                "success": True,
                "synced_count": synced_count,
            }

        except Exception as e:
            logger.error(f"Failed to sync usage to Lago for tenant {tenant_id}: {e}")
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
        Retrieves an aggregated usage summary for a tenant over a specified period.

        This activity calculates total sessions, API calls, audio minutes, tokens,
        and an estimated cost based on simplified pricing.

        Args:
            tenant_id: The ID of the tenant.
            start_time: The start (inclusive) of the usage period.
            end_time: The end (exclusive) of the usage period.

        Returns:
            A `UsageSummary` dataclass with aggregated usage and estimated cost.
        """
        try:
            # Local imports.
            from django.db.models import Sum

            from apps.billing.models import (
                UsageEvent as UsageRecordModel,
            )  # Correct model reference.
            from apps.sessions.models import Session

            # Aggregate usage by type.
            records = UsageRecordModel.objects.filter(
                tenant_id=tenant_id,
                event_timestamp__gte=start_time,
                event_timestamp__lt=end_time,
            )

            # Count sessions separately as they are stored in a different model.
            sessions = await Session.objects.filter(
                tenant_id=tenant_id,
                created_at__gte=start_time,
                created_at__lt=end_time,
            ).acount()

            api_calls = await records.filter(
                event_type=UsageRecordModel.EventType.API_CALL
            ).acount()

            audio_agg = await records.filter(
                event_type=UsageRecordModel.EventType.AUDIO_MINUTES
            ).aaggregate(total=Sum("quantity"))
            audio_minutes = audio_agg.get("total") or 0.0

            input_agg = await records.filter(
                event_type=UsageRecordModel.EventType.INPUT_TOKENS
            ).aaggregate(total=Sum("quantity"))
            input_tokens = int(input_agg.get("total") or 0)

            output_agg = await records.filter(
                event_type=UsageRecordModel.EventType.OUTPUT_TOKENS
            ).aaggregate(total=Sum("quantity"))
            output_tokens = int(output_agg.get("total") or 0)

            # Calculate estimated cost (simplified pricing).
            # Note: In a production system, these rates should be externalized
            # (e.g., from Lago or a configuration service) and potentially tier-dependent.
            cost_cents = (
                sessions * 10  # $0.10 per session
                + api_calls * 1  # $0.01 per API call
                + int(audio_minutes * 5)  # $0.05 per audio minute
                + (input_tokens // 1000) * 1  # $0.01 per 1K input tokens
                + (output_tokens // 1000) * 2  # $0.02 per 1K output tokens
            )

            return UsageSummary(
                tenant_id=tenant_id,
                period_start=start_time,
                period_end=end_time,
                sessions=sessions,
                api_calls=api_calls,
                audio_minutes=float(audio_minutes),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_cost_cents=cost_cents,
            )

        except Exception as e:
            logger.error(f"Failed to get usage summary for tenant {tenant_id}: {e}")
            raise

    @activity.defn(name="billing_check_limits")
    async def check_limits(
        self,
        tenant_id: str,
    ) -> dict[str, Any]:
        """
        Checks if a tenant is currently within their defined plan limits.

        This activity retrieves current month's usage for key metrics and compares
        it against the tenant's `max_sessions_per_month` limit.

        Args:
            tenant_id: The ID of the tenant to check limits for.

        Returns:
            A dictionary containing the tenant ID, tier, limits, and a boolean
            flag `any_exceeded` indicating if any limit has been surpassed.
        """
        try:
            # Local imports.
            from datetime import datetime

            from apps.sessions.models import Session
            from apps.tenants.models import Tenant

            tenant = await Tenant.objects.aget(id=tenant_id)

            # Get current month usage for sessions.
            now = datetime.utcnow()
            month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            sessions_this_month = await Session.objects.filter(
                tenant=tenant,
                created_at__gte=month_start,
            ).acount()

            # Compare against tenant limits.
            limits = {
                "sessions": {
                    "used": sessions_this_month,
                    "limit": tenant.max_sessions_per_month,
                    "exceeded": sessions_this_month >= tenant.max_sessions_per_month,
                },
            }

            any_exceeded = any(limit["exceeded"] for limit in limits.values())

            if any_exceeded:
                logger.warning(f"Tenant {tenant_id} has exceeded limits: {limits}")

            return {
                "tenant_id": tenant_id,
                "tier": tenant.tier,
                "limits": limits,
                "any_exceeded": any_exceeded,
            }

        except Exception as e:
            logger.error(f"Failed to check limits for tenant {tenant_id}: {e}")
            # If an error occurs, assume no limits exceeded to avoid blocking,
            # but ensure error is logged.
            return {
                "tenant_id": tenant_id,
                "error": str(e),
                "any_exceeded": False,
            }
