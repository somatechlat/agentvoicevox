"""
Property tests for JWT authentication validation.

**Feature: django-saas-backend, Property 5: JWT Authentication Validation**
**Validates: Requirements 3.1, 3.5, 3.6**

Tests that:
1. Valid JWT tokens are accepted and set user context
2. Expired tokens return 401 with "token_expired"
3. Invalid/malformed tokens return 401 with "invalid_token"

Uses REAL JWT encoding/decoding - NO MOCKS for token validation logic.
"""

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from hypothesis import given, settings
from hypothesis import strategies as st

# ==========================================================================
# TEST KEYS FOR JWT SIGNING
# ==========================================================================

# RSA key pair for testing (DO NOT USE IN PRODUCTION)
TEST_PRIVATE_KEY = """-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEA0Z3VS5JJcds3xfn/ygWyF8PbnGy0AHB7MmM2rMHRqWdSpYfE
9HhSBqsHIBdqaJBmkHaJ5sM0h3d3EAi0fZlHLKgZKnPtBgkXwmHLWUVOHEDP4Cek
sIhFjzCnPyQ9Y8P9IQMV5raAzF7xqtc6mnLWnMyBrMTiB8OockFN1Gp5LTcHM1Kn
nFtNLfXkkDvmhMQN0BPnMxrPwEx2MbLCkJRzF1M5xKLYpFlZjPsLmsTrWU3Ah6F2
L5EZFZS6sSgLkkyNSyYQ5xwG5xfnhLMY1FC/1bLrwPM2pTBWN1y5j5Kx5lKrdsNS
nnQfOkgqfDoxHE/0Amxkkr5Bqjm2v8SFEHlpGwIDAQABAoIBAFHMmvPKL9JtCe6z
xU7Kk1VYT0WPgUeqRnVdlnkv0EYP0r6k8h8fTsNAoMr1H7D9ohWLeJ5L8onLLV8N
zsBPQ3L5FvJlybCfCLja2dOANsT0Dj+xLd/rPQeRcO2MKVwK5CtjfLnAtgFXkOXv
UcrznTJTjFmC71Iq3XFQG/I5d0LjWLfsq2F3S98l/phLB7nZxVMVzfGLhCPGqsVs
z5CI3S/qZmH5hJpnKiPBfnpMFqgXXKlUqHPVTLXsLys5pWNfzsBDaiP00kwHq0+t
VHbKT5K3j7vYJrYfmpkHBzlpMhPPklL/yfAUWLWgVBOm5yRfiJMwUa6wkGwsLPF5
PNhBqYECgYEA7Hl+FhvBfv8VqNpglOOqG1P1nuHHDhvLkuE8Ii5eqWqYTYfYdHVr
g8h3DqGmYqjJ4JzRYfYkN5S3L/hRPRRM5VzPknqFrDeNtjwTTfDVfeem4F9hhfGs
WO1z7dXD5mTUkJwGb3sHIbNhKfaP2p5d7f7AxFv0aMoLw0I7B2nnxasCgYEA4wOv
sHOKZNPiGD1l/S1PB8LFTKGqVc8yFn3qTAOw0xP5dLX/V7B5Z5Hj8XnPZAKVcYwR
LhS7OYSQ5L7vphKxqDOyZSlKaMLS3vzVOYFU+lDve9I7A8sHSz3GnQpXwHpYcnBN
kT3PNhJVdJJZ3qB8ONNZ5PbNfG7yrthKkHFMU4ECgYBqBpLAnp5v/hFqYk0DCXMR
Fz8S5KJaOmPvD3HcxqChRRP7hie2F6bpR9DBfaOkHQqLzTMQ7vNFvGbYdRqP0i8D
TiHBmMDg5LMKW6R7F8woSKPvM5xyMGItSx/cPyLIQ9EZmGHY3vCnw8ePqwXmQGdN
1HqS9EAbSjZgDLTBe/DLqwKBgETqMc1n7Wz9Baq3aLz/5vz5VqLwKI8qP5LKCwGV
c5Tb+Kn6thG7fMmUYrUq0/f/dguOv0cPWnaYf0hGwlPVSiRfPqpXpmbkb9SUNLmD
Q7gfqHmMfBQv4icEyxZrHHxgO3TEk2ECvj6ziU+aNGrPmPxJRsH0OfbDoqf9xkP9
xYABAoGBANu0I09UrZ4MYvyX0lqCe9LhMGBP+qYBVNL1PvHkTYf5hXmVqrpgkzLP
dOFsjEcDUnPi7WKv4eDEswTSzPajigHYBfVTmwPfg9I3qdqprxhMk9hVyKFM8s/Y
JCcJPmTrXf0e9F7LBjPKSfq5xHqgYqPVrFqMvKB5b0pkFQPf7FQo
-----END RSA PRIVATE KEY-----"""

