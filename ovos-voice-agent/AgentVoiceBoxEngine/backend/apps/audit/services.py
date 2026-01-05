"""
Audit Log Service Layer
=======================

This module contains the business logic for querying, filtering, and managing
audit log entries. It provides methods to retrieve specific logs, historical
activity for resources or users, and functionality for exporting and cleaning
up old log data.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from django.utils import timezone

from apps.audit.models import AuditLog
from apps.tenants.models import Tenant


class AuditLogService:
    """A service class encapsulating all business logic for AuditLog operations."""

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
        Retrieves a paginated list of audit logs for a specific tenant, with extensive filtering options.

        Args:
            tenant: The Tenant for which to list audit logs.
            actor_id: (Optional) Filter logs by the ID of the actor (user, API key, or 'system').
            actor_type: (Optional) Filter logs by the type of actor.
            action: (Optional) Filter logs by the action performed (e.g., 'create', 'login').
            resource_type: (Optional) Filter logs by the type of resource affected (e.g., 'Project', 'User').
            resource_id: (Optional) Filter logs by the ID of the specific resource affected.
            start_date: (Optional) Filter logs created on or after this datetime.
            end_date: (Optional) Filter logs created on or before this datetime.
            page: The page number for pagination.
            page_size: The number of items per page.

        Returns:
            A tuple containing:
            - A list of `AuditLog` instances for the requested page.
            - An integer representing the total count of logs matching the filters.
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
        """
        Retrieves a single audit log entry by its primary key (ID).

        Args:
            log_id: The UUID of the audit log entry to retrieve.

        Returns:
            The `AuditLog` instance if found, otherwise None.
        """
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
        """
        Retrieves the audit history for a specific resource within a tenant.

        Returns up to the 100 most recent logs related to the resource.

        Args:
            tenant: The Tenant associated with the resource.
            resource_type: The type of resource (e.g., 'Project', 'User').
            resource_id: The ID of the specific resource.

        Returns:
            A list of `AuditLog` instances, ordered by most recent first.
        """
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
        """
        Retrieves recent audit activity for a specific user (actor_id) within a tenant.

        Returns up to the 100 most recent logs.

        Args:
            tenant: The Tenant associated with the user.
            actor_id: The ID of the user (actor) whose activity to retrieve.
            days: The number of days back to search for activity.

        Returns:
            A list of `AuditLog` instances, ordered by most recent first.
        """
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
        """
        Retrieves a list of all distinct action types that have been logged for a tenant.

        This is useful for populating filter options in a UI.

        Args:
            tenant: The Tenant for which to get actions.

        Returns:
            A list of unique action strings.
        """
        return list(
            AuditLog.objects.filter(tenant=tenant).values_list("action", flat=True).distinct()
        )

    @staticmethod
    def get_available_resource_types(tenant: Tenant) -> list[str]:
        """
        Retrieves a list of all distinct resource types that have been logged for a tenant.

        This is useful for populating filter options in a UI.

        Args:
            tenant: The Tenant for which to get resource types.

        Returns:
            A list of unique resource type strings.
        """
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
        """
        Exports audit log entries for a tenant to a CSV formatted string.

        The export includes key audit fields for analysis. `old_values` and `new_values`
        are not included in the CSV due to their JSON structure complexity.

        Args:
            tenant: The Tenant whose audit logs are to be exported.
            start_date: (Optional) Include logs created on or after this datetime.
            end_date: (Optional) Include logs created on or before this datetime.

        Returns:
            A string containing the audit logs in CSV format.
        """
        qs = AuditLog.objects.filter(tenant=tenant)

        if start_date:
            qs = qs.filter(created_at__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__lte=end_date)

        # Define CSV header.
        lines = [
            "timestamp,actor_id,actor_email,actor_type,action,resource_type,resource_id,description,ip_address,request_id"
        ]

        # Iterate over logs and format into CSV rows.
        # .iterator() is used for memory efficiency with potentially large querysets.
        for log in qs.order_by("-created_at").iterator():
            # Escape double quotes within description to prevent CSV parsing issues.
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
                    f'"{description}"',  # Enclose description in quotes.
                    str(log.ip_address or ""),
                    str(log.request_id or ""),
                ]
            )
            lines.append(line)

        return "\n".join(lines)

    @staticmethod
    def cleanup_old_logs(retention_days: int = 90) -> int:
        """
        Deletes audit logs older than a specified retention period.

        This method is crucial for data hygiene and compliance. It explicitly
        bypasses the `AuditLog` model's `delete()` override to ensure logs
        can be removed from the database.

        Args:
            retention_days: The number of days for which logs should be retained.
                            Logs older than this period will be deleted.

        Returns:
            The number of `AuditLog` entries that were deleted.
        """
        cutoff = timezone.now() - timedelta(days=retention_days)
        # Use the queryset's `delete()` method directly to bypass the model's
        # overridden `delete()` method which prevents deletion.
        deleted_count, _ = AuditLog.objects.filter(created_at__lt=cutoff).delete()
        return deleted_count
