"""
Session service layer.

Contains all business logic for session operations.
"""
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.db import transaction
from django.db.models import Avg, Count, Q, QuerySet, Sum
from django.utils import timezone

from apps.core.exceptions import (
    NotFoundError,
    TenantLimitExceededError,
    ValidationError,
)
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService

from .models import Session, SessionEvent


class SessionService:
    """Service class for session operations."""

    @staticmethod
    def get_by_id(session_id: UUID) -> Session:
        """
        Get session by ID.

        Raises:
            NotFoundError: If session not found
        """
        try:
            return Session.objects.select_related(
                "tenant", "project", "api_key", "user"
            ).get(id=session_id)
        except Session.DoesNotExist:
            raise NotFoundError(f"Session {session_id} not found")

    @staticmethod
    def list_sessions(
        tenant: Optional[Tenant] = None,
        project_id: Optional[UUID] = None,
        status: Optional[str] = None,
        api_key_id: Optional[UUID] = None,
        user_id: Optional[UUID] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[QuerySet, int]:
        """
        List sessions with filtering and pagination.

        Returns:
            Tuple of (queryset, total_count)
        """
        if tenant:
            qs = Session.all_objects.filter(tenant=tenant)
        else:
            qs = Session.objects.all()

        qs = qs.select_related("tenant", "project", "api_key", "user")

        # Apply filters
        if project_id:
            qs = qs.filter(project_id=project_id)
        if status:
            qs = qs.filter(status=status)
        if api_key_id:
            qs = qs.filter(api_key_id=api_key_id)
        if user_id:
            qs = qs.filter(user_id=user_id)
        if from_date:
            qs = qs.filter(created_at__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__lte=to_date)

        # Get total count before pagination
        total = qs.count()

        # Apply pagination
        offset = (page - 1) * page_size
        qs = qs[offset : offset + page_size]

        return qs, total

    @staticmethod
    @transaction.atomic
    def create_session(
        tenant: Tenant,
        project_id: UUID,
        api_key=None,
        user=None,
        config: Dict[str, Any] = None,
        metadata: Dict[str, Any] = None,
        client_ip: str = None,
        user_agent: str = None,
    ) -> Session:
        """
        Create a new session.

        Raises:
            NotFoundError: If project not found
            TenantLimitExceededError: If tenant session limit reached
        """
        from apps.projects.models import Project

        # Get project
        try:
            project = Project.all_objects.get(id=project_id, tenant=tenant)
        except Project.DoesNotExist:
            raise NotFoundError(f"Project {project_id} not found")

        # Check tenant session limit for current month
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_count = Session.all_objects.filter(
            tenant=tenant,
            created_at__gte=month_start,
        ).count()
        TenantService.enforce_limit(tenant, "sessions", current_count)

        # Check concurrent session limit for project
        active_count = Session.all_objects.filter(
            project=project,
            status=Session.Status.ACTIVE,
        ).count()
        if active_count >= project.max_concurrent_sessions:
            raise TenantLimitExceededError(
                f"Project has reached maximum concurrent sessions ({project.max_concurrent_sessions})"
            )

        # Build config from project defaults
        session_config = project.get_voice_config()
        if config:
            session_config.update(config)

        # Create session
        session = Session(
            tenant=tenant,
            project=project,
            api_key=api_key,
            user=user,
            config=session_config,
            metadata=metadata or {},
            client_ip=client_ip,
            user_agent=user_agent or "",
        )
        session.save()

        # Log creation event
        SessionService.log_event(
            session=session,
            event_type=SessionEvent.EventType.SESSION_CREATED,
            data={"config": session_config},
        )

        return session

    @staticmethod
    @transaction.atomic
    def start_session(session_id: UUID) -> Session:
        """
        Start a session.

        Raises:
            NotFoundError: If session not found
            ValidationError: If session is not in CREATED state
        """
        session = SessionService.get_by_id(session_id)

        if session.status != Session.Status.CREATED:
            raise ValidationError(f"Cannot start session in {session.status} state")

        session.start()

        SessionService.log_event(
            session=session,
            event_type=SessionEvent.EventType.SESSION_STARTED,
            data={},
        )

        return session

    @staticmethod
    @transaction.atomic
    def complete_session(session_id: UUID) -> Session:
        """
        Complete a session normally.

        Raises:
            NotFoundError: If session not found
            ValidationError: If session is not active
        """
        session = SessionService.get_by_id(session_id)

        if session.status != Session.Status.ACTIVE:
            raise ValidationError(f"Cannot complete session in {session.status} state")

        session.complete()

        SessionService.log_event(
            session=session,
            event_type=SessionEvent.EventType.SESSION_COMPLETED,
            data={
                "duration_seconds": session.duration_seconds,
                "turn_count": session.turn_count,
                "total_tokens": session.total_tokens,
            },
        )

        return session

    @staticmethod
    @transaction.atomic
    def terminate_session(session_id: UUID, reason: str = "") -> Session:
        """
        Terminate a session.

        Raises:
            NotFoundError: If session not found
        """
        session = SessionService.get_by_id(session_id)

        if session.status in [Session.Status.COMPLETED, Session.Status.TERMINATED]:
            return session  # Already terminated

        session.terminate(reason)

        SessionService.log_event(
            session=session,
            event_type=SessionEvent.EventType.SESSION_TERMINATED,
            data={"reason": reason},
        )

        return session

    @staticmethod
    @transaction.atomic
    def set_session_error(
        session_id: UUID,
        error_code: str,
        error_message: str,
    ) -> Session:
        """
        Set session to error state.

        Raises:
            NotFoundError: If session not found
        """
        session = SessionService.get_by_id(session_id)
        session.set_error(error_code, error_message)

        SessionService.log_event(
            session=session,
            event_type=SessionEvent.EventType.SESSION_ERROR,
            data={"error_code": error_code, "error_message": error_message},
        )

        return session

    @staticmethod
    @transaction.atomic
    def update_metrics(
        session_id: UUID,
        input_tokens: int = 0,
        output_tokens: int = 0,
        audio_input_seconds: float = 0,
        audio_output_seconds: float = 0,
        increment_turns: bool = False,
    ) -> Session:
        """
        Update session metrics.

        Raises:
            NotFoundError: If session not found
        """
        session = SessionService.get_by_id(session_id)
        session.update_metrics(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            audio_input_seconds=audio_input_seconds,
            audio_output_seconds=audio_output_seconds,
            increment_turns=increment_turns,
        )
        return session

    @staticmethod
    def log_event(
        session: Session,
        event_type: str,
        data: Dict[str, Any],
    ) -> SessionEvent:
        """Log a session event."""
        return SessionEvent.objects.create(
            session=session,
            event_type=event_type,
            data=data,
        )

    @staticmethod
    def get_events(
        session_id: UUID,
        event_type: Optional[str] = None,
    ) -> Tuple[List[SessionEvent], int]:
        """
        Get session events.

        Returns:
            Tuple of (events, total_count)
        """
        session = SessionService.get_by_id(session_id)
        qs = SessionEvent.objects.filter(session=session)

        if event_type:
            qs = qs.filter(event_type=event_type)

        total = qs.count()
        events = list(qs)

        return events, total

    @staticmethod
    def get_stats(
        tenant: Tenant,
        project_id: Optional[UUID] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get session statistics.

        Returns:
            Dictionary with session stats
        """
        qs = Session.all_objects.filter(tenant=tenant)

        if project_id:
            qs = qs.filter(project_id=project_id)
        if from_date:
            qs = qs.filter(created_at__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__lte=to_date)

        # Aggregate stats
        stats = qs.aggregate(
            total_sessions=Count("id"),
            total_duration=Sum("duration_seconds"),
            total_input_tokens=Sum("input_tokens"),
            total_output_tokens=Sum("output_tokens"),
            total_audio_input=Sum("audio_input_seconds"),
            total_audio_output=Sum("audio_output_seconds"),
            avg_duration=Avg("duration_seconds"),
            avg_turns=Avg("turn_count"),
        )

        # Count by status
        status_counts = qs.values("status").annotate(count=Count("id"))
        status_map = {s["status"]: s["count"] for s in status_counts}

        return {
            "total_sessions": stats["total_sessions"] or 0,
            "active_sessions": status_map.get(Session.Status.ACTIVE, 0),
            "completed_sessions": status_map.get(Session.Status.COMPLETED, 0),
            "error_sessions": status_map.get(Session.Status.ERROR, 0),
            "total_duration_seconds": stats["total_duration"] or 0,
            "total_input_tokens": stats["total_input_tokens"] or 0,
            "total_output_tokens": stats["total_output_tokens"] or 0,
            "total_audio_input_seconds": stats["total_audio_input"] or 0,
            "total_audio_output_seconds": stats["total_audio_output"] or 0,
            "average_duration_seconds": stats["avg_duration"] or 0,
            "average_turns": stats["avg_turns"] or 0,
        }

    @staticmethod
    @transaction.atomic
    def cleanup_expired_sessions(max_duration_hours: int = 24) -> int:
        """
        Terminate sessions that have exceeded maximum duration.

        Returns:
            Number of sessions terminated
        """
        cutoff = timezone.now() - timedelta(hours=max_duration_hours)

        expired_sessions = Session.all_objects.filter(
            status=Session.Status.ACTIVE,
            started_at__lt=cutoff,
        )

        count = 0
        for session in expired_sessions:
            session.terminate(reason=f"Exceeded maximum duration ({max_duration_hours} hours)")
            SessionService.log_event(
                session=session,
                event_type=SessionEvent.EventType.SESSION_TERMINATED,
                data={"reason": "auto_terminated", "max_duration_hours": max_duration_hours},
            )
            count += 1

        return count

    @staticmethod
    def count_active_sessions(tenant: Tenant) -> int:
        """Count active sessions in a tenant."""
        return Session.all_objects.filter(
            tenant=tenant,
            status=Session.Status.ACTIVE,
        ).count()

    @staticmethod
    def count_sessions_this_month(tenant: Tenant) -> int:
        """Count sessions created this month."""
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Session.all_objects.filter(
            tenant=tenant,
            created_at__gte=month_start,
        ).count()
