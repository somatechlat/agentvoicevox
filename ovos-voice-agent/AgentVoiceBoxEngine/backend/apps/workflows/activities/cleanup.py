"""
Cleanup activities for Temporal workflows.

Handles cleanup of expired sessions, old data, etc.
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""

    operation: str
    items_processed: int
    items_deleted: int
    errors: List[str]
    duration_ms: float


class CleanupActivities:
    """
    Cleanup activities for maintenance tasks.

    Activities:
    - cleanup_expired_sessions: Terminate expired sessions
    - cleanup_old_audit_logs: Archive old audit logs
    - cleanup_orphaned_files: Remove orphaned media files
    - aggregate_metrics: Aggregate metrics data
    """

    @activity.defn(name="cleanup_expired_sessions")
    async def cleanup_expired_sessions(
        self,
        max_session_age_hours: int = 24,
    ) -> CleanupResult:
        """
        Terminate sessions that have exceeded maximum age.

        Args:
            max_session_age_hours: Maximum session age in hours

        Returns:
            CleanupResult with cleanup statistics
        """
        import time

        start_time = time.time()
        errors = []

        try:
            from apps.sessions.models import Session
            from django.utils import timezone

            cutoff = timezone.now() - timedelta(hours=max_session_age_hours)

            # Find expired active sessions
            expired_sessions = Session.objects.filter(
                status__in=["created", "active"],
                created_at__lt=cutoff,
            )

            count = await expired_sessions.acount()
            terminated = 0

            async for session in expired_sessions:
                try:
                    session.status = "terminated"
                    session.terminated_at = timezone.now()
                    await session.asave()
                    terminated += 1

                    logger.info(
                        f"Terminated expired session {session.id} "
                        f"(created {session.created_at})"
                    )

                except Exception as e:
                    errors.append(f"Session {session.id}: {str(e)}")

            duration = (time.time() - start_time) * 1000

            logger.info(
                f"Cleanup expired sessions: {terminated}/{count} terminated"
            )

            return CleanupResult(
                operation="cleanup_expired_sessions",
                items_processed=count,
                items_deleted=terminated,
                errors=errors,
                duration_ms=duration,
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
        Archive or delete audit logs older than retention period.

        Note: Audit logs are immutable, so we archive rather than delete.

        Args:
            retention_days: Number of days to retain
            archive: Whether to archive before deletion

        Returns:
            CleanupResult with cleanup statistics
        """
        import time

        start_time = time.time()
        errors = []

        try:
            from apps.audit.models import AuditLog
            from django.utils import timezone

            cutoff = timezone.now() - timedelta(days=retention_days)

            # Count old logs
            old_logs = AuditLog.objects.filter(created_at__lt=cutoff)
            count = await old_logs.acount()

            archived = 0

            if archive and count > 0:
                # Export to archive (in production, this would go to S3/GCS)
                import json
                from pathlib import Path

                archive_dir = Path("/app/data/audit_archives")
                archive_dir.mkdir(parents=True, exist_ok=True)

                archive_file = archive_dir / f"audit_{cutoff.strftime('%Y%m%d')}.jsonl"

                async for log in old_logs:
                    try:
                        with open(archive_file, "a") as f:
                            f.write(json.dumps({
                                "id": str(log.id),
                                "tenant_id": str(log.tenant_id),
                                "actor_id": log.actor_id,
                                "actor_email": log.actor_email,
                                "action": log.action,
                                "resource_type": log.resource_type,
                                "resource_id": log.resource_id,
                                "created_at": log.created_at.isoformat(),
                            }) + "\n")
                        archived += 1

                    except Exception as e:
                        errors.append(f"Log {log.id}: {str(e)}")

                logger.info(f"Archived {archived} audit logs to {archive_file}")

            # Note: We don't actually delete audit logs due to immutability
            # In production, archived logs would be moved to cold storage

            duration = (time.time() - start_time) * 1000

            return CleanupResult(
                operation="cleanup_old_audit_logs",
                items_processed=count,
                items_deleted=0,  # Audit logs are never deleted
                errors=errors,
                duration_ms=duration,
            )

        except Exception as e:
            logger.error(f"Failed to cleanup audit logs: {e}")
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
        Remove orphaned media files not referenced by any model.

        Args:
            media_dir: Path to media directory

        Returns:
            CleanupResult with cleanup statistics
        """
        import time
        from pathlib import Path

        start_time = time.time()
        errors = []
        processed = 0
        deleted = 0

        try:
            media_path = Path(media_dir)
            if not media_path.exists():
                return CleanupResult(
                    operation="cleanup_orphaned_files",
                    items_processed=0,
                    items_deleted=0,
                    errors=["Media directory does not exist"],
                    duration_ms=(time.time() - start_time) * 1000,
                )

            # Get all files in media directory
            for file_path in media_path.rglob("*"):
                if file_path.is_file():
                    processed += 1

                    # Check if file is referenced
                    # In production, this would check against database
                    # For now, just log
                    logger.debug(f"Checking file: {file_path}")

            duration = (time.time() - start_time) * 1000

            return CleanupResult(
                operation="cleanup_orphaned_files",
                items_processed=processed,
                items_deleted=deleted,
                errors=errors,
                duration_ms=duration,
            )

        except Exception as e:
            logger.error(f"Failed to cleanup orphaned files: {e}")
            return CleanupResult(
                operation="cleanup_orphaned_files",
                items_processed=0,
                items_deleted=0,
                errors=[str(e)],
                duration_ms=(time.time() - start_time) * 1000,
            )

    @activity.defn(name="aggregate_metrics")
    async def aggregate_metrics(
        self,
        tenant_id: str = None,
    ) -> Dict[str, Any]:
        """
        Aggregate metrics for reporting.

        Args:
            tenant_id: Optional tenant to aggregate for (None = all)

        Returns:
            Dict with aggregated metrics
        """
        import time

        start_time = time.time()

        try:
            from django.db.models import Count, Sum, Avg
            from apps.sessions.models import Session
            from apps.tenants.models import Tenant
            from django.utils import timezone

            now = timezone.now()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Build base queryset
            sessions_qs = Session.objects.all()
            if tenant_id:
                sessions_qs = sessions_qs.filter(tenant_id=tenant_id)

            # Aggregate metrics
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
                    "total_seconds": (await sessions_qs.aaggregate(
                        total=Sum("duration_seconds")
                    ))["total"] or 0,
                    "avg_seconds": (await sessions_qs.aaggregate(
                        avg=Avg("duration_seconds")
                    ))["avg"] or 0,
                },
                "tokens": {
                    "input_total": (await sessions_qs.aaggregate(
                        total=Sum("input_tokens")
                    ))["total"] or 0,
                    "output_total": (await sessions_qs.aaggregate(
                        total=Sum("output_tokens")
                    ))["total"] or 0,
                },
            }

            if not tenant_id:
                metrics["tenants"] = {
                    "total": await Tenant.objects.acount(),
                    "active": await Tenant.objects.filter(status="active").acount(),
                }

            duration = (time.time() - start_time) * 1000
            metrics["processing_time_ms"] = duration

            logger.info(f"Aggregated metrics in {duration:.0f}ms")

            return metrics

        except Exception as e:
            logger.error(f"Failed to aggregate metrics: {e}")
            return {
                "error": str(e),
                "processing_time_ms": (time.time() - start_time) * 1000,
            }
