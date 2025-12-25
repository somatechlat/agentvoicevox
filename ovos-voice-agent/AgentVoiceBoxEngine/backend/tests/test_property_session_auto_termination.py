"""
Property tests for session auto-termination.

**Feature: django-saas-backend, Property 11: Session Auto-Termination**
**Validates: Requirements 8.10**

Tests that:
1. Sessions exceeding 24 hours are automatically terminated
2. Active sessions within limit are not terminated
3. Termination reason is recorded correctly

Uses REAL Django models and database - NO MOCKS.
"""

import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Hours exceeding 24-hour limit
hours_exceeding_limit = st.integers(min_value=25, max_value=72)

# Hours within 24-hour limit
hours_within_limit = st.integers(min_value=1, max_value=23)


# ==========================================================================
# PROPERTY 11: SESSION AUTO-TERMINATION
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestSessionAutoTermination:
    """
    Property tests for session auto-termination.

    **Feature: django-saas-backend, Property 11: Session Auto-Termination**
    **Validates: Requirements 8.10**

    For any session exceeding 24 hours:
    - The system SHALL automatically terminate it
    - Status SHALL be set to 'terminated'
    """

    @pytest.fixture
    def project_factory(self, tenant_factory):
        """Factory for creating test projects."""
        from apps.projects.models import Project

        created_projects = []

        def _create_project(tenant=None, name="Test Project"):
            if tenant is None:
                tenant = tenant_factory()

            project = Project.objects.create(
                tenant=tenant,
                name=name,
                slug=f"test-project-{uuid.uuid4().hex[:8]}",
            )
            created_projects.append(project)
            return project

        yield _create_project

        for project in created_projects:
            try:
                project.delete()
            except Exception:
                pass

    @pytest.fixture
    def session_factory(self, tenant_factory, project_factory):
        """Factory for creating test sessions."""
        from apps.sessions.models import Session

        created_sessions = []

        def _create_session(
            tenant=None,
            project=None,
            status="active",
            started_at=None,
        ):
            if tenant is None:
                tenant = tenant_factory()
            if project is None:
                project = project_factory(tenant=tenant)

            session = Session(
                tenant=tenant,
                project=project,
                status=status,
                started_at=started_at or timezone.now(),
            )
            session.save()
            created_sessions.append(session)
            return session

        yield _create_session

        for session in created_sessions:
            try:
                session.delete()
            except Exception:
                pass

    @pytest.mark.property
    @given(hours_over=hours_exceeding_limit)
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_sessions_exceeding_24_hours_are_terminated(
        self,
        hours_over: int,
        session_factory,
    ):
        """
        Property: Sessions exceeding 24 hours are terminated.

        For any active session started more than 24 hours ago,
        cleanup_expired_sessions SHALL terminate it.

        **Validates: Requirement 8.10**
        """
        from apps.sessions.models import Session
        from apps.sessions.services import SessionService

        # Create session started hours_over ago
        started_at = timezone.now() - timedelta(hours=hours_over)
        session = session_factory(status="active", started_at=started_at)

        # Verify session is active
        assert session.status == Session.Status.ACTIVE

        # Run cleanup
        terminated_count = SessionService.cleanup_expired_sessions(max_duration_hours=24)

        # Verify session was terminated
        session.refresh_from_db()
        assert session.status == Session.Status.TERMINATED
        assert terminated_count >= 1

    @pytest.mark.property
    @given(hours_active=hours_within_limit)
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_sessions_within_24_hours_not_terminated(
        self,
        hours_active: int,
        session_factory,
    ):
        """
        Property: Sessions within 24 hours are NOT terminated.

        For any active session started less than 24 hours ago,
        cleanup_expired_sessions SHALL NOT terminate it.

        **Validates: Requirement 8.10**
        """
        from apps.sessions.models import Session
        from apps.sessions.services import SessionService

        # Create session started hours_active ago (within limit)
        started_at = timezone.now() - timedelta(hours=hours_active)
        session = session_factory(status="active", started_at=started_at)

        # Verify session is active
        assert session.status == Session.Status.ACTIVE

        # Run cleanup
        SessionService.cleanup_expired_sessions(max_duration_hours=24)

        # Verify session is still active
        session.refresh_from_db()
        assert session.status == Session.Status.ACTIVE

    @pytest.mark.property
    @given(hours_over=hours_exceeding_limit)
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_termination_reason_is_recorded(
        self,
        hours_over: int,
        session_factory,
    ):
        """
        Property: Termination reason is recorded in metadata.

        For any auto-terminated session,
        the termination reason SHALL be recorded.

        **Validates: Requirement 8.10**
        """
        from apps.sessions.services import SessionService

        # Create expired session
        started_at = timezone.now() - timedelta(hours=hours_over)
        session = session_factory(status="active", started_at=started_at)

        # Run cleanup
        SessionService.cleanup_expired_sessions(max_duration_hours=24)

        # Verify termination reason
        session.refresh_from_db()
        assert "termination_reason" in session.metadata
        assert "24" in session.metadata["termination_reason"]

    @pytest.mark.property
    @given(num_expired=st.integers(min_value=1, max_value=5))
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_multiple_expired_sessions_all_terminated(
        self,
        num_expired: int,
        session_factory,
        tenant_factory,
    ):
        """
        Property: All expired sessions are terminated.

        For any number of expired sessions,
        cleanup SHALL terminate all of them.

        **Validates: Requirement 8.10**
        """
        from apps.sessions.models import Session
        from apps.sessions.services import SessionService

        tenant = tenant_factory()
        sessions = []

        # Create multiple expired sessions
        for i in range(num_expired):
            started_at = timezone.now() - timedelta(hours=25 + i)
            session = session_factory(
                tenant=tenant,
                status="active",
                started_at=started_at,
            )
            sessions.append(session)

        # Run cleanup
        terminated_count = SessionService.cleanup_expired_sessions(max_duration_hours=24)

        # Verify all were terminated
        assert terminated_count >= num_expired
        for session in sessions:
            session.refresh_from_db()
            assert session.status == Session.Status.TERMINATED

    @pytest.mark.property
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_non_active_sessions_not_affected(self, session_factory):
        """
        Property: Non-active sessions are not affected by cleanup.

        For any session not in 'active' status,
        cleanup SHALL NOT modify it.
        """
        from apps.sessions.models import Session
        from apps.sessions.services import SessionService

        # Create completed session (old)
        started_at = timezone.now() - timedelta(hours=48)
        session = session_factory(status="completed", started_at=started_at)
        session.status = Session.Status.COMPLETED
        session.save()

        # Run cleanup
        SessionService.cleanup_expired_sessions(max_duration_hours=24)

        # Verify session is still completed (not terminated)
        session.refresh_from_db()
        assert session.status == Session.Status.COMPLETED


