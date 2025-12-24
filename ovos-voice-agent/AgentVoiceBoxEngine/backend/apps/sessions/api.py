"""
Session API endpoints.

Public session endpoints for tenant-scoped operations.
"""
from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError
from apps.core.middleware.tenant import get_current_tenant

from .schemas import (
    SessionCreate,
    SessionEventsResponse,
    SessionEventResponse,
    SessionListResponse,
    SessionResponse,
    SessionStats,
    SessionTerminate,
)
from .services import SessionService

router = Router()


@router.get("", response=SessionListResponse)
def list_sessions(
    request,
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    status: Optional[str] = Query(None, description="Filter by status"),
    api_key_id: Optional[UUID] = Query(None, description="Filter by API key"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO format)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List sessions in the current tenant.

    Requires at least OPERATOR role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_operator:
        raise PermissionDeniedError("Operator role required to list sessions")

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

    pages = (total + page_size - 1) // page_size

    return SessionListResponse(
        items=[SessionResponse.from_orm(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/stats", response=SessionStats)
def get_session_stats(
    request,
    project_id: Optional[UUID] = Query(None, description="Filter by project"),
    from_date: Optional[str] = Query(None, description="Filter from date (ISO format)"),
    to_date: Optional[str] = Query(None, description="Filter to date (ISO format)"),
):
    """
    Get session statistics.

    Requires at least OPERATOR role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_operator:
        raise PermissionDeniedError("Operator role required to view session stats")

    stats = SessionService.get_stats(
        tenant=tenant,
        project_id=project_id,
        from_date=from_date,
        to_date=to_date,
    )

    return SessionStats(**stats)


@router.get("/{session_id}", response=SessionResponse)
def get_session(request, session_id: UUID):
    """
    Get session by ID.

    Requires at least OPERATOR role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_operator:
        raise PermissionDeniedError("Operator role required to view sessions")

    session = SessionService.get_by_id(session_id)

    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant")

    return SessionResponse.from_orm(session)


@router.get("/{session_id}/events", response=SessionEventsResponse)
def get_session_events(
    request,
    session_id: UUID,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
):
    """
    Get session events.

    Requires at least OPERATOR role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_operator:
        raise PermissionDeniedError("Operator role required to view session events")

    session = SessionService.get_by_id(session_id)
    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant")

    events, total = SessionService.get_events(session_id, event_type)

    return SessionEventsResponse(
        items=[SessionEventResponse.from_orm(e) for e in events],
        total=total,
    )


@router.post("", response=SessionResponse)
def create_session(request, payload: SessionCreate):
    """
    Create a new session.

    This endpoint is typically called via API key authentication.
    Requires at least DEVELOPER role for user authentication.
    """
    tenant = get_current_tenant()
    user = request.user

    # Get API key from request if present
    api_key = getattr(request, "api_key", None)

    # If no API key, require developer role
    if not api_key and not user.is_developer:
        raise PermissionDeniedError("Developer role required to create sessions")

    # Get client info
    client_ip = request.META.get("REMOTE_ADDR")
    user_agent = request.META.get("HTTP_USER_AGENT", "")

    session = SessionService.create_session(
        tenant=tenant,
        project_id=payload.project_id,
        api_key=api_key,
        user=user if not api_key else None,
        config=payload.config,
        metadata=payload.metadata,
        client_ip=client_ip,
        user_agent=user_agent,
    )

    return SessionResponse.from_orm(session)


@router.post("/{session_id}/start", response=SessionResponse)
def start_session(request, session_id: UUID):
    """
    Start a session.

    Requires at least DEVELOPER role.
    """
    tenant = get_current_tenant()
    user = request.user

    api_key = getattr(request, "api_key", None)
    if not api_key and not user.is_developer:
        raise PermissionDeniedError("Developer role required to start sessions")

    session = SessionService.get_by_id(session_id)
    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant")

    started_session = SessionService.start_session(session_id)
    return SessionResponse.from_orm(started_session)


@router.post("/{session_id}/complete", response=SessionResponse)
def complete_session(request, session_id: UUID):
    """
    Complete a session normally.

    Requires at least DEVELOPER role.
    """
    tenant = get_current_tenant()
    user = request.user

    api_key = getattr(request, "api_key", None)
    if not api_key and not user.is_developer:
        raise PermissionDeniedError("Developer role required to complete sessions")

    session = SessionService.get_by_id(session_id)
    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant")

    completed_session = SessionService.complete_session(session_id)
    return SessionResponse.from_orm(completed_session)


@router.post("/{session_id}/terminate", response=SessionResponse)
def terminate_session(request, session_id: UUID, payload: SessionTerminate = None):
    """
    Terminate a session.

    Requires at least OPERATOR role.
    """
    tenant = get_current_tenant()
    user = request.user

    api_key = getattr(request, "api_key", None)
    if not api_key and not user.is_operator:
        raise PermissionDeniedError("Operator role required to terminate sessions")

    session = SessionService.get_by_id(session_id)
    if session.tenant_id != tenant.id:
        raise PermissionDeniedError("Session not found in this tenant")

    reason = payload.reason if payload else ""
    terminated_session = SessionService.terminate_session(session_id, reason)
    return SessionResponse.from_orm(terminated_session)