TEST_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0Z3VS5JJcds3xfn/ygWy
F8PbnGy0AHB7MmM2rMHRqWdSpYfE9HhSBqsHIBdqaJBmkHaJ5sM0h3d3EAi0fZlH
LKgZKnPtBgkXwmHLWUVOHEDP4CeksIhFjzCnPyQ9Y8P9IQMV5raAzF7xqtc6mnLW
nMyBrMTiB8OockFN1Gp5LTcHM1KnnFtNLfXkkDvmhMQN0BPnMxrPwEx2MbLCkJRz
F1M5xKLYpFlZjPsLmsTrWU3Ah6F2L5EZFZS6sSgLkkyNSyYQ5xwG5xfnhLMY1FC/
1bLrwPM2pTBWN1y5j5Kx5lKrdsNSnnQfOkgqfDoxHE/0Amxkkr5Bqjm2v8SFEHlp
GwIDAQAB
-----END PUBLIC KEY-----"""


# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Valid email strategy
email_strategy = st.emails()

# Valid UUID strategy
uuid_strategy = st.uuids()

# Role strategy
role_strategy = st.lists(
    st.sampled_from(["admin", "developer", "operator", "viewer", "billing"]),
    min_size=0,
    max_size=3,
    unique=True,
)


def create_jwt_token(
    user_id: str,
    tenant_id: str,
    email: str = "test@example.com",
    roles: list = None,
    exp_delta: timedelta = None,
    algorithm: str = "RS256",
    private_key: str = TEST_PRIVATE_KEY,
) -> str:
    """Create a JWT token for testing."""
    now = datetime.now(timezone.utc)
    exp = now + (exp_delta or timedelta(hours=1))

    payload = {
        "sub": user_id,
        "tenant_id": tenant_id,
        "email": email,
        "given_name": "Test",
        "family_name": "User",
        "realm_access": {"roles": roles or []},
        "iat": now,
        "exp": exp,
        "aud": "agentvoicebox",
        "iss": "http://localhost:8080/realms/agentvoicebox",
    }

    return jwt.encode(payload, private_key, algorithm=algorithm)


# ==========================================================================
# PROPERTY 5: JWT AUTHENTICATION VALIDATION
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestJWTAuthenticationValidation:
    """
    Property tests for JWT authentication validation.

    **Feature: django-saas-backend, Property 5: JWT Authentication Validation**
    **Validates: Requirements 3.1, 3.5, 3.6**

    For any JWT token in the Authorization header:
    - Valid tokens SHALL be accepted and set user context
    - Expired tokens SHALL return 401 with "token_expired"
    - Malformed tokens SHALL return 401 with "invalid_token"
    """

    @pytest.fixture(autouse=True)
    def setup_keycloak_mock(self, monkeypatch):
        """Mock Keycloak public key retrieval."""
        from apps.core.middleware import authentication

        # Mock the public key retrieval to return our test key
        monkeypatch.setattr(
            authentication.KeycloakAuthenticationMiddleware,
            "_get_keycloak_public_key",
            lambda self: TEST_PUBLIC_KEY,
        )

    @pytest.mark.property
    @given(
        user_id=uuid_strategy,
        tenant_id=uuid_strategy,
        roles=role_strategy,
    )
    @settings(max_examples=50)
    def test_valid_jwt_sets_user_context(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
        roles: list,
    ):
        """
        Property: Valid JWT tokens set user context on request.

        For any valid JWT token with user_id, tenant_id, and roles,
        the middleware SHALL set these values on the request object.

        **Validates: Requirement 3.1**
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        token = create_jwt_token(
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            roles=roles,
        )

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        # Should succeed
        assert response.status_code == 200

        # User context should be set
        assert hasattr(request, "user_id")
        assert request.user_id == str(user_id)
        assert hasattr(request, "jwt_tenant_id")
        assert request.jwt_tenant_id == str(tenant_id)
        assert hasattr(request, "jwt_roles")
        assert set(request.jwt_roles) == set(roles)
        assert request.auth_type == "jwt"

    @pytest.mark.property
    @given(
        user_id=uuid_strategy,
        tenant_id=uuid_strategy,
    )
    @settings(max_examples=30)
    def test_expired_jwt_returns_401_token_expired(
        self,
        user_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ):
        """
        Property: Expired JWT tokens return 401 with "token_expired".

        For any JWT token that has expired,
        the middleware SHALL return 401 with error code "token_expired".

        **Validates: Requirement 3.5**
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        # Create expired token (expired 1 hour ago)
        token = create_jwt_token(
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            exp_delta=timedelta(hours=-1),
        )

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 401
        assert b"token_expired" in response.content

    @pytest.mark.property
    @given(
        malformed_token=st.text(min_size=10, max_size=100).filter(
            lambda x: "." not in x or x.count(".") != 2
        ),
    )
    @settings(max_examples=30)
    def test_malformed_jwt_returns_401_invalid_token(self, malformed_token: str):
        """
        Property: Malformed JWT tokens return 401 with "invalid_token".

        For any malformed JWT token (wrong structure),
        the middleware SHALL return 401 with error code "invalid_token".

        **Validates: Requirement 3.6**
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_AUTHORIZATION=f"Bearer {malformed_token}",
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 401
        assert b"invalid_token" in response.content

    @pytest.mark.property
    def test_jwt_with_wrong_signature_returns_401(self):
        """
        Property: JWT with wrong signature returns 401 with "invalid_token".

        For any JWT token signed with a different key,
        the middleware SHALL return 401 with error code "invalid_token".

        **Validates: Requirement 3.6**
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        # Create a valid-looking JWT but tamper with the signature
        # This simulates a token signed with a different key
        token = create_jwt_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
        )

        # Tamper with the signature (last part of JWT)
        parts = token.split(".")
        parts[2] = parts[2][::-1]  # Reverse the signature
        tampered_token = ".".join(parts)

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_AUTHORIZATION=f"Bearer {tampered_token}",
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 401
        assert b"invalid_token" in response.content


# ==========================================================================
# AUTH EXEMPT PATH TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestAuthExemptPaths:
    """
    Property tests for authentication-exempt paths.

    Certain paths (health checks, docs, metrics) should NOT require
    authentication.
    """

    @pytest.mark.property
    @given(
        path=st.sampled_from(
            [
                "/health/",
                "/health/ready/",
                "/metrics",
                "/api/v2/docs",
                "/api/v2/openapi.json",
            ]
        )
    )
    @settings(max_examples=10)
    def test_exempt_paths_allow_no_auth(self, path: str):
        """
        Property: Exempt paths allow requests without authentication.

        For any exempt path (health, metrics, docs),
        the middleware SHALL allow the request without auth.
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        factory = RequestFactory()
        request = factory.get(path)

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 200


