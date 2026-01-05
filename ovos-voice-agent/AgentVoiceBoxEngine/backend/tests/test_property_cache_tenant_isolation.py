"""
Property tests for cache tenant isolation.

**Feature: django-saas-backend, Property 13: Cache Tenant Isolation**
**Validates: Requirements 10.1**

Tests that:
1. Cache keys are prefixed with tenant ID
2. Different tenants cannot access each other's cached data
3. Global cache keys work without tenant context

Uses REAL Django cache backend - NO MOCKS.
"""

import uuid

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Cache key strategy
cache_key_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
    min_size=1,
    max_size=50,
).filter(str.strip)

# Cache value strategy
cache_value_strategy = st.one_of(
    st.text(min_size=1, max_size=100).filter(str.strip),
    st.integers(min_value=-1000, max_value=1000),
    st.lists(st.integers(), min_size=1, max_size=10),
    st.dictionaries(
        keys=st.text(min_size=1, max_size=10).filter(str.strip),
        values=st.integers(),
        min_size=1,
        max_size=5,
    ),
)


# ==========================================================================
# PROPERTY 13: CACHE TENANT ISOLATION
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestCacheTenantIsolation:
    """
    Property tests for cache tenant isolation.

    **Feature: django-saas-backend, Property 13: Cache Tenant Isolation**
    **Validates: Requirements 10.1**

    For any cache operation:
    - Keys SHALL be prefixed with tenant ID
    - Different tenants SHALL NOT access each other's data
    """

    @pytest.mark.property
    @given(key=cache_key_strategy)
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_cache_key_contains_tenant_prefix(
        self,
        key: str,
        tenant_factory,
    ):
        """
        Property: Cache keys are prefixed with tenant ID.

        For any cache key and tenant,
        the built key SHALL contain the tenant ID prefix.

        **Validates: Requirement 10.1**
        """
        from apps.core.cache import CacheService
        from apps.core.middleware.tenant import clear_current_tenant, set_current_tenant

        tenant = tenant_factory()
        set_current_tenant(tenant)

        try:
            prefixed_key = CacheService._build_key(key)

            # Key must contain tenant prefix
            assert f"tenant:{tenant.id}:" in prefixed_key
            # Key must end with original key
            assert prefixed_key.endswith(f":{key}")
        finally:
            clear_current_tenant()

    @pytest.mark.property
    @given(key=cache_key_strategy, value=cache_value_strategy)
    @settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_tenant_a_cannot_access_tenant_b_cache(
        self,
        key: str,
        value,
        tenant_factory,
    ):
        """
        Property: Tenants cannot access each other's cached data.

        For any cached value by tenant A,
        tenant B SHALL NOT be able to retrieve it.

        **Validates: Requirement 10.1**
        """
        from apps.core.cache import CacheService
        from apps.core.middleware.tenant import clear_current_tenant, set_current_tenant

        tenant_a = tenant_factory(name="Tenant A", slug=f"tenant-a-{uuid.uuid4().hex[:8]}")
        tenant_b = tenant_factory(name="Tenant B", slug=f"tenant-b-{uuid.uuid4().hex[:8]}")

        try:
            # Set value as tenant A
            set_current_tenant(tenant_a)
            CacheService.set(key, value, timeout=60)

            # Verify tenant A can retrieve it
            retrieved_a = CacheService.get(key)
            assert retrieved_a == value

            # Switch to tenant B
            set_current_tenant(tenant_b)

            # Tenant B should NOT see tenant A's value
            retrieved_b = CacheService.get(key)
            assert retrieved_b is None

        finally:
            clear_current_tenant()

    @pytest.mark.property
    @given(key=cache_key_strategy, value=cache_value_strategy)
    @settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_same_tenant_can_retrieve_cached_value(
        self,
        key: str,
        value,
        tenant_factory,
    ):
        """
        Property: Same tenant can retrieve its cached values.

        For any cached value,
        the same tenant SHALL be able to retrieve it.

        **Validates: Requirement 10.1**
        """
        from apps.core.cache import CacheService
        from apps.core.middleware.tenant import clear_current_tenant, set_current_tenant

        tenant = tenant_factory()
        set_current_tenant(tenant)

        try:
            # Set value
            CacheService.set(key, value, timeout=60)

            # Retrieve value
            retrieved = CacheService.get(key)

            # Should match
            assert retrieved == value

        finally:
            clear_current_tenant()

    @pytest.mark.property
    @given(key=cache_key_strategy)
    @settings(max_examples=30)
    def test_global_key_without_tenant_context(self, key: str):
        """
        Property: Keys without tenant context use global prefix.

        For any cache key without tenant context,
        the key SHALL use 'global:' prefix.

        **Validates: Requirement 10.1**
        """
        from apps.core.cache import CacheService
        from apps.core.middleware.tenant import clear_current_tenant

        clear_current_tenant()

        prefixed_key = CacheService._build_key(key)

        # Key must have global prefix
        assert prefixed_key.startswith("global:")
        assert prefixed_key == f"global:{key}"

    @pytest.mark.property
    @given(key=cache_key_strategy, value=cache_value_strategy)
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_delete_only_affects_tenant_cache(
        self,
        key: str,
        value,
        tenant_factory,
    ):
        """
        Property: Delete only affects the tenant's cache.

        For any delete operation by tenant A,
        tenant B's cache SHALL NOT be affected.

        **Validates: Requirement 10.1**
        """
        from apps.core.cache import CacheService
        from apps.core.middleware.tenant import clear_current_tenant, set_current_tenant

        tenant_a = tenant_factory(name="Tenant A", slug=f"tenant-a-{uuid.uuid4().hex[:8]}")
        tenant_b = tenant_factory(name="Tenant B", slug=f"tenant-b-{uuid.uuid4().hex[:8]}")

        try:
            # Set value for both tenants
            set_current_tenant(tenant_a)
            CacheService.set(key, value, timeout=60)

            set_current_tenant(tenant_b)
            CacheService.set(key, value, timeout=60)

            # Delete tenant A's cache
            set_current_tenant(tenant_a)
            CacheService.delete(key)

            # Tenant A's value should be gone
            assert CacheService.get(key) is None

            # Tenant B's value should still exist
            set_current_tenant(tenant_b)
            assert CacheService.get(key) == value

        finally:
            clear_current_tenant()

    @pytest.mark.property
    @given(
        key=cache_key_strategy,
        tenant_id=st.uuids(),
    )
    @settings(max_examples=50)
    def test_explicit_tenant_id_override(self, key: str, tenant_id: uuid.UUID):
        """
        Property: Explicit tenant_id parameter overrides context.

        For any explicit tenant_id parameter,
        the key SHALL use that tenant ID regardless of context.

        **Validates: Requirement 10.1**
        """
        from apps.core.cache import CacheService

        prefixed_key = CacheService._build_key(key, tenant_id=str(tenant_id))

        assert f"tenant:{tenant_id}:" in prefixed_key
        assert prefixed_key == f"tenant:{tenant_id}:{key}"


