"""
Property tests for tenant context extraction and isolation.

**Feature: django-saas-backend, Property 2: Tenant Context Extraction**
**Validates: Requirements 2.4**

Tests that tenant context is correctly extracted from:
1. JWT claims (request.jwt_tenant_id)
2. X-Tenant-ID header
3. Subdomain

Uses Django's RequestFactory for REAL HttpRequest objects - NO MOCKS.
"""

import uuid

import pytest
from django.test import RequestFactory
from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Valid subdomain slugs (alphanumeric with hyphens)
slug_strategy = st.from_regex(r"^[a-z][a-z0-9-]{0,30}[a-z0-9]$", fullmatch=True).filter(
    lambda x: "--" not in x and len(x) >= 2
)


def _is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


# ==========================================================================
# PROPERTY 2: TENANT CONTEXT EXTRACTION
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestTenantContextExtraction:
    """
    Property tests for tenant context extraction from requests.

    **Feature: django-saas-backend, Property 2: Tenant Context Extraction**
    **Validates: Requirements 2.4**

    Uses Django RequestFactory for REAL HttpRequest objects.
    """

    @pytest.mark.property
    @given(tenant_uuid=st.uuids())
    @settings(max_examples=100)
    def test_jwt_tenant_id_extraction(self, tenant_uuid: uuid.UUID):
        """
        Property: Valid UUID in JWT claims is correctly extracted.

        For any valid UUID set as request.jwt_tenant_id,
        the middleware SHALL extract and return that UUID.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v2/test/")
        request.jwt_tenant_id = str(tenant_uuid)

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id is not None
        assert extracted_id == tenant_uuid

    @pytest.mark.property
    @given(tenant_uuid=st.uuids())
    @settings(max_examples=100)
    def test_header_tenant_id_extraction(self, tenant_uuid: uuid.UUID):
        """
        Property: Valid UUID in X-Tenant-ID header is correctly extracted.

        For any valid UUID in the X-Tenant-ID header (when JWT is absent),
        the middleware SHALL extract and return that UUID.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_X_TENANT_ID=str(tenant_uuid),
        )

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id is not None
        assert extracted_id == tenant_uuid

    @pytest.mark.property
    @given(jwt_uuid=st.uuids(), header_uuid=st.uuids())
    @settings(max_examples=100)
    def test_jwt_takes_priority_over_header(self, jwt_uuid: uuid.UUID, header_uuid: uuid.UUID):
        """
        Property: JWT tenant ID takes priority over X-Tenant-ID header.

        When both JWT claims and header contain tenant IDs,
        the middleware SHALL use the JWT tenant ID.
        """
        assume(jwt_uuid != header_uuid)

        from apps.core.middleware.tenant import TenantMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_X_TENANT_ID=str(header_uuid),
        )
        request.jwt_tenant_id = str(jwt_uuid)

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id == jwt_uuid
        assert extracted_id != header_uuid

    @pytest.mark.property
    @given(
        invalid_jwt=st.text(min_size=1, max_size=50).filter(
            lambda x: not _is_valid_uuid(x) and x.strip()
        ),
        valid_header=st.uuids(),
    )
    @settings(max_examples=50)
    def test_invalid_jwt_falls_through_to_valid_header(
        self, invalid_jwt: str, valid_header: uuid.UUID
    ):
        """
        Property: Invalid JWT falls through to valid header.

        When JWT contains invalid UUID but header contains valid UUID,
        the middleware SHALL use the header UUID.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_X_TENANT_ID=str(valid_header),
        )
        request.jwt_tenant_id = invalid_jwt

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id == valid_header

    @pytest.mark.property
    def test_two_part_host_skips_subdomain_extraction(self):
        """
        Property: Two-part hosts skip subdomain extraction.

        For hosts with only two parts (e.g., example.com),
        the middleware SHALL NOT attempt subdomain extraction.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v2/test/", HTTP_HOST="example.com")

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id is None

    @pytest.mark.property
    def test_single_part_host_skips_subdomain_extraction(self):
        """
        Property: Single-part hosts skip subdomain extraction.

        For hosts with only one part (e.g., localhost),
        the middleware SHALL NOT attempt subdomain extraction.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v2/test/", HTTP_HOST="localhost")

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id is None

    @pytest.mark.property
    @given(slug=slug_strategy)
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_subdomain_extraction_with_valid_tenant(self, slug: str, tenant_factory):
        """
        Property: Valid subdomain with existing tenant extracts tenant ID.

        For any valid subdomain slug that matches an existing tenant,
        the middleware SHALL extract and return that tenant's ID.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        tenant = tenant_factory(slug=slug)
        
        # Use the actual tenant slug (which includes UUID suffix)
        actual_slug = tenant.slug

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_HOST=f"{actual_slug}.example.com",
        )

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id is not None
        assert extracted_id == tenant.id

    @pytest.mark.property
    @given(slug=slug_strategy)
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_subdomain_nonexistent_tenant_returns_none(self, slug: str):
        """
        Property: Subdomain with non-existent tenant returns None.

        For any subdomain slug that does not match an existing tenant,
        the middleware SHALL return None.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_HOST=f"{slug}.example.com",
        )

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id is None

    @pytest.mark.property
    @given(jwt_uuid=st.uuids(), slug=slug_strategy)
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_jwt_takes_priority_over_subdomain(
        self, jwt_uuid: uuid.UUID, slug: str, tenant_factory
    ):
        """
        Property: JWT tenant ID takes priority over subdomain.

        When both JWT claims and subdomain contain tenant IDs,
        the middleware SHALL use the JWT tenant ID.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        tenant = tenant_factory(slug=slug)
        assume(jwt_uuid != tenant.id)

        # Use the actual tenant slug (which includes UUID suffix)
        actual_slug = tenant.slug

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_HOST=f"{actual_slug}.example.com",
        )
        request.jwt_tenant_id = str(jwt_uuid)

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id == jwt_uuid
        assert extracted_id != tenant.id

    @pytest.mark.property
    @given(header_uuid=st.uuids(), slug=slug_strategy)
    @settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_header_takes_priority_over_subdomain(
        self, header_uuid: uuid.UUID, slug: str, tenant_factory
    ):
        """
        Property: X-Tenant-ID header takes priority over subdomain.

        When both header and subdomain contain tenant IDs,
        the middleware SHALL use the header tenant ID.
        """
        from apps.core.middleware.tenant import TenantMiddleware

        tenant = tenant_factory(slug=slug)
        assume(header_uuid != tenant.id)

        # Use the actual tenant slug (which includes UUID suffix)
        actual_slug = tenant.slug

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_HOST=f"{actual_slug}.example.com",
            HTTP_X_TENANT_ID=str(header_uuid),
        )

        middleware = TenantMiddleware(get_response=lambda r: r)
        extracted_id = middleware._extract_tenant_id(request)

        assert extracted_id == header_uuid
        assert extracted_id != tenant.id


