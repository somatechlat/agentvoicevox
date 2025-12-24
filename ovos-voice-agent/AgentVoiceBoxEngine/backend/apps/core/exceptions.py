"""
Custom exceptions for AgentVoiceBox Platform.

All exceptions follow a consistent structure with:
- status_code: HTTP status code
- error_code: Machine-readable error identifier
- message: Human-readable error message
- details: Optional additional error details
"""
from typing import Any, Dict, Optional


class APIException(Exception):
    """Base exception for all API errors."""
    
    status_code: int = 500
    error_code: str = "internal_error"
    default_message: str = "An unexpected error occurred"
    
    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)


# ==========================================================================
# VALIDATION ERRORS (400)
# ==========================================================================
class ValidationError(APIException):
    """Request validation failed."""
    status_code = 400
    error_code = "validation_error"
    default_message = "Request validation failed"


# ==========================================================================
# AUTHENTICATION ERRORS (401)
# ==========================================================================
class AuthenticationError(APIException):
    """Authentication failed."""
    status_code = 401
    error_code = "authentication_error"
    default_message = "Authentication required"


class TokenExpiredError(AuthenticationError):
    """JWT token has expired."""
    error_code = "token_expired"
    default_message = "Token has expired"


class InvalidTokenError(AuthenticationError):
    """JWT token is invalid or malformed."""
    error_code = "invalid_token"
    default_message = "Invalid or malformed token"


class APIKeyExpiredError(AuthenticationError):
    """API key has expired."""
    error_code = "api_key_expired"
    default_message = "API key has expired"


class APIKeyRevokedError(AuthenticationError):
    """API key has been revoked."""
    error_code = "api_key_revoked"
    default_message = "API key has been revoked"


# ==========================================================================
# AUTHORIZATION ERRORS (403)
# ==========================================================================
class PermissionDeniedError(APIException):
    """User does not have permission to perform this action."""
    status_code = 403
    error_code = "permission_denied"
    default_message = "Permission denied"


class InsufficientScopeError(PermissionDeniedError):
    """API key does not have required scope."""
    error_code = "insufficient_scope"
    default_message = "API key does not have required scope"


class TenantSuspendedError(PermissionDeniedError):
    """Tenant account is suspended."""
    error_code = "tenant_suspended"
    default_message = "Tenant account is suspended"


class TenantLimitExceededError(PermissionDeniedError):
    """Tenant has exceeded their plan limits."""
    error_code = "tenant_limit_exceeded"
    default_message = "Tenant has exceeded plan limits"


# ==========================================================================
# NOT FOUND ERRORS (404)
# ==========================================================================
class NotFoundError(APIException):
    """Resource not found."""
    status_code = 404
    error_code = "not_found"
    default_message = "Resource not found"


class TenantNotFoundError(NotFoundError):
    """Tenant not found."""
    error_code = "tenant_not_found"
    default_message = "Tenant not found"


class UserNotFoundError(NotFoundError):
    """User not found."""
    error_code = "user_not_found"
    default_message = "User not found"


class ResourceNotFoundError(NotFoundError):
    """Generic resource not found."""
    error_code = "resource_not_found"
    default_message = "Requested resource not found"


# ==========================================================================
# CONFLICT ERRORS (409)
# ==========================================================================
class ConflictError(APIException):
    """Resource conflict."""
    status_code = 409
    error_code = "conflict"
    default_message = "Resource conflict"


class DuplicateResourceError(ConflictError):
    """Resource already exists."""
    error_code = "duplicate_resource"
    default_message = "Resource already exists"


# ==========================================================================
# RATE LIMIT ERRORS (429)
# ==========================================================================
class RateLimitError(APIException):
    """Rate limit exceeded."""
    status_code = 429
    error_code = "rate_limit_exceeded"
    default_message = "Rate limit exceeded"
    
    def __init__(
        self,
        message: Optional[str] = None,
        retry_after: int = 60,
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, details)
        self.retry_after = retry_after
        self.details["retry_after"] = retry_after
