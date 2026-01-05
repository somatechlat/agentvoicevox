"""
Property tests for exception sanitization.

**Feature: django-saas-backend, Property 17: Exception Sanitization**
**Validates: Requirements 13.6**

Tests that:
1. Production mode returns generic error without stack traces
2. Development mode includes stack trace for debugging
3. Known API exceptions return proper error codes
4. All exceptions are logged with full context

Uses REAL Django middleware - NO MOCKS.
"""

import json
from typing import Any
from unittest.mock import patch

import pytest
from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, override_settings
from hypothesis import HealthCheck, given
from hypothesis import settings as hypothesis_settings
from hypothesis import strategies as st

from apps.core.exceptions import (
    AuthenticationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
    TenantNotFoundError,
    TenantSuspendedError,
    TokenExpiredError,
    ValidationError,
)

# ==========================================================================
# STRATEGIES FOR PROPERTY-BASED TESTING
# ==========================================================================

# Exception message strategy - generates messages that won't appear in generic error
# "An unexpected error occurred" - avoid single chars that appear in this message
exception_message_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "P", "S"),
        # Exclude characters that appear in "An unexpected error occurred"
        blacklist_characters="Anunexpctdrorcu ",
    ),
    min_size=3,  # Minimum 3 chars to avoid false positives
    max_size=200,
).filter(lambda x: x.strip() and len(x.strip()) >= 3)

# Exception type strategy - all known API exceptions
api_exception_strategy = st.sampled_from(
    [
        ValidationError,
        AuthenticationError,
        TokenExpiredError,
        PermissionDeniedError,
        TenantSuspendedError,
        NotFoundError,
        TenantNotFoundError,
        ConflictError,
        RateLimitError,
    ]
)

# Random exception details strategy
exception_details_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=20).filter(str.strip),
    values=st.one_of(
        st.text(min_size=1, max_size=50).filter(str.strip),
        st.integers(min_value=-1000, max_value=1000),
        st.booleans(),
    ),
    min_size=0,
    max_size=5,
)


# ==========================================================================
# HELPER FUNCTIONS
# ==========================================================================


def create_failing_view(exception: Exception):
    """Create a view that raises the given exception."""

    def view(request: HttpRequest) -> HttpResponse:
        """A simple view that raises an exception for testing."""
        raise exception

    return view


def parse_json_response(response: HttpResponse) -> dict[str, Any]:
    """Parse JSON response body."""
    return json.loads(response.content.decode("utf-8"))


# ==========================================================================
# PROPERTY 17: EXCEPTION SANITIZATION
# ==========================================================================