# ==========================================================================
# JWT CLAIMS EXTRACTION TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestJWTClaimsExtraction:
    """
    Property tests for JWT claims extraction.

    Tests that all relevant claims are correctly extracted from JWT.
    """

    @pytest.fixture(autouse=True)
    def setup_keycloak_mock(self, monkeypatch):
        """Mock Keycloak public key retrieval."""
        from apps.core.middleware import authentication

        monkeypatch.setattr(
            authentication.KeycloakAuthenticationMiddleware,
            "_get_keycloak_public_key",
            lambda self: TEST_PUBLIC_KEY,
        )

    @pytest.mark.property
    @given(
        email=email_strategy,
        first_name=st.text(min_size=1, max_size=50).filter(str.strip),
        last_name=st.text(min_size=1, max_size=50).filter(str.strip),
    )
    @settings(max_examples=20)
    def test_jwt_extracts_user_profile_claims(
        self,
        email: str,
        first_name: str,
        last_name: str,
    ):
        """
        Property: JWT claims include user profile information.

        For any JWT with email, given_name, family_name claims,
        the middleware SHALL extract and make them available.
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        user_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())

        # Create token with profile claims
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_id,
            "tenant_id": tenant_id,
            "email": email,
            "given_name": first_name.strip(),
            "family_name": last_name.strip(),
            "realm_access": {"roles": ["developer"]},
            "iat": now,
            "exp": now + timedelta(hours=1),
            "aud": "agentvoicebox",
            "iss": "http://localhost:8080/realms/agentvoicebox",
        }
        token = jwt.encode(payload, TEST_PRIVATE_KEY, algorithm="RS256")

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 200
        assert hasattr(request, "jwt_claims")
        assert request.jwt_claims.get("email") == email
        assert request.jwt_claims.get("given_name") == first_name.strip()
        assert request.jwt_claims.get("family_name") == last_name.strip()

    @pytest.mark.property
    @given(
        exp_minutes=st.integers(min_value=1, max_value=60),
    )
    @settings(max_examples=10)
    def test_jwt_with_future_expiry_is_valid(self, exp_minutes: int):
        """
        Property: JWT with future expiry is accepted.

        For any JWT that expires in the future,
        the middleware SHALL accept it.
        """
        from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware

        token = create_jwt_token(
            user_id=str(uuid.uuid4()),
            tenant_id=str(uuid.uuid4()),
            exp_delta=timedelta(minutes=exp_minutes),
        )

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/projects/",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = KeycloakAuthenticationMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.status_code == 200
