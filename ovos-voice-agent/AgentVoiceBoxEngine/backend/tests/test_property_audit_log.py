"""
Property tests for audit log immutability.

**Feature: django-saas-backend, Property 16: Audit Log Immutability**
**Validates: Requirements 12.5**

Tests that:
1. Update attempts raise error
2. Delete attempts raise error
3. Audit logs are created correctly

Uses REAL Django models and database - NO MOCKS.
"""

import uuid

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Safe text strategy (excludes NUL bytes which PostgreSQL doesn't support)
safe_text_strategy = st.text(
    alphabet=st.characters(blacklist_characters="\x00"),
    min_size=1,
    max_size=200,
).filter(str.strip)

# Action strategy
action_strategy = st.sampled_from(
    [
        "create",
        "update",
        "delete",
        "login",
        "logout",
        "api_call",
        "permission_change",
        "settings_change",
        "billing_event",
    ]
)

# Actor type strategy
actor_type_strategy = st.sampled_from(["user", "api_key", "system"])

# Resource type strategy
resource_type_strategy = st.sampled_from(
    [
        "tenant",
        "user",
        "project",
        "api_key",
        "session",
        "settings",
    ]
)


# ==========================================================================
# PROPERTY 16: AUDIT LOG IMMUTABILITY
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestAuditLogImmutability:
    """
    Property tests for audit log immutability.

    **Feature: django-saas-backend, Property 16: Audit Log Immutability**
    **Validates: Requirements 12.5**

    For any audit log entry:
    - Update attempts SHALL raise error
    - Delete attempts SHALL raise error
    """

    @pytest.mark.property
    @given(
        action=action_strategy,
        resource_type=resource_type_strategy,
        actor_type=actor_type_strategy,
    )
    @settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_audit_log_update_raises_error(
        self,
        action: str,
        resource_type: str,
        actor_type: str,
        tenant_factory,
    ):
        """
        Property: Update attempts raise ValueError.

        For any existing audit log entry,
        attempting to update it SHALL raise ValueError.

        **Validates: Requirement 12.5**
        """
        from apps.audit.models import AuditLog

        tenant = tenant_factory()

        # Create audit log
        audit_log = AuditLog.log(
            action=action,
            resource_type=resource_type,
            actor_id=str(uuid.uuid4()),
            actor_type=actor_type,
            tenant=tenant,
            description="Test audit log",
        )

        # Attempt to update
        audit_log.description = "Modified description"

        with pytest.raises(ValueError, match="cannot be modified"):
            audit_log.save()

    @pytest.mark.property
    @given(
        action=action_strategy,
        resource_type=resource_type_strategy,
        actor_type=actor_type_strategy,
    )
    @settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_audit_log_delete_raises_error(
        self,
        action: str,
        resource_type: str,
        actor_type: str,
        tenant_factory,
    ):
        """
        Property: Delete attempts raise ValueError.

        For any existing audit log entry,
        attempting to delete it SHALL raise ValueError.

        **Validates: Requirement 12.5**
        """
        from apps.audit.models import AuditLog

        tenant = tenant_factory()

        # Create audit log
        audit_log = AuditLog.log(
            action=action,
            resource_type=resource_type,
            actor_id=str(uuid.uuid4()),
            actor_type=actor_type,
            tenant=tenant,
            description="Test audit log",
        )

        # Attempt to delete
        with pytest.raises(ValueError, match="cannot be deleted"):
            audit_log.delete()

    @pytest.mark.property
    @given(
        action=action_strategy,
        resource_type=resource_type_strategy,
        actor_type=actor_type_strategy,
        description=safe_text_strategy,
    )
    @settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_audit_log_creation_succeeds(
        self,
        action: str,
        resource_type: str,
        actor_type: str,
        description: str,
        tenant_factory,
    ):
        """
        Property: Audit log creation succeeds with valid data.

        For any valid audit log data,
        creation SHALL succeed and persist the data.
        """
        from apps.audit.models import AuditLog

        tenant = tenant_factory()
        actor_id = str(uuid.uuid4())

        # Create audit log
        audit_log = AuditLog.log(
            action=action,
            resource_type=resource_type,
            actor_id=actor_id,
            actor_type=actor_type,
            tenant=tenant,
            description=description.strip(),
        )

        # Verify creation
        assert audit_log.id is not None
        assert audit_log.action == action
        assert audit_log.resource_type == resource_type
        assert audit_log.actor_id == actor_id
        assert audit_log.actor_type == actor_type
        assert audit_log.tenant_id == tenant.id
        assert audit_log.description == description.strip()
        assert audit_log.created_at is not None

        # Verify persistence
        retrieved = AuditLog.objects.get(id=audit_log.id)
        assert retrieved.action == action
        assert retrieved.description == description.strip()


# ==========================================================================
# AUDIT LOG QUERY TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestAuditLogQueries:
    """
    Property tests for audit log queries.
    """

    @pytest.mark.property
    @given(num_logs=st.integers(min_value=1, max_value=10))
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_for_tenant_returns_correct_logs(
        self,
        num_logs: int,
        tenant_factory,
    ):
        """
        Property: for_tenant returns only tenant's logs.

        For any tenant, the for_tenant query SHALL return
        only logs belonging to that tenant.
        """
        from apps.audit.models import AuditLog

        tenant_a = tenant_factory(name="Tenant A", slug=f"tenant-a-{uuid.uuid4().hex[:8]}")
        tenant_b = tenant_factory(name="Tenant B", slug=f"tenant-b-{uuid.uuid4().hex[:8]}")

        # Create logs for tenant A
        for i in range(num_logs):
            AuditLog.log(
                action="create",
                resource_type="project",
                actor_id=str(uuid.uuid4()),
                actor_type="user",
                tenant=tenant_a,
                description=f"Tenant A log {i}",
            )

        # Create logs for tenant B
        for i in range(num_logs):
            AuditLog.log(
                action="create",
                resource_type="project",
                actor_id=str(uuid.uuid4()),
                actor_type="user",
                tenant=tenant_b,
                description=f"Tenant B log {i}",
            )

        # Query for tenant A
        tenant_a_logs = AuditLog.objects.for_tenant(tenant_a)
        assert tenant_a_logs.count() == num_logs
        for log in tenant_a_logs:
            assert log.tenant_id == tenant_a.id

        # Query for tenant B
        tenant_b_logs = AuditLog.objects.for_tenant(tenant_b)
        assert tenant_b_logs.count() == num_logs
        for log in tenant_b_logs:
            assert log.tenant_id == tenant_b.id

    @pytest.mark.property
    @given(
        resource_type=resource_type_strategy,
        resource_id=st.uuids(),
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_for_resource_returns_correct_logs(
        self,
        resource_type: str,
        resource_id: uuid.UUID,
        tenant_factory,
    ):
        """
        Property: for_resource returns logs for specific resource.

        For any resource type and ID, the for_resource query SHALL
        return only logs for that resource.
        """
        from apps.audit.models import AuditLog

        tenant = tenant_factory()

        # Create log for specific resource
        AuditLog.log(
            action="create",
            resource_type=resource_type,
            resource_id=str(resource_id),
            actor_id=str(uuid.uuid4()),
            actor_type="user",
            tenant=tenant,
        )

        # Create log for different resource
        AuditLog.log(
            action="create",
            resource_type=resource_type,
            resource_id=str(uuid.uuid4()),
            actor_id=str(uuid.uuid4()),
            actor_type="user",
            tenant=tenant,
        )

        # Query for specific resource
        resource_logs = AuditLog.objects.for_resource(resource_type, str(resource_id))
        assert resource_logs.count() == 1
        assert resource_logs.first().resource_id == str(resource_id)


# ==========================================================================
# AUDIT LOG CONVENIENCE METHOD TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestAuditLogConvenienceMethods:
    """
    Property tests for audit log convenience methods.
    """

    @pytest.mark.property
    @given(
        action=action_strategy,
        resource_type=resource_type_strategy,
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_log_system_action_sets_correct_actor(
        self,
        action: str,
        resource_type: str,
        tenant_factory,
    ):
        """
        Property: log_system_action sets actor_type to 'system'.

        For any system action, the actor_type SHALL be 'system'
        and actor_id SHALL be 'system'.
        """
        from apps.audit.models import AuditLog

        tenant = tenant_factory()

        audit_log = AuditLog.log_system_action(
            action=action,
            resource_type=resource_type,
            tenant=tenant,
            description="System action",
        )

        assert audit_log.actor_type == "system"
        assert audit_log.actor_id == "system"
        assert audit_log.actor_email == ""

    @pytest.mark.property
    @given(
        old_value=safe_text_strategy,
        new_value=safe_text_strategy,
    )
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_audit_log_stores_old_and_new_values(
        self,
        old_value: str,
        new_value: str,
        tenant_factory,
    ):
        """
        Property: Audit log stores old and new values correctly.

        For any update action with old and new values,
        both SHALL be stored in the audit log.
        """
        from apps.audit.models import AuditLog

        tenant = tenant_factory()

        old_values = {"name": old_value.strip()}
        new_values = {"name": new_value.strip()}

        audit_log = AuditLog.log(
            action="update",
            resource_type="project",
            actor_id=str(uuid.uuid4()),
            actor_type="user",
            tenant=tenant,
            old_values=old_values,
            new_values=new_values,
        )

        assert audit_log.old_values == old_values
        assert audit_log.new_values == new_values

        # Verify persistence
        retrieved = AuditLog.objects.get(id=audit_log.id)
        assert retrieved.old_values == old_values
        assert retrieved.new_values == new_values
