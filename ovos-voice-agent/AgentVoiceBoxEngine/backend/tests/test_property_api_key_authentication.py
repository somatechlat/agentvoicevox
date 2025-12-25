"""
Property tests for API key authentication.

**Feature: django-saas-backend, Property 6: API Key Authentication**
**Validates: Requirements 3.9, 7.9, 7.10**

Tests that:
1. Valid API keys authenticate successfully
2. Expired keys return 401 with "api_key_expired"
3. Revoked keys return 401 with "api_key_revoked"

Uses REAL Django models and database - NO MOCKS.
"""

import uuid
from datetime import timedelta

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils import timezone
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Valid API key name strategy
name_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "Zs")),
    min_size=1,
    max_size=100,
).filter(lambda x: x.strip())

# Scope strategy
scope_strategy = st.lists(
    st.sampled_from(["realtime", "billing", "admin"]),
    min_size=1,
    max_size=3,
    unique=True,
)


# ==========================================================================
# FIXTURES
# ==========================================================================


@pytest.fixture
def api_key_factory(tenant_factory, user_factory):
    """Factory for creating test API keys."""
    from apps.api_keys.services import APIKeyService

    created_keys = []

    def _create_api_key(
        tenant=None,
        name: str = "Test API Key",
        scopes: list = None,
        expires_in_days: int = None,
        revoked: bool = False,
    ):
        if tenant is None:
            tenant = tenant_factory()

        user = user_factory(tenant=tenant)

        api_key, full_key = APIKeyService.create_key(
            tenant=tenant,
            name=name,
            created_by=user,
            scopes=scopes or ["realtime"],
            expires_in_days=expires_in_days,
        )

        if revoked:
            api_key.revoke(user=user, reason="Test revocation")

        created_keys.append((api_key, full_key))
        return api_key, full_key

    yield _create_api_key

    # Cleanup
    for api_key, _ in created_keys:
        try:
            api_key.delete()
        except Exception:
            pass


@pytest.fixture
def user_factory(db):
    """Factory for creating test users."""
    from apps.users.models import User

    created_users = []

    def _create_user(
        tenant,
        email: str = None,
        keycloak_id: str = None,
    ):
        if email is None:
            email = f"test-{uuid.uuid4().hex[:8]}@example.com"
        if keycloak_id is None:
            keycloak_id = str(uuid.uuid4())

        user = User.objects.create(
            tenant=tenant,
            email=email,
            keycloak_id=keycloak_id,
            first_name="Test",
            last_name="User",
        )
        created_users.append(user)
        return user

    yield _create_user

    # Cleanup
    for user in created_users:
        try:
            user.delete()
        except Exception:
            pass


