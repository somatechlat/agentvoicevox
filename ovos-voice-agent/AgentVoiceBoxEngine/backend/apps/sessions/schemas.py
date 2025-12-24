"""
Pydantic schemas for Session API.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from ninja import Schema


class SessionCreate(Schema):
    """Schema for creating a session."""
    project_id: UUID
    config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}


class SessionResponse(Schema):
    """Schema for session response."""
    id: UUID
    tenant_id: UUID
    project_id: UUID
    api_key_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    status: str
    config: Dict[str, Any]
    duration_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    audio_input_seconds: float
    audio_output_seconds: float
    total_audio_seconds: float
    turn_count: int
    error_code: str
    error_message: str
    metadata: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None

    @staticmethod
    def from_orm(session) -> "SessionResponse":
        return SessionResponse(
            id=session.id,
            tenant_id=session.tenant_id,
            project_id=session.project_id,
            api_key_id=session.api_key_id,
            user_id=session.user_id,
            status=session.status,
            config=session.config,
            duration_seconds=session.duration_seconds,
            input_tokens=session.input_tokens,
            output_tokens=session.output_tokens,
            total_tokens=session.total_tokens,
            audio_input_seconds=session.audio_input_seconds,
            audio_output_seconds=session.audio_output_seconds,
            total_audio_seconds=session.total_audio_seconds,
            turn_count=session.turn_count,
            error_code=session.error_code,
            error_message=session.error_message,
            metadata=session.metadata,
            created_at=session.created_at,
            started_at=session.started_at,
            terminated_at=session.terminated_at,
        )


class SessionListResponse(Schema):
    """Schema for paginated session list."""
    items: List[SessionResponse]
    total: int
    page: int
    page_size: int
    pages: int


class SessionEventResponse(Schema):
    """Schema for session event response."""
    id: UUID
    session_id: UUID
    event_type: str
    data: Dict[str, Any]
    created_at: datetime

    @staticmethod
    def from_orm(event) -> "SessionEventResponse":
        return SessionEventResponse(
            id=event.id,
            session_id=event.session_id,
            event_type=event.event_type,
            data=event.data,
            created_at=event.created_at,
        )


class SessionEventsResponse(Schema):
    """Schema for session events list."""
    items: List[SessionEventResponse]
    total: int


class SessionMetricsUpdate(Schema):
    """Schema for updating session metrics."""
    input_tokens: int = 0
    output_tokens: int = 0
    audio_input_seconds: float = 0
    audio_output_seconds: float = 0
    increment_turns: bool = False


class SessionTerminate(Schema):
    """Schema for terminating a session."""
    reason: str = ""


class SessionStats(Schema):
    """Schema for session statistics."""
    total_sessions: int
    active_sessions: int
    completed_sessions: int
    error_sessions: int
    total_duration_seconds: float
    total_input_tokens: int
    total_output_tokens: int
    total_audio_input_seconds: float
    total_audio_output_seconds: float
    average_duration_seconds: float
    average_turns: float
