"""
Custom API Exception Definitions
==================================

This module defines a structured set of custom exceptions for the AgentVoiceBox
Platform API. All exceptions inherit from `APIException`, providing a consistent
way to convey error information (HTTP status code, machine-readable error code,
human-readable message, and optional details) to API clients.

These exceptions are designed to be caught by a custom exception handler (e.g.,
in Django Ninja or Django REST Framework) to automatically translate them into
standardized HTTP error responses.
"""

from typing import Any, Optional


class APIException(Exception):
    """
    Base exception for all API-specific errors.

    All custom API exceptions in the platform should inherit from this class.
    It provides a standardized structure for error responses, including an
    HTTP status code, a machine-readable error code, and a human-readable message.

    Attributes:
        status_code (int): The HTTP status code to return for this exception.
        error_code (str): A unique, machine-readable identifier for the error.
        default_message (str): A default human-readable message if a specific
                               message is not provided.
    """

    status_code: int = 500
    error_code: str = "internal_error"
    default_message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        """
        Initializes the APIException.

        Args:
            message: An optional human-readable message for the error.
                     Defaults to `self.default_message`.
            details: An optional dictionary for additional, context-specific error details.
            error_code: An optional machine-readable code, overriding `self.error_code`.
        """
        self.message = message or self.default_message
        self.details = details or {}
        if error_code:
            self.error_code = error_code
        super().__init__(self.message)


# ==========================================================================
# VALIDATION ERRORS (HTTP 400 Bad Request)
# ==========================================================================
class ValidationError(APIException):
    """
    Raised when client input data fails validation (e.g., missing fields, invalid format).
    Corresponds to HTTP 400 Bad Request.
    """

    status_code = 400
    error_code = "validation_error"
    default_message = "Request validation failed"


# ==========================================================================
# AUTHENTICATION ERRORS (HTTP 401 Unauthorized)
# ==========================================================================
class AuthenticationError(APIException):
    """
    Raised when the client fails to provide valid authentication credentials.
    Corresponds to HTTP 401 Unauthorized.
    """

    status_code = 401
    error_code = "authentication_error"
    default_message = "Authentication required"


class TokenExpiredError(AuthenticationError):
    """
    Raised when an provided JWT is valid but has expired.
    """

    error_code = "token_expired"
    default_message = "Authentication token has expired"


class InvalidTokenError(AuthenticationError):
    """
    Raised when an provided JWT is malformed, invalid, or unsigned.
    """

    error_code = "invalid_token"
    default_message = "Invalid or malformed authentication token"


class APIKeyExpiredError(AuthenticationError):
    """
    Raised when an provided API key is valid but has passed its expiration date.
    """

    error_code = "api_key_expired"
    default_message = "API key has expired"


class APIKeyRevokedError(AuthenticationError):
    """
    Raised when an provided API key has been explicitly revoked.
    """

    error_code = "api_key_revoked"
    default_message = "API key has been revoked"


# ==========================================================================
# AUTHORIZATION ERRORS (HTTP 403 Forbidden)
# ==========================================================================
class PermissionDeniedError(APIException):
    """
    Raised when the authenticated user does not have the necessary permissions
    to perform the requested action. Corresponds to HTTP 403 Forbidden.
    """

    status_code = 403
    error_code = "permission_denied"
    default_message = "Permission denied"


class InsufficientScopeError(PermissionDeniedError):
    """
    Raised when an API key is authenticated but does not possess the required
    scope(s) for the requested operation.
    """

    error_code = "insufficient_scope"
    default_message = "API key does not have required scope"


class TenantSuspendedError(PermissionDeniedError):
    """
    Raised when an operation is attempted for a tenant whose account is suspended.
    """

    error_code = "tenant_suspended"
    default_message = "Tenant account is suspended"


class TenantLimitExceededError(PermissionDeniedError):
    """
    Raised when a tenant attempts an action that would exceed their
    plan-defined resource limits (e.g., max users, max projects).
    """

    error_code = "tenant_limit_exceeded"
    default_message = "Tenant has exceeded plan limits"


# ==========================================================================
# NOT FOUND ERRORS (HTTP 404 Not Found)
# ==========================================================================
class NotFoundError(APIException):
    """
    Raised when the requested resource does not exist.
    Corresponds to HTTP 404 Not Found.
    """

    status_code = 404
    error_code = "not_found"
    default_message = "Resource not found"


class TenantNotFoundError(NotFoundError):
    """
    Raised when a specific tenant cannot be found.
    """

    error_code = "tenant_not_found"
    default_message = "Tenant not found"


class UserNotFoundError(NotFoundError):
    """
    Raised when a specific user cannot be found.
    """

    error_code = "user_not_found"
    default_message = "User not found"


class ResourceNotFoundError(NotFoundError):
    """
    A generic version of NotFoundError for when a specific resource type isn't needed.
    """

    error_code = "resource_not_found"
    default_message = "Requested resource not found"


# ==========================================================================
# CONFLICT ERRORS (HTTP 409 Conflict)
# ==========================================================================
class ConflictError(APIException):
    """
    Raised when a request conflicts with the current state of the server.
    Typically used for uniqueness constraints or conflicting resource states.
    Corresponds to HTTP 409 Conflict.
    """

    status_code = 409
    error_code = "conflict"
    default_message = "Resource conflict"


class DuplicateResourceError(ConflictError):
    """
    Raised when an attempt is made to create a resource that already exists
    and violates a uniqueness constraint.
    """

    error_code = "duplicate_resource"
    default_message = "Resource already exists"


# ==========================================================================
# RATE LIMIT ERRORS (HTTP 429 Too Many Requests)
# ==========================================================================
class RateLimitError(APIException):
    """
    Raised when the client has sent too many requests in a given amount of time.
    Corresponds to HTTP 429 Too Many Requests.
    """

    status_code = 429
    error_code = "rate_limit_exceeded"
    default_message = "Rate limit exceeded"

    def __init__(
        self,
        message: Optional[str] = None,
        retry_after: int = 60,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initializes the RateLimitError.

        Args:
            message: An optional human-readable message.
            retry_after: The number of seconds the client should wait before making
                         another request.
            details: An optional dictionary for additional error details.
        """
        super().__init__(message, details)
        self.retry_after = retry_after
        self.details["retry_after"] = retry_after


# ==========================================================================
# NOT IMPLEMENTED ERRORS (HTTP 501 Not Implemented)
# ==========================================================================
class FeatureNotImplementedError(APIException):
    """
    Raised when the requested functionality is not implemented on the server.
    Corresponds to HTTP 501 Not Implemented.
    """

    status_code = 501
    error_code = "not_implemented"
    default_message = "Requested feature is not implemented or configured"
