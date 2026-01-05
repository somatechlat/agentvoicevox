"""
Property tests for rate limiting enforcement.

**Feature: django-saas-backend, Property 14: Rate Limiting Enforcement**
**Validates: Requirements 10.7**

Tests that:
1. Exceeded rate limits return 429 Too Many Requests
2. Rate limit headers are present: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
3. Response includes retry_after value
4. Different rate limit tiers are enforced correctly

Uses REAL Django middleware and Redis cache - NO MOCKS.
"""

import time
import uuid

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory
from hypothesis import HealthCheck, given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# IP address strategy (valid IPv4)
ip_address_strategy = st.tuples(
    st.integers(min_value=1, max_value=254),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=0, max_value=255),
    st.integers(min_value=1, max_value=254),
).map(lambda t: f"{t[0]}.{t[1]}.{t[2]}.{t[3]}")

# User ID strategy
user_id_strategy = st.uuids()

# API key ID strategy
api_key_id_strategy = st.uuids()


# ==========================================================================
# HELPER FUNCTIONS
# ==========================================================================


def create_request_with_context(
    request_factory: RequestFactory,
    path: str = "/api/v2/test/",
    method: str = "GET",
    client_ip: str = "127.0.0.1",
    user_id: str | None = None,
    api_key_id: str | None = None,
    jwt_roles: list | None = None,
) -> HttpRequest:
    """Create a request with optional authentication context."""
    factory_method = getattr(request_factory, method.lower())
    request = factory_method(path)
    request.META["REMOTE_ADDR"] = client_ip

    if user_id is not None:
        request.user_id = user_id
    if api_key_id is not None:
        request.api_key_id = api_key_id
    if jwt_roles is not None:
        request.jwt_roles = jwt_roles

    return request


def clear_rate_limit_cache() -> None:
    """Clear rate limit cache entries for testing."""
    from django.core.cache import cache

    cache.clear()


# ==========================================================================
# PROPERTY 14: RATE LIMITING ENFORCEMENT
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestRateLimitingEnforcement:
    """
    Property tests for rate limiting enforcement.

    **Feature: django-saas-backend, Property 14: Rate Limiting Enforcement**
    **Validates: Requirements 10.7**

    For any request that exceeds the rate limit:
    - The system SHALL return 429 Too Many Requests
    - The response SHALL include X-RateLimit-* headers
    - The response SHALL include retry_after value
    """

    @pytest.fixture(autouse=True)
    def setup_rate_limits(self):
        """Ensure rate limits are configured for testing."""
        clear_rate_limit_cache()
        yield
        clear_rate_limit_cache()

    @pytest.mark.property
    @given(client_ip=ip_address_strategy)
    @hypothesis_settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_rate_limit_headers_present_on_all_responses(
        self,
        client_ip: str,
        request_factory: RequestFactory,
    ):
        """
        Property: All responses include rate limit headers.

        For any request,
        the response SHALL include X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset.

        **Validates: Requirement 10.6**
        """
        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)
        request = create_request_with_context(request_factory, client_ip=client_ip)
        response = middleware(request)

        assert "X-RateLimit-Limit" in response
        assert "X-RateLimit-Remaining" in response
        assert "X-RateLimit-Reset" in response
        assert response["X-RateLimit-Limit"].isdigit()
        assert response["X-RateLimit-Remaining"].isdigit()
        assert response["X-RateLimit-Reset"].isdigit()

    @pytest.mark.property
    def test_exceeded_rate_limit_returns_429(self, request_factory: RequestFactory):
        """
        Property: Exceeded rate limits return 429 Too Many Requests.

        For any request that exceeds the rate limit,
        the system SHALL return 429 with retry_after.

        **Validates: Requirement 10.7**
        """
        from django.conf import settings

        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)
        client_ip = f"192.168.1.{uuid.uuid4().int % 254 + 1}"
        rate_limit = settings.RATE_LIMITS["DEFAULT"]

        # Make requests up to the limit
        for i in range(rate_limit):
            request = create_request_with_context(request_factory, client_ip=client_ip)
            response = middleware(request)
            assert response.status_code == 200

        # Next request should be rate limited
        request = create_request_with_context(request_factory, client_ip=client_ip)
        response = middleware(request)

        assert response.status_code == 429
        assert "X-RateLimit-Limit" in response
        assert response["X-RateLimit-Remaining"] == "0"

        # Verify response body contains retry_after
        import json

        body = json.loads(response.content)
        assert body["error"] == "rate_limit_exceeded"
        assert "retry_after" in body["details"]
        assert isinstance(body["details"]["retry_after"], int)

    @pytest.mark.property
    @given(user_id=user_id_strategy)
    @hypothesis_settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_authenticated_user_rate_limit_key(
        self,
        user_id: uuid.UUID,
        request_factory: RequestFactory,
    ):
        """
        Property: Authenticated users are rate limited by user ID.

        For any authenticated user,
        the rate limit key SHALL be based on user_id.

        **Validates: Requirement 10.5**
        """
        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)
        request = create_request_with_context(
            request_factory,
            user_id=str(user_id),
            client_ip="10.0.0.1",
        )

        key, limit = middleware._get_rate_limit_params(request)

        assert f"ratelimit:user:{user_id}" == key
        assert limit > 0

    @pytest.mark.property
    @given(api_key_id=api_key_id_strategy)
    @hypothesis_settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_api_key_rate_limit_key(
        self,
        api_key_id: uuid.UUID,
        request_factory: RequestFactory,
    ):
        """
        Property: API key requests are rate limited by API key ID.

        For any API key request,
        the rate limit key SHALL be based on api_key_id.

        **Validates: Requirement 10.5**
        """
        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)
        request = create_request_with_context(
            request_factory,
            api_key_id=str(api_key_id),
            client_ip="10.0.0.1",
        )

        key, limit = middleware._get_rate_limit_params(request)

        assert f"ratelimit:apikey:{api_key_id}" == key

    @pytest.mark.property
    @given(client_ip=ip_address_strategy)
    @hypothesis_settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_unauthenticated_rate_limit_by_ip(
        self,
        client_ip: str,
        request_factory: RequestFactory,
    ):
        """
        Property: Unauthenticated requests are rate limited by IP.

        For any unauthenticated request,
        the rate limit key SHALL be based on client IP.

        **Validates: Requirement 10.5**
        """
        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)
        request = create_request_with_context(request_factory, client_ip=client_ip)

        key, limit = middleware._get_rate_limit_params(request)

        assert f"ratelimit:ip:{client_ip}" == key

    @pytest.mark.property
    @given(user_id=user_id_strategy)
    @hypothesis_settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_admin_users_get_higher_rate_limit(
        self,
        user_id: uuid.UUID,
        request_factory: RequestFactory,
    ):
        """
        Property: Admin users get higher rate limits.

        For any admin user,
        the rate limit SHALL be higher than default.

        **Validates: Requirement 10.8**
        """
        from django.conf import settings

        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)

        # Regular user request
        regular_request = create_request_with_context(
            request_factory,
            user_id=str(user_id),
            client_ip="10.0.0.1",
        )
        _, regular_limit = middleware._get_rate_limit_params(regular_request)

        # Admin user request
        admin_request = create_request_with_context(
            request_factory,
            user_id=str(user_id),
            jwt_roles=["admin"],
            client_ip="10.0.0.1",
        )
        _, admin_limit = middleware._get_rate_limit_params(admin_request)

        assert admin_limit > regular_limit
        assert admin_limit == settings.RATE_LIMITS["ADMIN"]

    @pytest.mark.property
    def test_rate_limit_remaining_decrements(self, request_factory: RequestFactory):
        """
        Property: Rate limit remaining decrements with each request.

        For any sequence of requests,
        X-RateLimit-Remaining SHALL decrement by 1 per request.

        **Validates: Requirement 10.6**
        """
        from django.conf import settings

        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)
        client_ip = f"172.16.0.{uuid.uuid4().int % 254 + 1}"
        rate_limit = settings.RATE_LIMITS["DEFAULT"]

        previous_remaining = None
        for i in range(min(5, rate_limit)):
            request = create_request_with_context(request_factory, client_ip=client_ip)
            response = middleware(request)

            current_remaining = int(response["X-RateLimit-Remaining"])

            if previous_remaining is not None:
                assert current_remaining == previous_remaining - 1

            previous_remaining = current_remaining

    @pytest.mark.property
    def test_rate_limit_reset_is_future_timestamp(self, request_factory: RequestFactory):
        """
        Property: Rate limit reset is a future timestamp.

        For any request,
        X-RateLimit-Reset SHALL be a timestamp in the future.

        **Validates: Requirement 10.6**
        """
        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)
        client_ip = f"10.10.0.{uuid.uuid4().int % 254 + 1}"

        request = create_request_with_context(request_factory, client_ip=client_ip)
        response = middleware(request)

        reset_time = int(response["X-RateLimit-Reset"])
        current_time = int(time.time())

        assert reset_time >= current_time


