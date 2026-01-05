"""
System Cleanup and Maintenance Workflow Activities
==================================================

This module defines a set of Temporal Workflow Activities for various system
maintenance and cleanup tasks. These activities are designed to be executed
periodically within a Temporal workflow to ensure data hygiene, manage resource
lifecycles, and aggregate operational metrics.
"""

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """Represents the structured result of a cleanup operation.

    Attributes:
        operation (str): The name of the cleanup operation performed.
        items_processed (int): The total number of items considered for cleanup.
        items_deleted (int): The number of items actually deleted or terminated.
        errors (list[str]): A list of any errors encountered during the operation.
        duration_ms (float): The time taken to execute the cleanup operation in milliseconds.
    """

    operation: str
    items_processed: int
    items_deleted: int
    errors: list[str]
    duration_ms: float


class CleanupActivities:
    """
    A collection of Temporal Workflow Activities for system maintenance and cleanup tasks.

    These activities are designed to be executed within a Temporal workflow,
    providing robust and fault-tolerant mechanisms for routine system operations.
    """

    @activity.defn(name="cleanup_expired_sessions")
    async def cleanup_expired_sessions(
        self,
        max_session_age_hours: int = 24,
    ) -> CleanupResult:
        """
        Identifies and terminates voice sessions that have exceeded a maximum age.

        This activity targets sessions that are still in 'created' or 'active'
        status but have been open for longer than `max_session_age_hours`.
        It helps prevent stale sessions from consuming resources and
        improves data hygiene.

        Args:
            max_session_age_hours: The maximum number of hours an active
                                   session is allowed to run before being
                                   automatically terminated.

        Returns:
            A `CleanupResult` object detailing the outcome of the operation.
        """
        import time
        from django.utils import timezone
        from apps.sessions.models import Session  # Local import.

        start_time = time.time()
        errors = []
        terminated_count = 0

        try:
            cutoff_time = timezone.now() - timedelta(hours=max_session_age_hours)

            # Find sessions that are either created or active and are older than the cutoff.
            expired_sessions_qs = Session.objects.filter(
                status__in=["created", "active"],
                created_at__lt=cutoff_time,
            )

            total_processed = await expired_sessions_qs.acount()

            # Asynchronously iterate and terminate each expired session.
            async for session in expired_sessions_qs:
                try:
                    session.status = "terminated"
                    session.terminated_at = timezone.now()
                    await session.asave()
                    terminated_count += 1
                    logger.info(
                        f"Terminated expired session {session.id} "
                        f"(created {session.created_at.isoformat()})"
                    )
                except Exception as e:
                    errors.append(f"Error terminating session {session.id}: {e}")
                    logger.error(f"Error terminating expired session {session.id}: {e}")

            duration_ms = (time.time() - start_time) * 1000

            return CleanupResult(
                operation="cleanup_expired_sessions",
                items_processed=total_processed,
                items_deleted=terminated_count,  # Renamed from 'deleted' to 'terminated' for clarity.
                errors=errors,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return CleanupResult(
                operation="cleanup_expired_sessions",
                items_processed=0,
                items_deleted=0,
                errors=[str(e)],
                duration_ms=(time.time() - start_time) * 1000,
            )

    @activity.defn(name="cleanup_old_audit_logs")
    async def cleanup_old_audit_logs(
        self,
        retention_days: int = 90,
        archive: bool = True,
    ) -> CleanupResult:
        """
        Archives audit logs that are older than the specified retention period.

        **Important Note:** Audit logs are immutable and, in this current
        implementation, are **archived to a local file system, but NOT deleted
        from the database**. This local archiving is a placeholder for a more
        robust solution that would typically involve moving data to long-term
        cloud storage (e.g., AWS S3, Google Cloud Storage) and then safely
        deleting it from the active database.

        Args:
            retention_days: The number of days for which audit logs should be retained
                            in the active database. Logs older than this will be archived.
            archive: If True, older logs will be written to a local JSONL file.

        Returns:
            A `CleanupResult` object detailing the outcome of the archiving operation.
        """
        import json
        import time
        from pathlib import Path
        from django.utils import timezone
        from apps.audit.models import AuditLog  # Local import.

        start_time = time.time()
        errors = []
        archived_count = 0

        try:
            cutoff_time = timezone.now() - timedelta(days=retention_days)

            # Identify old logs.
            old_logs_qs = AuditLog.objects.filter(created_at__lt=cutoff_time)
            total_processed = await old_logs_qs.acount()

            if archive and total_processed > 0:
                # Define local archive directory and ensure it exists.
                archive_dir = Path("/app/data/audit_archives")
                archive_dir.mkdir(parents=True, exist_ok=True)

                # Generate a unique archive filename based on the cutoff date.
                archive_file = archive_dir / f"audit_{{cutoff_time.strftime('%Y%m%d_%H%M%S')}}.jsonl"

                # Stream logs to the JSONL archive file.
                async for log in old_logs_qs:
                    try:
                        with open(archive_file, "a") as f:
                            f.write(
                                json.dumps(
                                    {
                                        "id": str(log.id),
                                        "tenant_id": str(log.tenant_id) if log.tenant_id else None,
                                        "actor_id": log.actor_id,
                                        "actor_email": log.actor_email,
                                        "action": log.action,
                                        "resource_type": log.resource_type,
                                        "resource_id": log.resource_id,
                                        "created_at": log.created_at.isoformat(),
                                        "description": log.description,
                                        "old_values": log.old_values,
                                        "new_values": log.new_values,
                                        "metadata": log.metadata,
                                    }
                                )
                                + "\n"
                            )
                        archived_count += 1
                    except Exception as e:
                        errors.append(f"Error archiving log {log.id}: {e}")
                        logger.error(f"Error archiving audit log {log.id}: {e}")

                logger.info(f"Archived {archived_count} audit logs to {archive_file}.")

            duration_ms = (time.time() - start_time) * 1000

            return CleanupResult(
                operation="cleanup_old_audit_logs",
                items_processed=total_processed,
                items_deleted=0,  # Explicitly 0, as this activity only archives, not deletes from DB.
                errors=errors,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Failed to cleanup old audit logs: {e}")
            return CleanupResult(
                operation="cleanup_old_audit_logs",
                items_processed=0,
                items_deleted=0,
                errors=[str(e)],
                duration_ms=(time.time() - start_time) * 1000,
            )

    @activity.defn(name="cleanup_orphaned_files")
    async def cleanup_orphaned_files(
        self,
        media_dir: str = "/app/media",
    ) -> CleanupResult:
        """
        Identifies and removes media files from the file system that are no
        longer referenced by any model in the database (orphaned files).

        **Current Status:** This activity is currently a placeholder and only
        simulates the check. In a production implementation, it would actively
        query the database for all file-referencing fields (`FileField`, `ImageField`)
        across all relevant models and delete unreferenced files.

        Args:
            media_dir: The root path to the media directory to scan.

        Returns:
            A `CleanupResult` object detailing the outcome of the file scan.
        """
        import time
        from pathlib import Path

        start_time = time.time()
        errors = []
        processed_count = 0
        deleted_count = 0

        try:
            media_path = Path(media_dir)
            if not media_path.exists():
                logger.warning("Media directory '%s' does not exist. Skipping orphaned file cleanup.", media_dir)
                return CleanupResult(
                    operation="cleanup_orphaned_files",
                    items_processed=0,
                    items_deleted=0,
                    errors=[f"Media directory '{media_dir}' does not exist"],
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Simulate processing by listing files.
            for file_path in media_path.rglob("*"):
                if file_path.is_file():
                    processed_count += 1
                    logger.debug(f"Simulating check for orphaned file: {file_path}")
                    # Actual implementation would query DB here and delete if unreferenced.
                    # Example: if not is_referenced(file_path): file_path.unlink(); deleted_count += 1

            duration_ms = (time.time() - start_time) * 1000

            return CleanupResult(
                operation="cleanup_orphaned_files",
                items_processed=processed_count,
                items_deleted=deleted_count,
                errors=errors,
                duration_ms=duration_ms,
            )

        except Exception as e:
            logger.error(f"Failed to cleanup orphaned files in '{media_dir}': {e}")
            return CleanupResult(
                operation="cleanup_orphaned_files",
                items_processed=processed_count,
                items_deleted=deleted_count,
                errors=[str(e)],
                duration_ms=(time.time() - start_time) * 1000,
            )

    @activity.defn(name="aggregate_metrics")
    async def aggregate_metrics(
        self,
        tenant_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Aggregates various operational and usage metrics for reporting purposes.

        This activity can aggregate metrics system-wide or for a specific tenant.
        It collects data on sessions, duration, and token usage from the database.

        Args:
            tenant_id: (Optional) The ID of the tenant to aggregate metrics for.
                       If None, aggregates metrics across all tenants.

        Returns:
            A dictionary containing the aggregated metrics.
        """
        import time
        from django.db.models import Avg, Sum
        from django.utils import timezone
        from apps.sessions.models import Session  # Local import.
        from apps.tenants.models import Tenant  # Local import.

        start_time = time.time()

        try:
            now = timezone.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Build base queryset for sessions, filtered by tenant if specified.
            sessions_qs = Session.objects.all()
            if tenant_id:
                sessions_qs = sessions_qs.filter(tenant_id=tenant_id)

            # Perform various aggregations on the session data.
            metrics = {
                "timestamp": now.isoformat(),
                "tenant_id": tenant_id,
                "sessions": {
                    "total": await sessions_qs.acount(),
                    "today": await sessions_qs.filter(created_at__gte=today).acount(),
                    "this_month": await sessions_qs.filter(created_at__gte=this_month).acount(),
                    "active": await sessions_qs.filter(status="active").acount(),
                },
                "duration": {
                    "total_seconds": (await sessions_qs.aaggregate(total=Sum("duration_seconds")))["total"] or 0,
                    "avg_seconds": (await sessions_qs.aaggregate(avg=Avg("duration_seconds")))["avg"] or 0,
                },
                "tokens": {
                    "input_total": (await sessions_qs.aaggregate(total=Sum("input_tokens")))["total"] or 0,
                    "output_total": (await sessions_qs.aaggregate(total=Sum("output_tokens")))["total"] or 0,
                },
            }

            # Add tenant-specific counts if aggregating globally.
            if not tenant_id:
                metrics["tenants"] = {
                    "total": await Tenant.objects.acount(),
                    "active": await Tenant.objects.filter(status="active").acount(),
                }

            duration_ms = (time.time() - start_time) * 1000
            metrics["processing_time_ms"] = duration_ms

            logger.info(f"Aggregated metrics in {duration_ms:.0f}ms.")

            return metrics

        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            return {
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000,
            }