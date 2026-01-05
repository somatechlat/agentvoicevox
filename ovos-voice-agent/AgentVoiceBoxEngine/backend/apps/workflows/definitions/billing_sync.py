"""
Billing Synchronization Workflow
================================

This module defines the `BillingSyncWorkflow`, a Temporal Workflow responsible
for periodically collecting unsynced usage events, pushing them to the Lago
external billing system, and performing checks against tenant resource limits.
It ensures that usage data is accurately recorded and that tenants are notified
of potential overages.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from temporalio import workflow
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)


@dataclass
class BillingSyncInput:
    """
    Defines the input parameters for the `BillingSyncWorkflow`.

    Attributes:
        tenant_id (Optional[str]): The ID of a specific tenant to sync.
                                   If None, the workflow will attempt to sync for all active tenants.
        sync_window_minutes (int): The duration (in minutes) of the historical
                                   window for which unsynced usage events should be collected.
    """

    tenant_id: Optional[str] = None
    sync_window_minutes: int = 15


@dataclass
class BillingSyncResult:
    """
    Represents the structured result of the `BillingSyncWorkflow` execution.

    Attributes:
        tenants_synced (int): The total number of tenants for which usage was processed.
        records_synced (int): The total number of usage records successfully synced to Lago.
        errors (list[str]): A list of any errors encountered during the sync process.
        duration_ms (float): The total execution time of the workflow in milliseconds.
    """

    tenants_synced: int
    records_synced: int
    errors: list[str]
    duration_ms: float


@workflow.defn(name="BillingSyncWorkflow")
class BillingSyncWorkflow:
    """
    Temporal Workflow for orchestrating the synchronization of billing usage
    data to Lago and performing related billing checks.

    This workflow typically runs on a schedule (e.g., every 15 minutes) and:
    1.  Determines the time window for which to collect unsynced usage.
    2.  Fetches a list of active tenants (or a specific tenant if provided).
    3.  For each tenant, it executes activities to:
        - Sync usage events to the Lago billing API.
        - Mark synced records in the local database.
        - Check tenant-specific usage against defined limits.
        - Emit notifications if limits are exceeded.
    """

    @workflow.run
    async def run(self, input: BillingSyncInput) -> BillingSyncResult:
        """
        Executes the main logic of the billing synchronization workflow.

        Args:
            input: A `BillingSyncInput` object specifying tenant scope and sync window.

        Returns:
            A `BillingSyncResult` object containing statistics and errors from the sync.
        """
        import time

        start_time = time.time()
        errors = []
        tenants_synced = 0
        records_synced = 0

        # Define a retry policy for activities to handle transient failures.
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
        )

        # Calculate the time window for collecting usage events.
        end_time = datetime.utcnow()
        start_time_window = end_time - timedelta(minutes=input.sync_window_minutes)

        workflow.logger.info(
            f"Starting BillingSyncWorkflow for window {start_time_window.isoformat()} to {end_time.isoformat()}"
        )

        # Determine which tenants to sync.
        if input.tenant_id:
            tenant_ids = [input.tenant_id]
        else:
            # Execute an activity to get IDs of all active tenants.
            # Note: The activity "billing_get_active_tenants" is called here.
            # It's currently a placeholder or refers to an external implementation.
            tenant_ids = await workflow.execute_activity(
                "billing_get_active_tenants",
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

        # Import activities locally within the workflow run function.
        from apps.workflows.activities.billing import BillingActivities
        from apps.workflows.activities.notifications import (
            NotificationActivities,
            NotificationRequest,
        )

        # Process each tenant asynchronously within the workflow.
        for tenant_id in tenant_ids:
            try:
                # 1. Sync unsynced usage records to Lago.
                sync_result = await workflow.execute_activity(
                    BillingActivities.sync_usage_to_lago,
                    tenant_id,
                    start_time_window,
                    end_time,
                    start_to_close_timeout=timedelta(seconds=60),
                    retry_policy=retry_policy,
                )

                if sync_result.get("success"):
                    tenants_synced += 1
                    records_synced += sync_result.get("synced_count", 0)
                else:
                    errors.append(
                        f"Tenant {tenant_id} Lago sync failed: {sync_result.get('error')}"
                    )

                # 2. Check tenant's usage against defined limits.
                limits_result = await workflow.execute_activity(
                    BillingActivities.check_limits,
                    tenant_id,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )

                # 3. If limits are exceeded, send a notification.
                if limits_result.get("any_exceeded"):
                    await workflow.execute_activity(
                        NotificationActivities.send_notification,
                        NotificationRequest(
                            tenant_id=tenant_id,
                            user_id=None,  # Notification is tenant-wide, not user-specific.
                            notification_type="warning",
                            title="Usage Limit Exceeded",
                            message="Your usage has exceeded plan limits. Please upgrade your plan.",
                            channel="in_app",  # Send as an in-app notification.
                            metadata={"limits": limits_result.get("limits")},
                        ),
                        start_to_close_timeout=timedelta(seconds=30),
                        retry_policy=retry_policy,
                    )

            except Exception as e:
                errors.append(f"Error processing tenant {tenant_id}: {str(e)}")
                workflow.logger.error(f"Failed to sync or check limits for tenant {tenant_id}: {e}")

        duration_ms = (time.time() - start_time) * 1000

        workflow.logger.info(
            f"BillingSyncWorkflow complete: {tenants_synced} tenants processed, "
            f"{records_synced} records synced in {duration_ms:.0f}ms."
        )

        return BillingSyncResult(
            tenants_synced=tenants_synced,
            records_synced=records_synced,
            errors=errors,
            duration_ms=duration_ms,
        )


@workflow.defn(name="GetActiveTenantsWorkflow")
class GetActiveTenantsWorkflow:
    """
    Helper Temporal Workflow to retrieve a list of active tenant IDs.

    **Note:** This workflow's current implementation is a placeholder and
    always returns an empty list. In a production environment, this would
    execute an activity that queries the database for active tenants.
    """

    @workflow.run
    async def run(self) -> list[str]:
        """
        Executes the logic to get active tenant IDs.

        Returns:
            A list of strings, where each string is an active tenant's ID.
        """
        workflow.logger.warning(
            "GetActiveTenantsWorkflow is a stub and currently returns an empty list."
        )
        return []
