"""
Pydantic schemas for audit log API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ninja import Schema


class AuditLogOut(Schema):
    """Schema for audit log response."""

    id: UUID
    created_at: datetime
    actor_id: str
    actor_email: str
    actor_type: str
    tenant_id: Optional[UUID] = None
    ip_address: Optional[str] = None
    user_agent: str
    request_id: str
    action: str
    resource_type: str
    resource_id: str
    description: str
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    metadata: Dict[str, Any]


class AuditLogListOut(Schema):
    """Schema for paginated audit log list."""

    items: List[AuditLogOut]
    total: int
    page: int
    page_size: int


class AuditLogStatsOut(Schema):
    """Schema for audit log statistics."""

    total_logs: int
    actions_count: Dict[str, int]
    resource_types_count: Dict[str, int]
    actors_count: int
