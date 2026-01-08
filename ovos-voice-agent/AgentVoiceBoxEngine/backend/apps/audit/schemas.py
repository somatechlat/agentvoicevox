"""
Pydantic Schemas for the Audit Log API
=======================================

This module defines the Pydantic schemas for data validation and serialization
in the Audit Log API endpoints. These schemas represent the structure of
individual audit log entries and aggregated audit statistics returned by the API.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from ninja import Schema


class AuditLogOut(Schema):
    """
    Defines the response structure for a single audit log entry.
    This schema provides a detailed, immutable record of a system action.
    """

    id: UUID  # The unique identifier for this audit log entry.
    created_at: datetime  # The UTC timestamp when the auditable action occurred.
    actor_id: str  # The ID of the entity that performed the action (User ID, API Key ID, or 'system').
    actor_email: str  # The email address of the actor, if available.
    actor_type: str  # The type of entity that performed the action (e.g., 'user', 'api_key', 'system').
    tenant_id: Optional[UUID] = (
        None  # The ID of the tenant associated with the action, if any.
    )
    ip_address: Optional[str] = (
        None  # The IP address from which the request originated.
    )
    user_agent: str  # The User-Agent string of the client.
    request_id: str  # A correlation ID for the request.
    action: str  # The specific action performed (e.g., 'create', 'login').
    resource_type: str  # The type of resource affected (e.g., 'Project', 'User').
    resource_id: str  # The ID of the specific resource affected.
    description: str  # A human-readable summary of the action.
    old_values: dict[str, Any]  # A JSON object containing values before an update.
    new_values: dict[
        str, Any
    ]  # A JSON object containing values after a create or update.
    metadata: dict[str, Any]  # Additional contextual data related to the event.


class AuditLogListOut(Schema):
    """
    Defines the response structure for a paginated list of audit log entries.
    """

    items: list[AuditLogOut]  # The list of audit log entries on the current page.
    total: int  # The total number of audit log entries matching the query.
    page: int  # The current page number.
    page_size: int  # The number of items per page.


class AuditLogStatsOut(Schema):
    """
    Defines the response structure for aggregated audit log statistics.
    """

    total_logs: int  # The total number of audit logs in the aggregated set.
    actions_count: dict[str, int]  # A dictionary mapping each action type to its count.
    resource_types_count: dict[
        str, int
    ]  # A dictionary mapping each resource type to its count.
    actors_count: int  # The total number of distinct actors found in the logs.
