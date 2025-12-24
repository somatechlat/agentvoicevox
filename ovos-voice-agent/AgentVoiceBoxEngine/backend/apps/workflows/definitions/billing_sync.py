"""
Billing sync workflow for synchronizing usage to Lago.

Runs periodically to sync usage events to the billing system.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

from temporalio import workflow
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)


@dataclass
class BillingSyncInput:
    """Input for billing sync workflow."""

    tenant_id: str = None  # None = sync all tenants
    sync_window_minutes: int = 15


@dataclass
class BillingSyncResult:
    """Result of billing sync workflow."""

    tenants_synced: int
    records_synced: int
    errors: List[str]
    duration_ms: float


@workflow.defn(name="BillingSyncWorkflow")
class BillingSyncWorkflow:
    """
    Workflow for syncing usage to Lago billing system.

    Runs every 15 minutes to:
    - Collect unsynced usage records
    - Send to Lago billing API
    - Mark records as synced
    - Check tenant limits and emit alerts
    """

    @workflow.run
    async def run(self, input: BillingSyncInput) -> BillingSyncResult:
        """
        Run the billing sync workflow.

        Args:
            input: BillingSyncInput with sync configuration

        Returns:
            BillingSyncResult with sync statistics
        """
        import time

        start_time = time.time()
        errors = []
        tenants_synced = 0
        records_synced = 0

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
        )

        # Calculate sync window
        end_time = datetime.utcnow()
        start_time_window = end_time - timedelta(minutes=input.sync_window_minutes)

        workflow.logger.info(
            f"Starting billing sync for window {start_time_window} to {end_time}"
        )

        # Get tenants to sync
        if input.tenant_id:
            tenant_ids = [input.tenant_id]
        else:
            # Get all active tenants
            tenant_ids = await workflow.execute_activity(
                "billing_get_active_tenants",
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

        from apps.workflows.activities.billing import BillingActivities

        # Sync each tenant
        for tenant_id in tenant_ids:
            try:
                # Sync usage to Lago
                result = await workflow.execute_activity(
                    BillingActivities.sync_usage_to_lago,
                    tenant_id,
                    start_time_window,
                    end_time,
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy,
                )

                if result.get("success"):
                    tenants_synced += 1
                    records_synced += result.get("synced_count", 0)
                else:
                    errors.append(f"Tenant {tenant_id}: {result.get('error')}")

                # Check limits
                limits_result = await workflow.execute_activity(
                    BillingActivities.check_limits,
                    tenant_id,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )

                if limits_result.get("any_exceeded"):
                    # Emit billing alert
                    from apps.workflows.activities.notifications import (
                        NotificationActivities,
                        NotificationRequest,
                    )

                    await workflow.execute_activity(
                        NotificationActivities.send_notification,
                        NotificationRequest(
                            tenant_id=tenant_id,
                            user_id=None,
                            notification_type="warning",
                            title="Usage Limit Exceeded",
                            message="Your usage has exceeded plan limits. Please upgrade your plan.",
                            channel="in_app",
                            metadata={"limits": limits_result.get("limits")},
                        ),
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=retry_policy,
                    )

            except Exception as e:
                errors.append(f"Tenant {tenant_id}: {str(e)}")
                workflow.logger.error(f"Failed to sync tenant {tenant_id}: {e}")

        duration = (time.time() - start_time) * 1000

        workflow.logger.info(
            f"Billing sync complete: {tenants_synced} tenants, "
            f"{records_synced} records in {duration:.0f}ms"
        )

        return BillingSyncResult(
            tenants_synced=tenants_synced,
            records_synced=records_synced,
            errors=errors,
            duration_ms=duration,
        )


@workflow.defn(name="GetActiveTenantsWorkflow")
class GetActiveTenantsWorkflow:
    """Helper workflow to get active tenant IDs."""

    @workflow.run
    async def run(self) -> List[str]:
        """Get all active tenant IDs."""
        # This would be an activity in production
        # For now, return empty list
        return []
