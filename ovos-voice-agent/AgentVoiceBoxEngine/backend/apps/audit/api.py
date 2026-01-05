"""
Audit Log Viewing and Export API Endpoints
==========================================

This module provides API endpoints for viewing and exporting audit logs.
Due to the immutable nature of audit logs, there are no endpoints for
creating, updating, or deleting individual log entries via the API.

**Security Note:** Access to these endpoints typically requires a high level
of privilege (e.g., OPERATOR or ADMIN role). The current implementation relies
on implicit tenant-scoping through `AuditLog.objects` but **lacks explicit
permission checks for user roles on individual endpoints**. This should be
addressed for production security.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from django.http import HttpResponse
from ninja import Query, Router

from apps.core.exceptions import (
    NotFoundError,
    PermissionDeniedError,
)  # PermissionDeniedError added for documentation purposes

from .schemas import (
    AuditLogListOut,
    AuditLogOut,
)
from .services import AuditLogService

# Router for audit log endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Audit Logs"])


def _log_to_out(log) -> AuditLogOut:
    """
    Serializes an `AuditLog` model instance into an `AuditLogOut` schema.

    Args:
        log: The `AuditLog` model instance.

    Returns:
        An `AuditLogOut` object populated with the log data.
    """
    return AuditLogOut(
        id=log.id,
        created_at=log.created_at,
        actor_id=log.actor_id,
        actor_email=log.actor_email,
        actor_type=log.actor_type,
        tenant_id=log.tenant_id,
        ip_address=log.ip_address,
        user_agent=log.user_agent,
        request_id=log.request_id,
        action=log.action,
        resource_type=log.resource_type,
        resource_id=log.resource_id,
        description=log.description,
        old_values=log.old_values,
        new_values=log.new_values,
        metadata=log.metadata,
    )


@router.get("", response=AuditLogListOut, summary="List Audit Logs")
def list_audit_logs(
    request,
    actor_id: Optional[str] = Query(
        None, description="Filter by actor ID (user ID, API key ID, or 'system')."
    ),
    actor_type: Optional[str] = Query(
        None, description="Filter by actor type ('user', 'api_key', 'system')."
    ),
    action: Optional[str] = Query(
        None, description="Filter by action performed (e.g., 'create', 'login')."
    ),
    resource_type: Optional[str] = Query(
        None, description="Filter by resource type (e.g., 'Project', 'User')."
    ),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID."),
    start_date: Optional[datetime] = Query(
        None, description="Filter logs created on or after this datetime (ISO 8601)."
    ),
    end_date: Optional[datetime] = Query(
        None, description="Filter logs created on or before this datetime (ISO 8601)."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """
    Retrieves a paginated list of audit logs for the current tenant.

    This endpoint allows extensive filtering to pinpoint specific audit trails.

    **Permissions:** Assumed to require OPERATOR role or higher (explicit check missing).
    """
    # Assuming request.tenant is correctly set by middleware
    tenant = request.tenant
    # TODO: Implement explicit permission check (e.g., if not request.user.is_operator: raise PermissionDeniedError)
    logs, total = AuditLogService.list_logs(
        tenant=tenant,
        actor_id=actor_id,
        actor_type=actor_type,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    return AuditLogListOut(
        items=[_log_to_out(log) for log in logs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/actions", response=list[str], summary="List Available Audit Actions")
def list_actions(request):
    """
    Retrieves a list of all distinct audit action types that have been logged for the current tenant.

    This is useful for populating filter options in user interfaces.

    **Permissions:** Assumed to require OPERATOR role or higher (explicit check missing).
    """
    tenant = request.tenant
    # TODO: Implement explicit permission check
    return AuditLogService.get_available_actions(tenant)


@router.get("/resource-types", response=list[str], summary="List Available Audit Resource Types")
def list_resource_types(request):
    """
    Retrieves a list of all distinct resource types that have been logged for the current tenant.

    This is useful for populating filter options in user interfaces.

    **Permissions:** Assumed to require OPERATOR role or higher (explicit check missing).
    """
    tenant = request.tenant
    # TODO: Implement explicit permission check
    return AuditLogService.get_available_resource_types(tenant)


@router.get("/export", summary="Export Audit Logs to CSV")
def export_audit_logs(
    request,
    start_date: Optional[datetime] = Query(
        None, description="Export logs created on or after this datetime (ISO 8601)."
    ),
    end_date: Optional[datetime] = Query(
        None, description="Export logs created on or before this datetime (ISO 8601)."
    ),
):
    """
    Exports audit log entries for the current tenant to a CSV file.

    This endpoint generates a downloadable CSV containing a subset of audit log fields,
    suitable for offline analysis.

    **Permissions:** Assumed to require ADMIN role or higher (explicit check missing).
    """
    tenant = request.tenant
    # TODO: Implement explicit permission check (e.g., if not request.user.is_admin: raise PermissionDeniedError)
    csv_content = AuditLogService.export_csv(
        tenant=tenant,
        start_date=start_date,
        end_date=end_date,
    )

    response = HttpResponse(csv_content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
    return response


@router.get(
    "/resource/{resource_type}/{resource_id}",
    response=list[AuditLogOut],
    summary="Get Audit History for a Resource",
)
def get_resource_logs(request, resource_type: str, resource_id: str):
    """
    Retrieves the audit trail for a specific resource within the current tenant.

    **Permissions:** Assumed to require OPERATOR role or higher (explicit check missing).
    """
    tenant = request.tenant
    # TODO: Implement explicit permission check
    logs = AuditLogService.get_resource_history(tenant, resource_type, resource_id)
    return [_log_to_out(log) for log in logs]


@router.get("/actor/{actor_id}", response=list[AuditLogOut], summary="Get Audit Logs for an Actor")
def get_actor_logs(
    request,
    actor_id: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to retrieve past activity."),
):
    """
    Retrieves recent audit logs for a specific actor (user or API key) within the current tenant.

    **Permissions:** Assumed to require OPERATOR role or higher (explicit check missing).
    """
    tenant = request.tenant
    # TODO: Implement explicit permission check
    logs = AuditLogService.get_user_activity(tenant, actor_id, days)
    return [_log_to_out(log) for log in logs]


@router.get("/{log_id}", response=AuditLogOut, summary="Get a Specific Audit Log by ID")
def get_audit_log(request, log_id: UUID):
    """
    Retrieves a single, specific audit log entry by its unique ID.

    **Permissions:** Assumed to require OPERATOR role or higher (explicit check missing).
    """
    # Assuming request.tenant is correctly set by middleware
    # TODO: Implement explicit permission check
    log = AuditLogService.get_log(log_id)
    if not log or (
        log.tenant and log.tenant != request.tenant
    ):  # Ensure log belongs to current tenant if not sysadmin
        raise NotFoundError(f"Audit log {log_id} not found")
    return _log_to_out(log)
