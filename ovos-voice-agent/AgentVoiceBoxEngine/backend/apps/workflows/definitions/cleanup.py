"""
Cleanup workflow for maintenance tasks.

Runs periodically to clean up expired sessions, old data, etc.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List

from temporalio import workflow
from temporalio.common import RetryPolicy

logger = logging.getLogger(__name__)


@dataclass
class CleanupInput:
    """Input for cleanup workflow."""

    cleanup_sessions: bool = True
    cleanup_audit_logs: bool = True
    cleanup_files: bool = True
    aggregate_metrics: bool = True
    session_max_age_hours: int = 24
    audit_retention_days: int = 90


@dataclass
class CleanupWorkflowResult:
    """Result of cleanup workflow."""

    sessions_terminated: int
    audit_logs_archived: int
    files_deleted: int
    metrics_aggregated: bool
    errors: List[str]
    duration_ms: float


@workflow.defn(name="CleanupWorkflow")
class CleanupWorkflow:
    """
    Workflow for periodic cleanup and maintenance tasks.

    Runs hourly to:
    - Terminate expired sessions (>24 hours)
    - Archive old audit logs (>90 days)
    - Remove orphaned files
    - Aggregate metrics
    """

    @workflow.run
    async def run(self, input: CleanupInput) -> CleanupWorkflowResult:
        """
        Run the cleanup workflow.

        Args:
            input: CleanupInput with cleanup configuration

        Returns:
            CleanupWorkflowResult with cleanup statistics
        """
        import time

        start_time = time.time()
        errors = []
        sessions_terminated = 0
        audit_logs_archived = 0
        files_deleted = 0
        metrics_aggregated = False

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=60),
            maximum_attempts=3,
        )

        workflow.logger.info("Starting cleanup workflow")

        from apps.workflows.activities.cleanup import CleanupActivities

        # 1. Cleanup expired sessions
        if input.cleanup_sessions:
            try:
                result = await workflow.execute_activity(
                    CleanupActivities.cleanup_expired_sessions,
                    input.session_max_age_hours,
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                sessions_terminated = result.items_deleted
                errors.extend(result.errors)

            except Exception as e:
                errors.append(f"Session cleanup: {str(e)}")
                workflow.logger.error(f"Session cleanup failed: {e}")

        # 2. Archive old audit logs
        if input.cleanup_audit_logs:
            try:
                result = await workflow.execute_activity(
                    CleanupActivities.cleanup_old_audit_logs,
                    input.audit_retention_days,
                    True,  # archive
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=retry_policy,
                )
                audit_logs_archived = result.items_processed
                errors.extend(result.errors)

            except Exception as e:
                errors.append(f"Audit log cleanup: {str(e)}")
                workflow.logger.error(f"Audit log cleanup failed: {e}")

        # 3. Cleanup orphaned files
        if input.cleanup_files:
            try:
                result = await workflow.execute_activity(
                    CleanupActivities.cleanup_orphaned_files,
                    "/app/media",
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                files_deleted = result.items_deleted
                errors.extend(result.errors)

            except Exception as e:
                errors.append(f"File cleanup: {str(e)}")
                workflow.logger.error(f"File cleanup failed: {e}")

        # 4. Aggregate metrics
        if input.aggregate_metrics:
            try:
                await workflow.execute_activity(
                    CleanupActivities.aggregate_metrics,
                    None,  # All tenants
                    start_to_close_timeout=timedelta(minutes=5),
                    retry_policy=retry_policy,
                )
                metrics_aggregated = True

            except Exception as e:
                errors.append(f"Metrics aggregation: {str(e)}")
                workflow.logger.error(f"Metrics aggregation failed: {e}")

        duration = (time.time() - start_time) * 1000

        workflow.logger.info(
            f"Cleanup complete: {sessions_terminated} sessions, "
            f"{audit_logs_archived} audit logs, {files_deleted} files "
            f"in {duration:.0f}ms"
        )

        return CleanupWorkflowResult(
            sessions_terminated=sessions_terminated,
            audit_logs_archived=audit_logs_archived,
            files_deleted=files_deleted,
            metrics_aggregated=metrics_aggregated,
            errors=errors,
            duration_ms=duration,
        )


@workflow.defn(name="MetricsAggregationWorkflow")
class MetricsAggregationWorkflow:
    """
    Workflow for aggregating metrics.

    Runs every 5 minutes to aggregate metrics for dashboards.
    """

    @workflow.run
    async def run(self, tenant_id: str = None) -> Dict[str, Any]:
        """
        Run metrics aggregation.

        Args:
            tenant_id: Optional tenant to aggregate for

        Returns:
            Dict with aggregated metrics
        """
        from apps.workflows.activities.cleanup import CleanupActivities

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(seconds=30),
            maximum_attempts=3,
        )

        result = await workflow.execute_activity(
            CleanupActivities.aggregate_metrics,
            tenant_id,
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry_policy,
        )

        return result
