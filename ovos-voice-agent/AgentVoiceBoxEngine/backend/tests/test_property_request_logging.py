"""
Property tests for request ID generation.

**Feature: django-saas-backend, Property 15: Request ID Generation**
**Validates: Requirements 11.3**

Tests that:
1. Every request gets unique request_id in X-Request-ID header
2. Provided X-Request-ID is preserved
3. Request ID is set on request object

Uses REAL Django middleware - NO MOCKS.
"""

import uuid

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from hypothesis import given, settings
from hypothesis import strategies as st

# ==========================================================================
# PROPERTY 15: REQUEST ID GENERATION
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestRequestIDGeneration:
    """
    Property tests for request ID generation.

    **Feature: django-saas-backend, Property 15: Request ID Generation**
    **Validates: Requirements 11.3**

    For any HTTP request:
    - Every request SHALL get unique request_id in X-Request-ID header
    """

    @pytest.mark.property
    @given(num_requests=st.integers(min_value=2, max_value=20))
    @settings(max_examples=10)
    def test_each_request_gets_unique_id(self, num_requests: int):
        """
        Property: Each request gets a unique request ID.

        For any number of requests,
        each SHALL receive a unique X-Request-ID.

        **Validates: Requirement 11.3**
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request_ids = set()

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(get_response=get_response)

        for _ in range(num_requests):
            request = factory.get("/api/v2/test/")
            response = middleware(request)

            request_id = response.get("X-Request-ID")
            assert request_id is not None
            assert request_id not in request_ids
            request_ids.add(request_id)

        # All IDs should be unique
        assert len(request_ids) == num_requests

    @pytest.mark.property
    @given(provided_id=st.uuids())
    @settings(max_examples=50)
    def test_provided_request_id_is_preserved(self, provided_id: uuid.UUID):
        """
        Property: Provided X-Request-ID is preserved.

        For any request with X-Request-ID header,
        the middleware SHALL preserve that ID in the response.
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_X_REQUEST_ID=str(provided_id),
        )

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(get_response=get_response)
        response = middleware(request)

        assert response.get("X-Request-ID") == str(provided_id)

    @pytest.mark.property
    @given(
        path=st.sampled_from(
            [
                "/api/v2/projects/",
                "/api/v2/sessions/",
                "/api/v2/billing/usage/",
                "/health/",
                "/metrics",
            ]
        )
    )
    @settings(max_examples=20)
    def test_request_id_set_on_request_object(self, path: str):
        """
        Property: Request ID is set on request object.

        For any request, the middleware SHALL set request_id
        attribute on the request object.
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get(path)

        captured_request_id = None

        def get_response(req):
            nonlocal captured_request_id
            captured_request_id = getattr(req, "request_id", None)
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(get_response=get_response)
        response = middleware(request)

        # Request ID should be set on request object
        assert captured_request_id is not None
        # And should match response header
        assert captured_request_id == response.get("X-Request-ID")

    @pytest.mark.property
    def test_generated_request_id_is_valid_uuid(self):
        """
        Property: Generated request ID is a valid UUID.

        For any request without X-Request-ID,
        the generated ID SHALL be a valid UUID.
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v2/test/")

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(get_response=get_response)
        response = middleware(request)

        request_id = response.get("X-Request-ID")
        assert request_id is not None

        # Should be valid UUID
        try:
            uuid.UUID(request_id)
        except ValueError:
            pytest.fail(f"Request ID '{request_id}' is not a valid UUID")


# ==========================================================================
# CLIENT IP EXTRACTION TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestClientIPExtraction:
    """
    Property tests for client IP extraction.
    """

    @pytest.mark.property
    @given(ip_address=st.ip_addresses(v=4).map(str))
    @settings(max_examples=30)
    def test_x_forwarded_for_extracted(self, ip_address: str):
        """
        Property: X-Forwarded-For header is used for client IP.

        For any request with X-Forwarded-For header,
        the middleware SHALL use that IP.
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_X_FORWARDED_FOR=ip_address,
        )

        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse("OK"))
        extracted_ip = middleware._get_client_ip(request)

        assert extracted_ip == ip_address

    @pytest.mark.property
    @given(
        first_ip=st.ip_addresses(v=4).map(str),
        second_ip=st.ip_addresses(v=4).map(str),
    )
    @settings(max_examples=20)
    def test_first_ip_from_forwarded_chain(self, first_ip: str, second_ip: str):
        """
        Property: First IP from X-Forwarded-For chain is used.

        For any X-Forwarded-For with multiple IPs,
        the middleware SHALL use the first IP.
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get(
            "/api/v2/test/",
            HTTP_X_FORWARDED_FOR=f"{first_ip}, {second_ip}",
        )

        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse("OK"))
        extracted_ip = middleware._get_client_ip(request)

        assert extracted_ip == first_ip

    @pytest.mark.property
    def test_remote_addr_fallback(self):
        """
        Property: REMOTE_ADDR is used as fallback.

        When X-Forwarded-For is not present,
        the middleware SHALL use REMOTE_ADDR.
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v2/test/")
        # RequestFactory sets REMOTE_ADDR to 127.0.0.1 by default

        middleware = RequestLoggingMiddleware(get_response=lambda r: HttpResponse("OK"))
        extracted_ip = middleware._get_client_ip(request)

        assert extracted_ip == "127.0.0.1"


# ==========================================================================
# RESPONSE HEADER TESTS
# ==========================================================================


@pytest.mark.django_db(transaction=True)
class TestResponseHeaders:
    """
    Property tests for response headers.
    """

    @pytest.mark.property
    @given(
        method=st.sampled_from(["GET", "POST", "PUT", "PATCH", "DELETE"]),
        path=st.sampled_from(
            [
                "/api/v2/projects/",
                "/api/v2/sessions/",
                "/api/v2/api-keys/",
            ]
        ),
    )
    @settings(max_examples=30)
    def test_x_request_id_always_in_response(self, method: str, path: str):
        """
        Property: X-Request-ID is always in response.

        For any HTTP method and path,
        the response SHALL include X-Request-ID header.
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request_method = getattr(factory, method.lower())
        request = request_method(path)

        def get_response(req):
            return HttpResponse("OK", status=200)

        middleware = RequestLoggingMiddleware(get_response=get_response)
        response = middleware(request)

        assert "X-Request-ID" in response
        assert response["X-Request-ID"] is not None
        assert len(response["X-Request-ID"]) > 0

    @pytest.mark.property
    @given(status_code=st.sampled_from([200, 201, 400, 401, 403, 404, 500]))
    @settings(max_examples=20)
    def test_x_request_id_present_regardless_of_status(self, status_code: int):
        """
        Property: X-Request-ID present regardless of response status.

        For any response status code,
        the X-Request-ID header SHALL be present.
        """
        from apps.core.middleware.request_logging import RequestLoggingMiddleware

        factory = RequestFactory()
        request = factory.get("/api/v2/test/")

        def get_response(req):
            return HttpResponse("Response", status=status_code)

        middleware = RequestLoggingMiddleware(get_response=get_response)
        response = middleware(request)

        assert "X-Request-ID" in response
        assert response.status_code == status_code