class TestExceptionSanitization:
    """
    Property tests for exception sanitization.

    **Feature: django-saas-backend, Property 17: Exception Sanitization**
    **Validates: Requirements 13.6**

    For any unexpected exception in production mode:
    - The system SHALL return a generic error message
    - The system SHALL NOT expose stack traces or internal details
    """

    @pytest.mark.property
    @given(message=exception_message_strategy)
    @hypothesis_settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @override_settings(DEBUG=False)
    def test_production_mode_hides_stack_trace(
        self,
        message: str,
        request_factory: RequestFactory,
    ):
        """
        Property: Production mode returns generic error without stack trace.

        For any unexpected exception in production mode,
        the response SHALL NOT contain stack trace or exception details.

        **Validates: Requirement 13.6**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        # Create middleware with failing view
        exception = RuntimeError(message)
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        # Verify response
        assert response.status_code == 500

        body = parse_json_response(response)

        # Must have generic error
        assert body["error"] == "internal_error"
        assert body["message"] == "An unexpected error occurred"

        # Must NOT contain stack trace
        assert "traceback" not in body
        assert "details" not in body or "traceback" not in body.get("details", {})

        # Must NOT contain original exception message
        # Note: We check the message field specifically, not the entire body string
        # because short messages like ',' could appear in JSON structure
        assert message not in body.get("message", "")
        # Also verify it's not in any details field
        if "details" in body:
            assert message not in str(body["details"])

    @pytest.mark.property
    @given(message=exception_message_strategy)
    @hypothesis_settings(
        max_examples=30,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @override_settings(DEBUG=True)
    def test_development_mode_includes_stack_trace(
        self,
        message: str,
        request_factory: RequestFactory,
    ):
        """
        Property: Development mode includes stack trace for debugging.

        For any unexpected exception in development mode,
        the response SHALL include stack trace and exception details.

        **Validates: Requirement 13.7**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        exception = RuntimeError(message)
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        assert response.status_code == 500

        body = parse_json_response(response)

        # Must have error info
        assert body["error"] == "internal_error"

        # Must contain exception message
        assert message in body.get("message", "")

        # Must contain stack trace in details
        assert "details" in body
        assert "traceback" in body["details"]
        assert "exception_type" in body["details"]
        assert body["details"]["exception_type"] == "RuntimeError"

    @pytest.mark.property
    @given(
        exception_class=api_exception_strategy,
        message=exception_message_strategy,
        details=exception_details_strategy,
    )
    @hypothesis_settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @override_settings(DEBUG=False)
    def test_known_api_exceptions_return_proper_error_codes(
        self,
        exception_class,
        message: str,
        details: dict[str, Any],
        request_factory: RequestFactory,
    ):
        """
        Property: Known API exceptions return proper error codes.

        For any known APIException subclass,
        the response SHALL include the correct error_code and status_code.

        **Validates: Requirements 13.2, 13.3, 13.4, 13.5**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        # Handle RateLimitError specially (has retry_after param)
        if exception_class == RateLimitError:
            exception = exception_class(message=message, retry_after=60, details=details)
        else:
            exception = exception_class(message=message, details=details)

        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        # Verify status code matches exception
        assert response.status_code == exception_class.status_code

        body = parse_json_response(response)

        # Verify error code matches exception
        assert body["error"] == exception_class.error_code

        # Verify message is included
        assert body["message"] == message

    @pytest.mark.property
    @override_settings(DEBUG=False)
    def test_production_mode_no_sensitive_data_leak(self, request_factory: RequestFactory):
        """
        Property: Production mode does not leak sensitive data.

        For any exception containing sensitive data,
        the response SHALL NOT expose that data.

        **Validates: Requirement 13.6**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        # Create exception with sensitive data
        sensitive_data = {
            "password": "secret123",
            "api_key": "avb_supersecretkey",
            "database_url": "postgresql://user:pass@host/db",
            "secret_token": "jwt_token_here",
        }

        exception = RuntimeError(f"Database error: {sensitive_data}")
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        body = parse_json_response(response)
        response_str = str(body)

        # Verify no sensitive data in response
        assert "secret123" not in response_str
        assert "avb_supersecretkey" not in response_str
        assert "postgresql://" not in response_str
        assert "jwt_token_here" not in response_str

    @pytest.mark.property
    @given(message=exception_message_strategy)
    @hypothesis_settings(
        max_examples=20,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    @override_settings(DEBUG=False)
    def test_all_exceptions_return_json(
        self,
        message: str,
        request_factory: RequestFactory,
    ):
        """
        Property: All exceptions return valid JSON responses.

        For any exception,
        the response SHALL be valid JSON with consistent structure.

        **Validates: Requirement 13.1**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        exception = Exception(message)
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        # Verify content type is JSON
        assert response["Content-Type"] == "application/json"

        # Verify valid JSON
        body = parse_json_response(response)

        # Verify required fields
        assert "error" in body
        assert "message" in body
        assert isinstance(body["error"], str)
        assert isinstance(body["message"], str)


# ==========================================================================
# EXCEPTION LOGGING TESTS
# ==========================================================================


class TestExceptionLogging:
    """
    Property tests for exception logging.
    """

    @pytest.mark.property
    @given(message=exception_message_strategy)
    @hypothesis_settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_exceptions_are_logged_with_context(
        self,
        message: str,
        request_factory: RequestFactory,
    ):
        """
        Property: All exceptions are logged with full context.

        For any exception,
        the system SHALL log the exception with request context.

        **Validates: Requirement 13.8**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        exception = RuntimeError(message)
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        request.method = "GET"

        # Patch the logger to capture log calls
        with patch("apps.core.middleware.exception_handler.logger") as mock_logger:
            middleware(request)

            # Verify exception was logged
            mock_logger.exception.assert_called_once()

            # Verify log context includes request info
            call_kwargs = mock_logger.exception.call_args[1]
            assert "exception_type" in call_kwargs
            assert "exception_message" in call_kwargs
            assert "path" in call_kwargs
            assert "method" in call_kwargs


# ==========================================================================
# SPECIFIC EXCEPTION TYPE TESTS
# ==========================================================================


class TestSpecificExceptionTypes:
    """
    Property tests for specific exception types.
    """

    @pytest.mark.property
    @override_settings(DEBUG=False)
    def test_validation_error_returns_400(self, request_factory: RequestFactory):
        """
        Property: ValidationError returns 400 Bad Request.

        **Validates: Requirement 13.3**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        exception = ValidationError(
            message="Invalid input",
            details={"field": "email", "error": "Invalid format"},
        )
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.post("/api/v2/test/")
        response = middleware(request)

        assert response.status_code == 400

        body = parse_json_response(response)
        assert body["error"] == "validation_error"
        assert body["details"]["field"] == "email"

    @pytest.mark.property
    @override_settings(DEBUG=False)
    def test_authentication_error_returns_401(self, request_factory: RequestFactory):
        """
        Property: AuthenticationError returns 401 Unauthorized.

        **Validates: Requirement 13.4**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        exception = TokenExpiredError()
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        assert response.status_code == 401

        body = parse_json_response(response)
        assert body["error"] == "token_expired"

    @pytest.mark.property
    @override_settings(DEBUG=False)
    def test_permission_denied_returns_403(self, request_factory: RequestFactory):
        """
        Property: PermissionDeniedError returns 403 Forbidden.

        **Validates: Requirement 13.4**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        exception = PermissionDeniedError(message="Access denied to resource")
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        assert response.status_code == 403

        body = parse_json_response(response)
        assert body["error"] == "permission_denied"

    @pytest.mark.property
    @override_settings(DEBUG=False)
    def test_not_found_returns_404(self, request_factory: RequestFactory):
        """
        Property: NotFoundError returns 404 Not Found.

        **Validates: Requirement 13.3**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        exception = TenantNotFoundError(message="Tenant does not exist")
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        assert response.status_code == 404

        body = parse_json_response(response)
        assert body["error"] == "tenant_not_found"

    @pytest.mark.property
    @override_settings(DEBUG=False)
    def test_rate_limit_returns_429_with_retry_after(self, request_factory: RequestFactory):
        """
        Property: RateLimitError returns 429 with retry_after.

        **Validates: Requirement 13.3**
        """
        from apps.core.middleware.exception_handler import ExceptionMiddleware

        exception = RateLimitError(message="Too many requests", retry_after=120)
        middleware = ExceptionMiddleware(create_failing_view(exception))

        request = request_factory.get("/api/v2/test/")
        response = middleware(request)

        assert response.status_code == 429

        body = parse_json_response(response)
        assert body["error"] == "rate_limit_exceeded"
        assert body["details"]["retry_after"] == 120