# ==========================================================================
# PROPERTY 6: API KEY AUTHENTICATION
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestAPIKeyAuthentication:
    """
    Property tests for API key authentication.

    **Feature: django-saas-backend, Property 6: API Key Authentication**
    **Validates: Requirements 3.9, 7.9, 7.10**

    For any API key in the X-API-Key header:
    - Valid keys SHALL authenticate successfully
    - Expired keys SHALL return 401 with "api_key_expired"
    - Revoked keys SHALL return 401 with "api_key_revoked"
    """

    @pytest.mark.property
    @given(scopes=scope_strategy)
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_valid_api_key_authenticates(
        self,
        scopes: list,
        api_key_factory,
    ):
        """
        Property: Valid API keys authenticate successfully.

        For any valid API key with any combination of scopes,
        the middleware SHALL authenticate and set context.

        **Validates: Requirement 3.9**
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        api_key, full_key = api_key_factory(scopes=scopes)

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_X_API_KEY=full_key,
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 200
        assert hasattr(request, "api_key_id")
        assert request.api_key_id == api_key.id
        assert hasattr(request, "jwt_tenant_id")
        assert request.jwt_tenant_id == api_key.tenant_id
        assert request.auth_type == "api_key"

    @pytest.mark.property
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_expired_api_key_returns_401(self, api_key_factory):
        """
        Property: Expired API keys return 401 with "api_key_expired".

        For any API key that has expired,
        the middleware SHALL return 401 with error code "api_key_expired".

        **Validates: Requirement 7.9**
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        # Create key that expires immediately
        api_key, full_key = api_key_factory(expires_in_days=1)

        # Manually set expiration to past
        api_key.expires_at = timezone.now() - timedelta(hours=1)
        api_key.save(update_fields=["expires_at"])

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_X_API_KEY=full_key,
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 401
        assert b"api_key_expired" in response.content

    @pytest.mark.property
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_revoked_api_key_returns_401(self, api_key_factory):
        """
        Property: Revoked API keys return 401 with "api_key_revoked".

        For any API key that has been revoked,
        the middleware SHALL return 401 with error code "api_key_revoked".

        **Validates: Requirement 7.10**
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        # Create and revoke key
        api_key, full_key = api_key_factory(revoked=True)

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_X_API_KEY=full_key,
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 401
        assert b"api_key_revoked" in response.content

    @pytest.mark.property
    @given(
        invalid_key=st.text(min_size=10, max_size=100).filter(
            lambda x: not x.startswith("avb_") or len(x) != 68
        ),
    )
    @settings(max_examples=30)
    def test_invalid_format_api_key_returns_401(self, invalid_key: str):
        """
        Property: Invalid format API keys return 401.

        For any API key that doesn't match the expected format,
        the middleware SHALL return 401 with "invalid_api_key".
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_X_API_KEY=invalid_key,
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 401
        assert b"invalid_api_key" in response.content

    @pytest.mark.property
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_nonexistent_api_key_returns_401(self, tenant_factory):
        """
        Property: Non-existent API keys return 401.

        For any API key that doesn't exist in the database,
        the middleware SHALL return 401 with "invalid_api_key".
        """
        from apps.api_keys.models import APIKey
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        # Generate a valid-looking but non-existent key
        full_key, _, _ = APIKey.generate_key()

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_X_API_KEY=full_key,
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 401
        assert b"invalid_api_key" in response.content


