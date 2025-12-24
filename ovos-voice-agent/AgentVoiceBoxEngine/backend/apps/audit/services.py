"""
Audit logging services.

Business logic for audit log queries and exports.
"""
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from django.db.models import QuerySet
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.tenants.models import Tenant


class AuditLogService:
    """Service for querying audit logs."""

    @staticmethod
    def list_logs(
        tenant: Tenant,
        actor_id: Optional[str] = None,
        actor_type: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """
        List audit logs with filtering and pagination.

        Returns tuple of (logs, total_count).
        """
        qs = AuditLog.objects.filter(tenant=tenant)

        if actor_id:
            qs = qs.filter(actor_id=actor_id)
        if actor_type:
            qs = qs.filter(actor_type=actor_type)
        if action:
            qs = qs.filter(action=action)
        if resource_type:
            qs = qs.filter(resource_type=resource_type)
        if resource_id:
            qs = qs.filter(resource_id=resource_id)
        if start_date:
            qs = qs.filter(created_at__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__lte=end_date)

        total = qs.count()
        offset = (page - 1) * page_size
        logs = list(qs.order_by("-created_at")[offset : offset + page_size])

        return logs, total

    @staticmethod
    def get_log(log_id: UUID) -> Optional[AuditLog]:
        """Get an audit log by ID."""
        try:
            return AuditLog.objects.get(id=log_id)
        except AuditLog.DoesNotExist:
            return None

    @staticmethod
    def get_resource_history(
        tenant: Tenant,
        resource_type: str,
        resource_id: str,
    ) -> list[AuditLog]:
        """Get audit history for a specific resource."""
        return list(
            AuditLog.objects.filter(
                tenant=tenant,
                resource_type=resource_type,
                resource_id=resource_id,
            ).order_by("-created_at")[:100]
        )

    @staticmethod
    def get_user_activity(
        tenant: Tenant,
        actor_id: str,
        days: int = 30,
    ) -> list[AuditLog]:
        """Get recent activity for a user."""
        since = timezone.now() - timedelta(days=days)
        return list(
            AuditLog.objects.filter(
                tenant=tenant,
                actor_id=actor_id,
                created_at__gte=since,
            ).order_by("-created_at")[:100]
        )

    @staticmethod
    def get_available_actions(tenant: Tenant) -> list[str]:
        """Get list of actions that have been logged for a tenant."""
        return list(
            AuditLog.objects.filter(tenant=tenant)
            .values_list("action", flat=True)
            .distinct()
        )

    @staticmethod
    def get_available_resource_types(tenant: Tenant) -> list[str]:
        """Get list of resource types that have been logged for a tenant."""
        return list(
            AuditLog.objects.filter(tenant=tenant)
            .values_list("resource_type", flat=True)
            .distinct()
        )

    @staticmethod
    def export_csv(
        tenant: Tenant,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """Export audit logs to CSV format."""
        qs = AuditLog.objects.filter(tenant=tenant)

        if start_date:
            qs = qs.filter(created_at__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__lte=end_date)

        lines = [
            "timestamp,actor_id,actor_email,actor_type,action,resource_type,resource_id,description,ip_address,request_id"
        ]

        for log in qs.order_by("-created_at").iterator():
            description = log.description.replace('"', '""')
            line = ",".join(
                [
                    log.created_at.isoformat(),
                    str(log.actor_id),
                    str(log.actor_email or ""),
                    str(log.actor_type),
                    str(log.action),
                    str(log.resource_type),
                    str(log.resource_id or ""),
                    f'"{description}"',
                    str(log.ip_address or ""),
                    str(log.request_id or ""),
                ]
            )
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def cleanup_old_logs(retention_days: int = 90) -> int:
        """
        Delete audit logs older than retention period.

        Returns count of deleted logs.
        Note: This bypasses the model's delete() override.
        """
        cutoff = timezone.now() - timedelta(days=retention_days)
        # Use raw delete to bypass model override
        deleted, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
        return deleted
