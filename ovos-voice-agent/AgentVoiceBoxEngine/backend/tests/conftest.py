"""
Pytest configuration and fixtures for Django backend tests.

Provides:
- Django test database setup
- Hypothesis settings for property-based testing
- Common fixtures for tenants, users, and API keys
"""
import os
import uuid

import django
import pytest
from hypothesis import HealthCheck, settings as hypothesis_settings

# Set Django settings module before importing Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")
os.environ["TESTING"] = "true"

django.setup()

from apps.core.middleware.tenant import (  # noqa: E402
    clear_current_tenant,
    set_current_tenant,
)
from apps.tenants.models import Tenant, TenantSettings  # noqa: E402
from django.test import Client, RequestFactory  # noqa: E402


# ==========================================================================
# HYPOTHESIS CONFIGURATION
# ==========================================================================
# Configure Hypothesis for property-based testing
# Minimum 100 iterations per property test as per design spec
hypothesis_settings.register_profile(
    "default",
    max_examples=100,
    deadline=5000,  # 5 seconds
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
hypothesis_settings.register_profile(
    "ci",
    max_examples=200,
    deadline=10000,  # 10 seconds for CI
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
hypothesis_settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "default"))


# ==========================================================================
# PYTEST-DJANGO CONFIGURATION
# ==========================================================================
# Use transaction-based test isolation (no database flush between tests)
@pytest.fixture(scope="session")
def django_db_setup():
    """Configure Django test database - use existing database."""
    pass


@pytest.fixture(scope="session")
def django_db_modify_db_settings():
    """Don't modify database settings."""
    pass


@pytest.fixture(autouse=True)
def clear_tenant_context():
    """Clear tenant context before and after each test."""
    clear_current_tenant()
    yield
    clear_current_tenant()


# ==========================================================================
# TENANT FIXTURES
# ==========================================================================
@pytest.fixture
def tenant_factory(db):
    """Factory for creating test tenants."""
    created_tenants = []

    def _create_tenant(
        name: str = "Test Tenant",
        slug: str = None,
        tier: str = "free",
        status: str = "active",
    ) -> Tenant:
        if slug is None:
            slug = f"test-tenant-{uuid.uuid4().hex[:8]}"
        else:
            # Ensure slug is unique by appending UUID suffix
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"

        tenant = Tenant.objects.create(
            name=name,
            slug=slug,
            tier=tier,
            status=status,
        )
        TenantSettings.objects.create(tenant=tenant)
        created_tenants.append(tenant)
        return tenant

    yield _create_tenant

    # Cleanup
    for tenant in created_tenants:
        try:
            tenant.delete()
        except Exception:
            pass


@pytest.fixture
def sample_tenant(tenant_factory) -> Tenant:
    """Create a sample active tenant for testing."""
    return tenant_factory(
        name="Sample Tenant",
        slug=f"sample-{uuid.uuid4().hex[:8]}",
        tier="pro",
        status="active",
    )


@pytest.fixture
def suspended_tenant(tenant_factory) -> Tenant:
    """Create a suspended tenant for testing."""
    return tenant_factory(
        name="Suspended Tenant",
        slug=f"suspended-{uuid.uuid4().hex[:8]}",
        tier="free",
        status="suspended",
    )


@pytest.fixture
def tenant_context(sample_tenant):
    """Set up tenant context for the test."""
    set_current_tenant(sample_tenant)
    yield sample_tenant
    clear_current_tenant()


# ==========================================================================
# HTTP CLIENT FIXTURES
# ==========================================================================
@pytest.fixture
def client() -> Client:
    """Django test client."""
    return Client()


@pytest.fixture
def request_factory() -> RequestFactory:
    """Django request factory for unit testing views."""
    return RequestFactory()


# ==========================================================================
# UTILITY FUNCTIONS
# ==========================================================================
def make_request_with_tenant(
    request_factory: RequestFactory,
    tenant: Tenant,
    method: str = "GET",
    path: str = "/",
    **kwargs,
):
    """Create a request with tenant context."""
    factory_method = getattr(request_factory, method.lower())
    request = factory_method(path, **kwargs)
    request.tenant = tenant
    request.tenant_id = tenant.id
    return request
