"""
Audit log API endpoints.

Provides REST API for audit log viewing and export.
Audit logs are immutable - no create/update/delete endpoints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from django.http import HttpResponse
from ninja import Query, Router

from apps.core.exceptions import NotFoundError

from .schemas import (
    AuditLogListOut,
    AuditLogOut,
)
from .services import AuditLogService

router = Router()


def _log_to_out(log) -> AuditLogOut:
    """Convert AuditLog model to output schema."""
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


@router.get("", response=AuditLogListOut)
def list_audit_logs(
    request,
    actor_id: Optional[str] = Query(None),
    actor_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
):
    """List audit logs with filtering and pagination."""
    tenant = request.tenant
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


@router.get("/actions", response=List[str])
def list_actions(request):
    """List available audit action types for this tenant."""
    tenant = request.tenant
    return AuditLogService.get_available_actions(tenant)


@router.get("/resource-types", response=List[str])
def list_resource_types(request):
    """List available resource types for this tenant."""
    tenant = request.tenant
    return AuditLogService.get_available_resource_types(tenant)


@router.get("/export")
def export_audit_logs(
    request,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
):
    """Export audit logs to CSV."""
    tenant = request.tenant
    csv_content = AuditLogService.export_csv(
        tenant=tenant,
        start_date=start_date,
        end_date=end_date,
    )

    response = HttpResponse(csv_content, content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="audit_logs.csv"'
    return response


@router.get("/resource/{resource_type}/{resource_id}", response=List[AuditLogOut])
def get_resource_logs(request, resource_type: str, resource_id: str):
    """Get audit logs for a specific resource."""
    tenant = request.tenant
    logs = AuditLogService.get_resource_history(tenant, resource_type, resource_id)
    return [_log_to_out(log) for log in logs]


@router.get("/actor/{actor_id}", response=List[AuditLogOut])
def get_actor_logs(request, actor_id: str, days: int = Query(30, ge=1, le=365)):
    """Get audit logs for a specific actor."""
    tenant = request.tenant
    logs = AuditLogService.get_user_activity(tenant, actor_id, days)
    return [_log_to_out(log) for log in logs]


@router.get("/{log_id}", response=AuditLogOut)
def get_audit_log(request, log_id: UUID):
    """Get a specific audit log by ID."""
    log = AuditLogService.get_log(log_id)
    if not log:
        raise NotFoundError(f"Audit log {log_id} not found")
    return _log_to_out(log)