# ==========================================================================
# PROPERTY 7: API KEY LIFECYCLE ROUND-TRIP
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestAPIKeyLifecycle:
    """
    Property tests for API key lifecycle.

    **Feature: django-saas-backend, Property 7: API Key Lifecycle Round-Trip**
    **Validates: Requirements 7.2, 7.3, 7.4, 7.7**

    For any generated API key:
    - Key SHALL match format `avb_{random_32_bytes}`
    - Only SHA-256 hash SHALL be stored
    - Full key SHALL only be returned once at creation
    - Validation SHALL correctly identify valid keys by hash comparison
    """

    @pytest.mark.property
    @given(num_keys=st.integers(min_value=1, max_value=5))
    @settings(max_examples=10)
    def test_key_format_matches_spec(self, num_keys: int):
        """
        Property: Generated keys match format `avb_{random_32_bytes}`.

        For any number of generated keys,
        each key SHALL match the format avb_ followed by 64 hex chars.

        **Validates: Requirement 7.2**
        """
        from apps.api_keys.models import APIKey

        for _ in range(num_keys):
            full_key, prefix, key_hash = APIKey.generate_key()

            # Check format
            assert full_key.startswith("avb_")
            assert len(full_key) == 68  # avb_ (4) + 64 hex chars
            assert prefix == full_key[:12]

            # Verify hex chars after prefix
            hex_part = full_key[4:]
            assert all(c in "0123456789abcdef" for c in hex_part)

    @pytest.mark.property
    @given(num_keys=st.integers(min_value=1, max_value=5))
    @settings(max_examples=10)
    def test_hash_storage_not_full_key(self, num_keys: int):
        """
        Property: Only SHA-256 hash is stored, not full key.

        For any generated key,
        the stored hash SHALL be SHA-256 of the full key.

        **Validates: Requirement 7.3**
        """
        import hashlib

        from apps.api_keys.models import APIKey

        for _ in range(num_keys):
            full_key, prefix, key_hash = APIKey.generate_key()

            # Verify hash is SHA-256
            expected_hash = hashlib.sha256(full_key.encode()).hexdigest()
            assert key_hash == expected_hash
            assert len(key_hash) == 64  # SHA-256 produces 64 hex chars

            # Verify hash is NOT the full key
            assert key_hash != full_key

    @pytest.mark.property
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_full_key_returned_only_once(self, api_key_factory):
        """
        Property: Full key is only returned once at creation.

        After creation, the full key SHALL NOT be retrievable
        from the database.

        **Validates: Requirement 7.4**
        """
        from apps.api_keys.models import APIKey

        api_key, full_key = api_key_factory()

        # Retrieve key from database
        retrieved_key = APIKey.all_objects.get(id=api_key.id)

        # Full key should not be stored
        assert not hasattr(retrieved_key, "full_key")
        assert retrieved_key.key_hash != full_key

        # Only prefix and hash are available
        assert retrieved_key.key_prefix == full_key[:12]
        assert retrieved_key.key_hash == APIKey.hash_key(full_key)

    @pytest.mark.property
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_validation_by_hash_comparison(self, api_key_factory):
        """
        Property: Validation correctly identifies valid keys by hash.

        For any valid key, validation SHALL succeed by comparing
        the hash of the provided key with the stored hash.

        **Validates: Requirement 7.7**
        """
        from apps.api_keys.models import APIKey
        from apps.api_keys.services import APIKeyService

        api_key, full_key = api_key_factory()

        # Validate key
        result = APIKeyService.validate_key(full_key)

        assert result["key_id"] == api_key.id
        assert result["tenant_id"] == api_key.tenant_id

        # Verify hash comparison works
        assert APIKey.hash_key(full_key) == api_key.key_hash

    @pytest.mark.property
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_tampered_key_fails_validation(self, api_key_factory):
        """
        Property: Tampered keys fail validation.

        For any key with modified characters,
        validation SHALL fail due to hash mismatch.
        """
        from apps.api_keys.services import APIKeyService
        from apps.core.exceptions import AuthenticationError

        api_key, full_key = api_key_factory()

        # Tamper with the key (change last character)
        tampered_key = full_key[:-1] + ("a" if full_key[-1] != "a" else "b")

        with pytest.raises(AuthenticationError) as exc_info:
            APIKeyService.validate_key(tampered_key)

        assert exc_info.value.error_code == "invalid_api_key"


# ==========================================================================
# API KEY USAGE TRACKING TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestAPIKeyUsageTracking:
    """
    Property tests for API key usage tracking.

    Tests that usage is correctly recorded on each use.
    """

    @pytest.mark.property
    @given(num_uses=st.integers(min_value=1, max_value=10))
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_usage_count_increments(self, num_uses: int, api_key_factory):
        """
        Property: Usage count increments on each use.

        For any number of API key uses,
        the usage_count SHALL increment accordingly.
        """
        from apps.api_keys.services import APIKeyService

        api_key, full_key = api_key_factory()
        initial_count = api_key.usage_count

        for i in range(num_uses):
            APIKeyService.validate_key(full_key, ip_address="127.0.0.1")

        # Refresh from database
        api_key.refresh_from_db()

        assert api_key.usage_count == initial_count + num_uses

    @pytest.mark.property
    @given(ip_address=st.ip_addresses(v=4).map(str))
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_last_used_ip_recorded(self, ip_address: str, api_key_factory):
        """
        Property: Last used IP is recorded on each use.

        For any IP address used with an API key,
        the last_used_ip SHALL be updated.
        """
        from apps.api_keys.services import APIKeyService

        api_key, full_key = api_key_factory()

        APIKeyService.validate_key(full_key, ip_address=ip_address)

        # Refresh from database
        api_key.refresh_from_db()

        assert api_key.last_used_ip == ip_address
        assert api_key.last_used_at is not None