# ==========================================================================
# THREAD-LOCAL STORAGE TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestTenantThreadLocalStorage:
    """
    Property tests for tenant thread-local storage operations.

    Uses REAL Tenant objects from the database.
    """

    @pytest.mark.property
    def test_set_and_get_tenant(self, tenant_factory):
        """
        Property: Setting tenant makes it retrievable via get_current_tenant.
        """
        from apps.core.middleware.tenant import (
            clear_current_tenant,
            get_current_tenant,
            set_current_tenant,
        )

        tenant = tenant_factory()
        clear_current_tenant()

        set_current_tenant(tenant)
        retrieved = get_current_tenant()

        assert retrieved is not None
        assert retrieved.id == tenant.id

    @pytest.mark.property
    def test_set_and_get_tenant_id(self, tenant_factory):
        """
        Property: Setting tenant makes tenant_id retrievable.
        """
        from apps.core.middleware.tenant import (
            clear_current_tenant,
            get_current_tenant_id,
            set_current_tenant,
        )

        tenant = tenant_factory()
        clear_current_tenant()

        set_current_tenant(tenant)
        retrieved_id = get_current_tenant_id()

        assert retrieved_id is not None
        assert retrieved_id == tenant.id

    @pytest.mark.property
    def test_clear_tenant_removes_context(self, tenant_factory):
        """
        Property: Clearing tenant removes it from thread-local storage.
        """
        from apps.core.middleware.tenant import (
            clear_current_tenant,
            get_current_tenant,
            get_current_tenant_id,
            set_current_tenant,
        )

        tenant = tenant_factory()
        set_current_tenant(tenant)
        clear_current_tenant()

        assert get_current_tenant() is None
        assert get_current_tenant_id() is None

    @pytest.mark.property
    @given(tenant_uuid=st.uuids())
    @settings(max_examples=50)
    def test_set_tenant_id_directly(self, tenant_uuid: uuid.UUID):
        """
        Property: Setting tenant ID directly stores it correctly.
        """
        from apps.core.middleware.tenant import (
            clear_current_tenant,
            get_current_tenant_id,
            set_current_tenant_id,
        )

        clear_current_tenant()
        set_current_tenant_id(tenant_uuid)

        retrieved_id = get_current_tenant_id()
        assert retrieved_id == tenant_uuid

    @pytest.mark.property
    def test_set_none_tenant_clears_context(self):
        """
        Property: Setting None tenant clears the context.
        """
        from apps.core.middleware.tenant import (
            get_current_tenant,
            get_current_tenant_id,
            set_current_tenant,
        )

        set_current_tenant(None)

        assert get_current_tenant() is None
        assert get_current_tenant_id() is None
