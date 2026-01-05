"""
Session Management API Endpoints
================================

This module provides the tenant-scoped API endpoints for managing voice
interaction sessions. It includes functionality for listing, retrieving,
creating, and transitioning the state of sessions (e.g., start, complete, terminate).
Endpoints for retrieving session events and aggregated statistics are also provided.
"""

from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError
from apps.core.middleware.tenant import get_current_tenant

from .schemas import (
    SessionCreate,
    SessionEventResponse,
    SessionEventsResponse,
    SessionListResponse,
    SessionResponse,
    SessionStats,
    SessionTerminate,
)
from .services import SessionService

# Router for session management endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Sessions"])


@router.get("", response=SessionListResponse, summary="List Sessions in Tenant")
def list_sessions(
    request,
    project_id: Optional[UUID] = Query(
        None, description="Filter sessions by a specific project ID."
    ),
    status: Optional[str] = Query(
        None, description="Filter sessions by their status (e.g., 'active', 'completed')."
    ),
    api_key_id: Optional[UUID] = Query(None, description="Filter sessions by the API key used."),
    from_date: Optional[str] = Query(
        None, description="Filter sessions created on or after this date (ISO 8601 format)."
    ),
    to_date: Optional[str] = Query(
        None, description="Filter sessions created on or before this date (ISO 8601 format)."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lists all sessions within the current user's tenant, with filtering and pagination.

    **Permissions:** Requires OPERATOR role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_operator:
        raise PermissionDeniedError("Operator role or higher required to list sessions.")

    sessions, total = SessionService.list_sessions(
        tenant=tenant,
        project_id=project_id,
        status=status,
        api_key_id=api_key_id,
        from_date=from_date,
        to_date=to_date,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return SessionListResponse(
        items=[SessionResponse.from_orm(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/stats", response=SessionStats, summary="Get Session Statistics")
def get_session_stats(
    request,
    project_id: Optional[UUID] = Query(
        None, description="Filter statistics for a specific project."
    ),
    from_date: Optional[str] = Query(
        None, description="Include sessions created on or after this date (ISO 8601 format)."
    ),
    to_date: Optional[str] = Query(
        None, description="Include sessions created on or before this date (ISO 8601 format)."
    ),
):
    """
    Retrieves aggregated statistics for sessions within the current tenant.

    This endpoint provides insights into session usage, duration, token consumption,
    and status breakdowns, with optional filtering by project and date range.

    **Permissions:** Requires OPERATOR role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_operator:
        raise PermissionDeniedError("Operator role or higher required to view session statistics.")

    stats = SessionService.get_stats(
        tenant=tenant,
        project_id=project_id,
        from_date=from_date,
        to_date=to_date,
    )

    return SessionStats(**stats)


@router.get("/{session_id}", response=SessionResponse, summary="Get a Session by ID")
def get_session(request, session_id: UUID):
    """
    Retrieves details for a specific session by its ID.

    The session must belong to the current user's tenant.

    **Permissions:** Requires OPERATOR role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_operator:
        raise PermissionDeniedError("Operator role or higher required to view sessions.")

    session = SessionService.get_by_id(session_id)

    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant.")

    return SessionResponse.from_orm(session)


@router.get("/{session_id}/events", response=SessionEventsResponse, summary="Get Session Events")
def get_session_events(
    request,
    session_id: UUID,
    event_type: Optional[str] = Query(None, description="Filter events by a specific type."),
):
    """
    Retrieves all logged events for a specific session.

    The session must belong to the current user's tenant.

    **Permissions:** Requires OPERATOR role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_operator:
        raise PermissionDeniedError("Operator role or higher required to view session events.")

    session = SessionService.get_by_id(session_id)
    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant.")

    events, total = SessionService.get_events(session_id, event_type)

    return SessionEventsResponse(
        items=[SessionEventResponse.from_orm(e) for e in events],
        total=total,
    )


@router.post("", response=SessionResponse, summary="Create a New Session")
def create_session(request, payload: SessionCreate):
    """
    Initiates a new voice interaction session.

    The session can be created either with API key authentication or user authentication.
    If created via user authentication, the user must have at least DEVELOPER role.

    **Permissions:** Requires valid API key OR DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    # Determine authentication context and check permissions.
    api_key = getattr(request, "api_key", None)
    if not api_key and not user.is_developer:
        raise PermissionDeniedError("Developer role or valid API key required to create sessions.")

    # Populate client information from the request.
    client_ip = request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    session = SessionService.create_session(
        tenant=tenant,
        project_id=payload.project_id,
        api_key=api_key,
        # If API key is used, the user is typically not directly associated with the session.
        user=user if not api_key else None,
        config=payload.config,
        metadata=payload.metadata,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    return SessionResponse.from_orm(session)


@router.post("/{session_id}/start", response=SessionResponse, summary="Start a Session")
def start_session(request, session_id: UUID):
    """
    Transitions a session from 'CREATED' to 'ACTIVE' status.

    The session must belong to the current user's tenant.

    **Permissions:** Requires valid API key OR DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    api_key = getattr(request, "api_key", None)
    if not api_key and not user.is_developer:
        raise PermissionDeniedError("Developer role or valid API key required to start sessions.")

    session = SessionService.get_by_id(session_id)
    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant.")

    started_session = SessionService.start_session(session_id)
    return SessionResponse.from_orm(started_session)


@router.post("/{session_id}/complete", response=SessionResponse, summary="Complete a Session")
def complete_session(request, session_id: UUID):
    """
    Marks a session as 'COMPLETED' (normal termination).

    The session must belong to the current user's tenant.

    **Permissions:** Requires valid API key OR DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    api_key = getattr(request, "api_key", None)
    if not api_key and not user.is_developer:
        raise PermissionDeniedError(
            "Developer role or valid API key required to complete sessions."
        )

    session = SessionService.get_by_id(session_id)
    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant.")

    completed_session = SessionService.complete_session(session_id)
    return SessionResponse.from_orm(completed_session)


@router.post("/{session_id}/terminate", response=SessionResponse, summary="Terminate a Session")
def terminate_session(request, session_id: UUID, payload: Optional[SessionTerminate] = None):
    """
    Transitions a session to 'TERMINATED' status (abnormal termination).

    Allows for an optional reason to be provided for the termination.
    The session must belong to the current user's tenant.

    **Permissions:** Requires OPERATOR role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    api_key = getattr(request, "api_key", None)
    # Operator role can terminate, or if API key is used, Developer+ can terminate.
    if not api_key and not user.is_operator:
        raise PermissionDeniedError("Operator role or higher required to terminate sessions.")

    session = SessionService.get_by_id(session_id)
    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant.")

    reason = payload.reason if payload else ""
    terminated_session = SessionService.terminate_session(session_id, reason)
    return SessionResponse.from_orm(terminated_session)
