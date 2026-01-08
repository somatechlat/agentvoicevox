"""
Session Service Layer
=====================

This module contains all the business logic for managing voice interaction sessions.
It provides comprehensive functionality for session creation, lifecycle management,
metric tracking, event logging, and analytics. This service ensures that sessions
adhere to tenant and project limits, and that data is consistent and accurate.
"""

from datetime import timedelta
from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Avg, Count, QuerySet, Sum
from django.utils import timezone

from apps.api_keys.models import APIKey
from apps.core.exceptions import (
    NotFoundError,
    TenantLimitExceededError,
    ValidationError,
)
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService
from apps.users.models import User

from .models import Session, SessionEvent


class SessionService:
    """A service class encapsulating all business logic for Session operations."""

    @staticmethod
    def get_by_id(session_id: UUID) -> Session:
        """
        Retrieves a single session by its primary key (ID).

        Args:
            session_id: The UUID of the session to retrieve.

        Returns:
            The Session instance.

        Raises:
            NotFoundError: If a session with the specified ID does not exist.
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
    ) -> tuple[QuerySet, int]:
        """
        Provides a paginated and filterable list of sessions.

        If a `tenant` is provided, it lists sessions for that specific tenant
        (typically for admin views). If `tenant` is None, it uses the default
        tenant-scoped manager to list sessions for the current user's tenant.

        Args:
            tenant: (Optional) The Tenant for which to list sessions.
            project_id: (Optional) Filter sessions by a specific project ID.
            status: (Optional) Filter sessions by their status (e.g., 'active', 'completed').
            api_key_id: (Optional) Filter sessions by the API key used.
            user_id: (Optional) Filter sessions by the user who initiated them.
            from_date: (Optional) Filter sessions created on or after this date (ISO format).
            to_date: (Optional) Filter sessions created on or before this date (ISO format).
            page: The page number for pagination.
            page_size: The number of items per page.

        Returns:
            A tuple containing:
            - A queryset of Session instances for the requested page.
            - An integer representing the total count of sessions matching the filters.
        """
        if tenant:
            # For admin views, filter by explicit tenant.
            qs = Session.all_objects.filter(tenant=tenant)
        else:
            # For tenant-scoped views, use the default manager.
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

        total = qs.count()
        offset = (page - 1) * page_size
        paginated_qs = qs[offset : offset + page_size]

        return paginated_qs, total

    @staticmethod
    @transaction.atomic
    def create_session(
        tenant: Tenant,
        project_id: UUID,
        api_key: Optional[APIKey] = None,
        user: Optional[User] = None,
        config: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Session:
        """
        Initializes a new voice interaction session, performing necessary limit checks.

        This method:
        1.  Retrieves the associated `Project`.
        2.  Enforces tenant-level monthly session limits.
        3.  Enforces project-level concurrent session limits.
        4.  Builds the initial session configuration from project defaults,
            allowing optional overrides.
        5.  Creates the `Session` record.
        6.  Logs a `session.created` event.

        Args:
            tenant: The Tenant initiating the session.
            project_id: The UUID of the Project the session is associated with.
            api_key: (Optional) The APIKey used to create the session.
            user: (Optional) The User who created the session.
            config: (Optional) Dictionary of configuration overrides for the session.
            metadata: (Optional) Additional, unstructured metadata for the session.
            client_ip: (Optional) The IP address of the client.
            user_agent: (Optional) The user agent string of the client.

        Returns:
            The newly created Session instance in 'CREATED' status.

        Raises:
            NotFoundError: If the project is not found for the given tenant.
            TenantLimitExceededError: If tenant monthly or project concurrent session limits are met.
        """
        from apps.projects.models import (
            Project,
        )  # Local import to avoid circular dependency.

        try:
            # Use all_objects for Project lookup, but filter by tenant.
            project = Project.all_objects.get(id=project_id, tenant=tenant)
        except Project.DoesNotExist:
            raise NotFoundError(
                f"Project {project_id} not found for tenant {tenant.id}"
            )

        # Enforce tenant monthly session limit.
        current_month_sessions_count = SessionService.count_sessions_this_month(tenant)
        TenantService.enforce_limit(
            tenant, "max_sessions_per_month", current_month_sessions_count
        )

        # Enforce project concurrent session limit.
        active_concurrent_sessions = Session.all_objects.filter(
            project=project, status=Session.Status.ACTIVE
        ).count()
        if active_concurrent_sessions >= project.max_concurrent_sessions:
            raise TenantLimitExceededError(
                f"Project '{project.name}' has reached its maximum concurrent sessions limit ({project.max_concurrent_sessions})."
            )

        # Build session config from project defaults, allowing overrides.
        session_config = project.get_voice_config()
        if config:
            session_config.update(config)

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
        Transitions a session from 'CREATED' to 'ACTIVE' status.

        Args:
            session_id: The UUID of the session to start.

        Returns:
            The updated Session instance.

        Raises:
            NotFoundError: If the session does not exist.
            ValidationError: If the session is not in the 'CREATED' state.
        """
        session = SessionService.get_by_id(session_id)

        if session.status != Session.Status.CREATED:
            raise ValidationError(
                f"Cannot start session in {session.status} state. Only 'CREATED' sessions can be started."
            )

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
        Marks a session as 'COMPLETED' (normal termination) and calculates its final duration.

        Args:
            session_id: The UUID of the session to complete.

        Returns:
            The updated Session instance.

        Raises:
            NotFoundError: If the session does not exist.
            ValidationError: If the session is not in the 'ACTIVE' state.
        """
        session = SessionService.get_by_id(session_id)

        if session.status != Session.Status.ACTIVE:
            raise ValidationError(
                f"Cannot complete session in {session.status} state. Only 'ACTIVE' sessions can be completed."
            )

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
        Transitions a session to 'TERMINATED' status (abnormal termination).

        If the session is already completed or terminated, no action is taken.

        Args:
            session_id: The UUID of the session to terminate.
            reason: (Optional) A text description for the reason of termination.

        Returns:
            The updated Session instance.

        Raises:
            NotFoundError: If the session does not exist.
        """
        session = SessionService.get_by_id(session_id)

        if session.status in [Session.Status.COMPLETED, Session.Status.TERMINATED]:
            return session  # Idempotent: already terminated or completed.

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
        Transitions a session to 'ERROR' status and records error details.

        Args:
            session_id: The UUID of the session that encountered an error.
            error_code: A code identifying the type of error.
            error_message: A detailed message describing the error.

        Returns:
            The updated Session instance.

        Raises:
            NotFoundError: If the session does not exist.
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
        Updates various usage metrics for a given session.

        This method is typically called incrementally during an active session
        to aggregate usage statistics.

        Args:
            session_id: The UUID of the session to update.
            input_tokens: Number of input tokens to add.
            output_tokens: Number of output tokens to add.
            audio_input_seconds: Duration of audio input to add.
            audio_output_seconds: Duration of audio output to add.
            increment_turns: If True, increments the `turn_count` by one.

        Returns:
            The updated Session instance.

        Raises:
            NotFoundError: If the session does not exist.
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
        data: Optional[dict[str, Any]] = None,
    ) -> SessionEvent:
        """
        Creates and saves a new `SessionEvent` record for the specified session.

        Args:
            session: The Session instance to log the event for.
            event_type: The type of event (from `SessionEvent.EventType`).
            data: (Optional) A dictionary of event-specific data to store.

        Returns:
            The newly created SessionEvent instance.
        """
        return SessionEvent.objects.create(
            session=session,
            event_type=event_type,
            data=data or {},
        )

    @staticmethod
    def get_events(
        session_id: UUID,
        event_type: Optional[str] = None,
    ) -> tuple[list[SessionEvent], int]:
        """
        Retrieves all events for a specific session, with optional filtering by event type.

        Args:
            session_id: The UUID of the session whose events are to be retrieved.
            event_type: (Optional) Filter events by a specific type.

        Returns:
            A tuple containing:
            - A list of SessionEvent instances.
            - An integer representing the total count of events.
        """
        session = SessionService.get_by_id(session_id)
        qs = SessionEvent.objects.filter(session=session)

        if event_type:
            qs = qs.filter(event_type=event_type)

        total = qs.count()
        events = list(qs.order_by("created_at"))  # Ensure chronological order.

        return events, total

    @staticmethod
    def get_stats(
        tenant: Tenant,
        project_id: Optional[UUID] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Aggregates and returns various statistics for sessions belonging to a tenant.

        This method provides insights into usage patterns, such as total sessions,
        duration, token usage, and error rates, with optional filtering by project
        and date range.

        Args:
            tenant: The Tenant for which to gather statistics.
            project_id: (Optional) Filter statistics for a specific project.
            from_date: (Optional) Include sessions created on or after this date.
            to_date: (Optional) Include sessions created on or before this date.

        Returns:
            A dictionary containing aggregated session statistics.
        """
        qs = Session.all_objects.filter(tenant=tenant)

        if project_id:
            qs = qs.filter(project_id=project_id)
        if from_date:
            qs = qs.filter(created_at__gte=from_date)
        if to_date:
            qs = qs.filter(created_at__lte=to_date)

        # Aggregate numerical statistics.
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

        # Count sessions by their status for a breakdown.
        status_counts = qs.values("status").annotate(count=Count("id"))
        status_map = {s["status"]: s["count"] for s in status_counts}

        return {
            "total_sessions": stats["total_sessions"] or 0,
            "active_sessions": status_map.get(Session.Status.ACTIVE, 0),
            "completed_sessions": status_map.get(Session.Status.COMPLETED, 0),
            "error_sessions": status_map.get(Session.Status.ERROR, 0),
            "terminated_sessions": status_map.get(Session.Status.TERMINATED, 0),
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
        Identifies and terminates 'ACTIVE' sessions that have exceeded a maximum duration.

        This maintenance task helps prevent stale or abandoned sessions from
        consuming resources and skewing metrics. Each terminated session
        will have a `session.terminated` event logged.

        Args:
            max_duration_hours: The maximum number of hours an active session is allowed to run.

        Returns:
            The number of sessions that were terminated during this cleanup.
        """
        cutoff_time = timezone.now() - timedelta(hours=max_duration_hours)

        # Find active sessions that started before the cutoff time.
        expired_sessions = Session.all_objects.filter(
            status=Session.Status.ACTIVE,
            started_at__lt=cutoff_time,
        )

        terminated_count = 0
        for session in expired_sessions:
            session.terminate(
                reason=f"Exceeded maximum duration of {max_duration_hours} hours"
            )
            SessionService.log_event(
                session=session,
                event_type=SessionEvent.EventType.SESSION_TERMINATED,
                data={
                    "reason": "auto_terminated",
                    "max_duration_hours": max_duration_hours,
                },
            )
            terminated_count += 1

        return terminated_count

    @staticmethod
    def count_active_sessions(tenant: Tenant) -> int:
        """
        Counts the number of currently active sessions for a specific tenant.
        """
        return Session.all_objects.filter(
            tenant=tenant,
            status=Session.Status.ACTIVE,
        ).count()

    @staticmethod
    def count_sessions_this_month(tenant: Tenant) -> int:
        """
        Counts the number of sessions created by a specific tenant in the current month.
        This is used for enforcing monthly session limits.
        """
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return Session.all_objects.filter(
            tenant=tenant,
            created_at__gte=month_start,
        ).count()
