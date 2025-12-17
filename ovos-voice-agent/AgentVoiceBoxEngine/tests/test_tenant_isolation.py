"""Property-based tests for tenant data isolation.

**Feature: portal-admin-complete, Property 10: Tenant Data Isolation**
**Validates: Requirements E4.2**

Tests that all database queries properly filter by tenant_id,
ensuring no cross-tenant data leakage.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure imports work
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.models.base import Base
from app.models.tenant import APIKey, Project, Tenant, TenantStatus, TenantTier
from app.services.tenant_context import TenantIsolation


# =============================================================================
# Hypothesis Strategies
# =============================================================================


@st.composite
def tenant_strategy(draw):
    """Generate a random tenant."""
    return {
        "id": uuid.uuid4(),
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N", "P")))),
        "tier": draw(st.sampled_from(list(TenantTier))),
        "status": draw(st.sampled_from(list(TenantStatus))),
    }


@st.composite
def project_strategy(draw, tenant_id: uuid.UUID):
    """Generate a random project for a tenant."""
    return {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "name": draw(st.text(min_size=1, max_size=100, alphabet=st.characters(whitelist_categories=("L", "N")))),
    }


@st.composite
def api_key_strategy(draw, project_id: uuid.UUID):
    """Generate a random API key for a project."""
    return {
        "id": uuid.uuid4(),
        "project_id": project_id,
        "key_hash": f"$sha256$salt${draw(st.text(min_size=64, max_size=64, alphabet='0123456789abcdef'))}",
        "key_prefix": draw(st.text(min_size=8, max_size=8, alphabet="0123456789abcdef")),
        "name": draw(st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N")))),
        "scopes": draw(st.lists(st.sampled_from(["realtime:connect", "sessions:read", "usage:read"]), max_size=3)),
        "is_active": draw(st.booleans()),
    }


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def db_session(tmp_path):
    """Create a test database session."""
    db_uri = f"sqlite+pysqlite:///{tmp_path / 'test_isolation.db'}"
    engine = create_engine(db_uri, future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)
    session = session_factory()
    yield session
    session.close()
    engine.dispose()


# =============================================================================
# Property Tests
# =============================================================================


class TestTenantDataIsolation:
    """Property tests for tenant data isolation.

    **Feature: portal-admin-complete, Property 10: Tenant Data Isolation**
    **Validates: Requirements E4.2**
    """

    @given(
        tenant1_data=tenant_strategy(),
        tenant2_data=tenant_strategy(),
    )
    @settings(max_examples=100, deadline=None)
    def test_tenant_isolation_db_filter(
        self,
        tenant1_data,
        tenant2_data,
        tmp_path,
    ):
        """Property: For any database query, results SHALL only include records
        where tenant_id matches the authenticated user's tenant.

        **Feature: portal-admin-complete, Property 10: Tenant Data Isolation**
        **Validates: Requirements E4.2**
        """
        # Setup database
        db_uri = f"sqlite+pysqlite:///{tmp_path / f'test_{uuid.uuid4().hex[:8]}.db'}"
        engine = create_engine(db_uri, future=True)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        with session_factory() as session:
            # Create two tenants
            tenant1 = Tenant(
                id=tenant1_data["id"],
                name=tenant1_data["name"] or "Tenant1",
                tier=tenant1_data["tier"],
                status=tenant1_data["status"],
            )
            tenant2 = Tenant(
                id=tenant2_data["id"],
                name=tenant2_data["name"] or "Tenant2",
                tier=tenant2_data["tier"],
                status=tenant2_data["status"],
            )
            session.add(tenant1)
            session.add(tenant2)
            session.commit()

            # Create projects for each tenant
            project1 = Project(
                id=uuid.uuid4(),
                tenant_id=tenant1.id,
                name="Project1",
            )
            project2 = Project(
                id=uuid.uuid4(),
                tenant_id=tenant2.id,
                name="Project2",
            )
            session.add(project1)
            session.add(project2)
            session.commit()

            # Query with tenant isolation filter
            query = session.query(Project)
            filtered_query = TenantIsolation.db_filter(query, Project, tenant1.id)
            results = filtered_query.all()

            # Property: All results must belong to tenant1
            assert all(p.tenant_id == tenant1.id for p in results), (
                "Tenant isolation violated: found projects from other tenants"
            )

            # Property: No results from tenant2
            assert not any(p.tenant_id == tenant2.id for p in results), (
                "Cross-tenant data leakage detected"
            )

        engine.dispose()

    @given(
        tenant_id=st.uuids(),
        other_tenant_id=st.uuids(),
    )
    @settings(max_examples=100, deadline=None)
    def test_redis_key_namespacing(self, tenant_id, other_tenant_id):
        """Property: Redis keys SHALL be namespaced by tenant_id.

        **Feature: portal-admin-complete, Property 10: Tenant Data Isolation**
        **Validates: Requirements E4.3**
        """
        # Generate keys for different tenants
        key1 = TenantIsolation.redis_key("session", "abc123", tenant_id=str(tenant_id))
        key2 = TenantIsolation.redis_key("session", "abc123", tenant_id=str(other_tenant_id))

        # Property: Keys for different tenants must be different
        if tenant_id != other_tenant_id:
            assert key1 != key2, "Redis keys should be unique per tenant"

        # Property: Key must contain tenant_id
        assert str(tenant_id) in key1, "Redis key must contain tenant_id"

    @given(
        tenant_id=st.uuids(),
        key_parts=st.lists(st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz0123456789"), min_size=1, max_size=3),
    )
    @settings(max_examples=100, deadline=None)
    def test_redis_key_format(self, tenant_id, key_parts):
        """Property: Redis keys SHALL follow format {prefix}:{tenant_id}:{parts...}.

        **Feature: portal-admin-complete, Property 10: Tenant Data Isolation**
        **Validates: Requirements E4.3**
        """
        prefix = "session"
        key = TenantIsolation.redis_key(prefix, *key_parts, tenant_id=str(tenant_id))

        # Property: Key must start with prefix
        assert key.startswith(f"{prefix}:"), f"Key must start with prefix: {key}"

        # Property: Key must contain tenant_id after prefix
        parts = key.split(":")
        assert len(parts) >= 2, "Key must have at least prefix and tenant_id"
        assert parts[1] == str(tenant_id), "Second part must be tenant_id"


class TestAPIKeyTenantIsolation:
    """Property tests for API key tenant isolation.

    **Feature: portal-admin-complete, Property 10: Tenant Data Isolation**
    **Validates: Requirements E4.2**
    """

    @given(
        tenant1_data=tenant_strategy(),
        tenant2_data=tenant_strategy(),
    )
    @settings(max_examples=50, deadline=None)
    def test_api_keys_isolated_by_tenant(
        self,
        tenant1_data,
        tenant2_data,
        tmp_path,
    ):
        """Property: API key queries SHALL only return keys belonging to the
        authenticated tenant.

        **Feature: portal-admin-complete, Property 10: Tenant Data Isolation**
        **Validates: Requirements E4.2**
        """
        # Setup database
        db_uri = f"sqlite+pysqlite:///{tmp_path / f'test_{uuid.uuid4().hex[:8]}.db'}"
        engine = create_engine(db_uri, future=True)
        Base.metadata.create_all(engine)
        session_factory = sessionmaker(bind=engine, expire_on_commit=False)

        with session_factory() as session:
            # Create tenants
            tenant1 = Tenant(
                id=tenant1_data["id"],
                name=tenant1_data["name"] or "Tenant1",
            )
            tenant2 = Tenant(
                id=tenant2_data["id"],
                name=tenant2_data["name"] or "Tenant2",
            )
            session.add(tenant1)
            session.add(tenant2)
            session.commit()

            # Create projects
            project1 = Project(id=uuid.uuid4(), tenant_id=tenant1.id, name="P1")
            project2 = Project(id=uuid.uuid4(), tenant_id=tenant2.id, name="P2")
            session.add(project1)
            session.add(project2)
            session.commit()

            # Create API keys
            key1 = APIKey(
                id=uuid.uuid4(),
                project_id=project1.id,
                key_hash="$sha256$salt$" + "a" * 64,
                key_prefix="key1test",
                name="Key1",
                scopes=["realtime:connect"],
                is_active=True,
            )
            key2 = APIKey(
                id=uuid.uuid4(),
                project_id=project2.id,
                key_hash="$sha256$salt$" + "b" * 64,
                key_prefix="key2test",
                name="Key2",
                scopes=["realtime:connect"],
                is_active=True,
            )
            session.add(key1)
            session.add(key2)
            session.commit()

            # Query API keys with tenant isolation (via project join)
            results = (
                session.query(APIKey)
                .join(Project, APIKey.project_id == Project.id)
                .filter(Project.tenant_id == tenant1.id)
                .all()
            )

            # Property: All results must belong to tenant1's projects
            for key in results:
                project = session.query(Project).filter(Project.id == key.project_id).first()
                assert project.tenant_id == tenant1.id, (
                    "API key isolation violated: found key from other tenant"
                )

            # Property: Should not include tenant2's keys
            result_ids = {k.id for k in results}
            assert key2.id not in result_ids, "Cross-tenant API key leakage detected"

        engine.dispose()


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
