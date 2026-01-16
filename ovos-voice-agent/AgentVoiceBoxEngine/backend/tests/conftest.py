"""
Pytest configuration and fixtures for Django backend tests.

Provides:
- Django test database setup
- Hypothesis settings for property-based testing with Django extension
- Common fixtures for tenants, users, and API keys

Uses hypothesis.extra.django for Django-specific property testing:
- from_model() for generating valid model instances
- TestCase for per-example transaction isolation
"""

import os
import uuid

import django
import pytest
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings

# Set Django settings module before importing Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.testing")
os.environ["TESTING"] = "true"

django.setup()

from django.test import Client, RequestFactory  # noqa: E402

# Import Django-specific Hypothesis extension
from hypothesis.extra.django import from_model  # noqa: E402

from apps.core.middleware.tenant import (  # noqa: E402
    clear_current_tenant,
    set_current_tenant,
)
from apps.tenants.models import Tenant, TenantSettings  # noqa: E402

# ==========================================================================
# HYPOTHESIS CONFIGURATION (Django-specific)
# ==========================================================================
# Configure Hypothesis for property-based testing with Django extension
# Profiles optimized for 16-core machine with 64GB RAM
#
# Development profile: Fast feedback (30 examples, 3s deadline)
# CI profile: Thorough testing (100 examples, 10s deadline)
# Full profile: Maximum coverage (200 examples, 30s deadline)
#
# Usage:
#   HYPOTHESIS_PROFILE=dev pytest tests/  # Fast development
#   HYPOTHESIS_PROFILE=ci pytest tests/   # CI pipeline
#   HYPOTHESIS_PROFILE=full pytest tests/ # Full coverage

hypothesis_settings.register_profile(
    "dev",
    max_examples=30,  # Fast feedback for development
    deadline=3000,  # 3 seconds
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.function_scoped_fixture,
        HealthCheck.data_too_large,
    ],
    database=None,  # Don't persist examples in dev mode
)
hypothesis_settings.register_profile(
    "default",
    max_examples=50,  # Balanced for local testing
    deadline=5000,  # 5 seconds
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
hypothesis_settings.register_profile(
    "ci",
    max_examples=100,  # Thorough for CI
    deadline=10000,  # 10 seconds for CI
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
hypothesis_settings.register_profile(
    "full",
    max_examples=200,  # Maximum coverage
    deadline=30000,  # 30 seconds
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
# Default to 'dev' profile for fast local development
hypothesis_settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


# ==========================================================================
# PYTEST-DJANGO CONFIGURATION
# ==========================================================================
# Use transaction-based test isolation for parallel execution
# Each test runs in its own transaction that gets rolled back


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Configure Django test database for parallel execution.
    
    pytest-django handles database creation and migration automatically.
    We just hook into the setup to ensure specific settings if needed.
    """
    with django_db_blocker.unblock():
        pass  # Rely on pytest-django's native test DB management


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all tests by default."""
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
        """
        Creates and returns a single Tenant instance with its settings.

        Args:
            name: The name of the tenant.
            slug: The unique slug for the tenant. If None, a unique one is generated.
            tier: The subscription tier of the tenant.
            status: The lifecycle status of the tenant.

        Returns:
            The newly created Tenant instance.
        """
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


# ==========================================================================
# HYPOTHESIS DJANGO MODEL STRATEGIES
# ==========================================================================
# Pre-configured strategies for generating valid Django model instances
# using hypothesis.extra.django.from_model()

from hypothesis import strategies as st  # noqa: E402


def tenant_strategy(
    tier: str = None,
    status: str = None,
):
    """
    Strategy for generating valid Tenant instances.

    Uses hypothesis.extra.django.from_model() for Django-specific model generation.
    Respects field validators and generates valid instances.

    Args:
        tier: Optional fixed tier value, or generates random valid tier
        status: Optional fixed status value, or generates random valid status

    Returns:
        Hypothesis strategy that generates Tenant instances
    """
    tier_strategy = (
        st.just(tier)
        if tier
        else st.sampled_from(["free", "starter", "pro", "enterprise"])
    )
    status_strategy = (
        st.just(status)
        if status
        else st.sampled_from(["active", "suspended", "pending"])
    )

    return from_model(
        Tenant,
        name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
        slug=st.from_regex(r"^[a-z][a-z0-9-]{2,30}[a-z0-9]$", fullmatch=True).filter(
            lambda x: "--" not in x
        ),
        tier=tier_strategy,
        status=status_strategy,
    )


def active_tenant_strategy():
    """Strategy for generating active tenants only."""
    return tenant_strategy(status="active")


def suspended_tenant_strategy():
    """Strategy for generating suspended tenants only."""
    return tenant_strategy(status="suspended")