# ==========================================================================
# GET_OR_SET TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestCacheGetOrSet:
    """
    Property tests for cache get_or_set operation.
    """

    @pytest.mark.property
    @given(key=cache_key_strategy, value=st.integers(min_value=1, max_value=1000))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_get_or_set_returns_cached_value(
        self,
        key: str,
        value: int,
        tenant_factory,
    ):
        """
        Property: get_or_set returns cached value if exists.

        For any existing cached value,
        get_or_set SHALL return it without calling default.
        """
        from apps.core.cache import CacheService
        from apps.core.middleware.tenant import clear_current_tenant, set_current_tenant

        tenant = tenant_factory()
        set_current_tenant(tenant)

        try:
            # Pre-set value
            CacheService.set(key, value, timeout=60)

            # get_or_set should return cached value
            call_count = 0

            def default_func():
                """A dummy function that should not be called if the cache is hit."""
                nonlocal call_count
                call_count += 1
                return value + 100

            result = CacheService.get_or_set(key, default_func, timeout=60)

            assert result == value
            assert call_count == 0  # Default should not be called

        finally:
            clear_current_tenant()

    @pytest.mark.property
    @given(key=cache_key_strategy, value=st.integers(min_value=1, max_value=1000))
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_get_or_set_computes_and_caches_missing(
        self,
        key: str,
        value: int,
        tenant_factory,
    ):
        """
        Property: get_or_set computes and caches missing values.

        For any missing cache key,
        get_or_set SHALL call default and cache the result.
        """
        from apps.core.cache import CacheService
        from apps.core.middleware.tenant import clear_current_tenant, set_current_tenant

        tenant = tenant_factory()
        set_current_tenant(tenant)

        try:
            # Ensure key doesn't exist
            CacheService.delete(key)

            # get_or_set should compute and cache
            result = CacheService.get_or_set(key, lambda: value, timeout=60)

            assert result == value

            # Value should now be cached
            cached = CacheService.get(key)
            assert cached == value

        finally:
            clear_current_tenant()


# ==========================================================================
# KEY PREFIX TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestCacheKeyPrefix:
    """
    Property tests for cache key prefix generation.
    """

    @pytest.mark.property
    @given(tenant_id=st.uuids())
    @settings(max_examples=50)
    def test_get_key_prefix_format(self, tenant_id: uuid.UUID):
        """
        Property: Key prefix has correct format.

        For any tenant ID,
        the prefix SHALL be 'tenant:{tenant_id}:'.
        """
        from apps.core.cache import CacheService

        prefix = CacheService.get_key_prefix(tenant_id=str(tenant_id))

        assert prefix == f"tenant:{tenant_id}:"
        assert prefix.startswith("tenant:")
        assert prefix.endswith(":")

    @pytest.mark.property
    def test_get_key_prefix_global_without_tenant(self):
        """
        Property: Key prefix is 'global:' without tenant.

        Without tenant context,
        the prefix SHALL be 'global:'.
        """
        from apps.core.cache import CacheService
        from apps.core.middleware.tenant import clear_current_tenant

        clear_current_tenant()

        prefix = CacheService.get_key_prefix()

        assert prefix == "global:"