# ==========================================================================
# RATE LIMIT TIER TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestRateLimitTiers:
    """
    Property tests for rate limit tier enforcement.
    """

    @pytest.fixture(autouse=True)
    def setup_rate_limits(self):
        """Clear cache before and after tests."""
        clear_rate_limit_cache()
        yield
        clear_rate_limit_cache()

    @pytest.mark.property
    def test_api_key_tier_has_elevated_limit(self, request_factory: RequestFactory):
        """
        Property: API key tier has elevated rate limit.

        For any API key request,
        the rate limit SHALL be API_KEY tier (120/min).

        **Validates: Requirement 10.8**
        """
        from django.conf import settings

        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)
        api_key_id = str(uuid.uuid4())

        request = create_request_with_context(
            request_factory,
            api_key_id=api_key_id,
            client_ip="10.0.0.1",
        )

        _, limit = middleware._get_rate_limit_params(request)

        assert limit == settings.RATE_LIMITS["API_KEY"]
        assert limit > settings.RATE_LIMITS["DEFAULT"]


# ==========================================================================
# X-FORWARDED-FOR TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestXForwardedFor:
    """
    Property tests for X-Forwarded-For header handling.
    """

    @pytest.mark.property
    @given(client_ip=ip_address_strategy)
    @hypothesis_settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_x_forwarded_for_extracts_first_ip(
        self,
        client_ip: str,
        request_factory: RequestFactory,
    ):
        """
        Property: X-Forwarded-For extracts first IP address.

        For any X-Forwarded-For header with multiple IPs,
        the system SHALL use the first IP for rate limiting.

        **Validates: Requirement 10.5**
        """
        from apps.core.middleware.rate_limit import RateLimitMiddleware

        def get_response(request: HttpRequest) -> HttpResponse:
            """A dummy response handler for middleware tests."""
            return HttpResponse("OK", status=200)

        middleware = RateLimitMiddleware(get_response)

        request = request_factory.get("/api/v2/test/")
        request.META["HTTP_X_FORWARDED_FOR"] = f"{client_ip}, 10.0.0.1, 192.168.1.1"
        request.META["REMOTE_ADDR"] = "127.0.0.1"

        extracted_ip = middleware._get_client_ip(request)

        assert extracted_ip == client_ip
