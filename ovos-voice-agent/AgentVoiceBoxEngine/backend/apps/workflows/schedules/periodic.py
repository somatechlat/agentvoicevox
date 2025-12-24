"""
Periodic workflow schedules for Temporal.

Defines schedules for:
- Cleanup (hourly)
- Billing sync (every 15 minutes)
- Metrics aggregation (every 5 minutes)
"""
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List


@dataclass
class WorkflowSchedule:
    """Definition of a scheduled workflow."""

    schedule_id: str
    workflow_type: str
    workflow_id_prefix: str
    task_queue: str
    interval: timedelta
    args: List[Any]
    description: str


# Cleanup workflow - runs hourly
CLEANUP_SCHEDULE = WorkflowSchedule(
    schedule_id="cleanup-expired-sessions",
    workflow_type="CleanupWorkflow",
    workflow_id_prefix="cleanup",
    task_queue="default",
    interval=timedelta(hours=1),
    args=[{
        "cleanup_sessions": True,
        "cleanup_audit_logs": True,
        "cleanup_files": True,
        "aggregate_metrics": False,  # Handled by separate schedule
        "session_max_age_hours": 24,
        "audit_retention_days": 90,
    }],
    description="Cleanup expired sessions and archive old audit logs",
)


# Billing sync workflow - runs every 15 minutes
BILLING_SYNC_SCHEDULE = WorkflowSchedule(
    schedule_id="billing-sync",
    workflow_type="BillingSyncWorkflow",
    workflow_id_prefix="billing-sync",
    task_queue="billing",
    interval=timedelta(minutes=15),
    args=[{
        "tenant_id": None,  # All tenants
        "sync_window_minutes": 15,
    }],
    description="Sync usage to Lago billing system",
)


# Metrics aggregation workflow - runs every 5 minutes
METRICS_AGGREGATION_SCHEDULE = WorkflowSchedule(
    schedule_id="metrics-aggregation",
    workflow_type="MetricsAggregationWorkflow",
    workflow_id_prefix="metrics",
    task_queue="default",
    interval=timedelta(minutes=5),
    args=[None],  # All tenants
    description="Aggregate metrics for dashboards",
)


def get_all_schedules() -> List[WorkflowSchedule]:
    """Get all defined workflow schedules."""
    return [
        CLEANUP_SCHEDULE,
        BILLING_SYNC_SCHEDULE,
        METRICS_AGGREGATION_SCHEDULE,
    ]


async def create_schedules(client) -> Dict[str, Any]:
    """
    Create all workflow schedules in Temporal.

    Args:
        client: Temporal client

    Returns:
        Dict with schedule creation results
    """
    from temporalio.client import (
        Schedule,
        ScheduleActionStartWorkflow,
        ScheduleIntervalSpec,
        ScheduleSpec,
        ScheduleState,
    )

    results = {}

    for schedule in get_all_schedules():
        try:
            # Check if schedule exists
            try:
                existing = await client.get_schedule_handle(schedule.schedule_id)
                await existing.describe()
                results[schedule.schedule_id] = {
                    "status": "exists",
                    "description": schedule.description,
                }
                continue
            except Exception:
                pass  # Schedule doesn't exist, create it

            # Create schedule
            await client.create_schedule(
                schedule.schedule_id,
                Schedule(
                    action=ScheduleActionStartWorkflow(
                        schedule.workflow_type,
                        *schedule.args,
                        id=f"{schedule.workflow_id_prefix}-{{{{.ScheduleTime.Format \"20060102-150405\"}}}}",
                        task_queue=schedule.task_queue,
                    ),
                    spec=ScheduleSpec(
                        intervals=[
                            ScheduleIntervalSpec(every=schedule.interval),
                        ],
                    ),
                    state=ScheduleState(
                        note=schedule.description,
                    ),
                ),
            )

            results[schedule.schedule_id] = {
                "status": "created",
                "description": schedule.description,
                "interval": str(schedule.interval),
            }

        except Exception as e:
            results[schedule.schedule_id] = {
                "status": "error",
                "error": str(e),
            }

    return results


async def delete_schedules(client) -> Dict[str, Any]:
    """
    Delete all workflow schedules from Temporal.

    Args:
        client: Temporal client

    Returns:
        Dict with schedule deletion results
    """
    results = {}

    for schedule in get_all_schedules():
        try:
            handle = await client.get_schedule_handle(schedule.schedule_id)
            await handle.delete()
            results[schedule.schedule_id] = {"status": "deleted"}

        except Exception as e:
            results[schedule.schedule_id] = {
                "status": "error",
                "error": str(e),
            }

    return results