# ==========================================================================
# SESSION EVENT LOGGING TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestSessionTerminationEvents:
    """
    Property tests for session termination event logging.
    """

    @pytest.fixture
    def project_factory(self, tenant_factory):
        """Factory for creating test projects."""
        from apps.projects.models import Project

        created_projects = []

        def _create_project(tenant=None, name="Test Project"):
            if tenant is None:
                tenant = tenant_factory()

            project = Project.objects.create(
                tenant=tenant,
                name=name,
                slug=f"test-project-{uuid.uuid4().hex[:8]}",
            )
            created_projects.append(project)
            return project

        yield _create_project

        for project in created_projects:
            try:
                project.delete()
            except Exception:
                pass

    @pytest.fixture
    def session_factory(self, tenant_factory, project_factory):
        """Factory for creating test sessions."""
        from apps.sessions.models import Session

        created_sessions = []

        def _create_session(
            tenant=None,
            project=None,
            status="active",
            started_at=None,
        ):
            if tenant is None:
                tenant = tenant_factory()
            if project is None:
                project = project_factory(tenant=tenant)

            session = Session(
                tenant=tenant,
                project=project,
                status=status,
                started_at=started_at or timezone.now(),
            )
            session.save()
            created_sessions.append(session)
            return session

        yield _create_session

        for session in created_sessions:
            try:
                session.delete()
            except Exception:
                pass

    @pytest.mark.property
    @given(hours_over=hours_exceeding_limit)
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_termination_event_is_logged(
        self,
        hours_over: int,
        session_factory,
    ):
        """
        Property: Termination event is logged for auto-terminated sessions.

        For any auto-terminated session,
        a SESSION_TERMINATED event SHALL be logged.
        """
        from apps.sessions.models import SessionEvent
        from apps.sessions.services import SessionService

        # Create expired session
        started_at = timezone.now() - timedelta(hours=hours_over)
        session = session_factory(status="active", started_at=started_at)

        # Run cleanup
        SessionService.cleanup_expired_sessions(max_duration_hours=24)

        # Verify termination event was logged
        events = SessionEvent.objects.filter(
            session=session,
            event_type=SessionEvent.EventType.SESSION_TERMINATED,
        )
        assert events.exists()

        # Verify event data
        event = events.first()
        assert "auto_terminated" in str(event.data.get("reason", ""))
