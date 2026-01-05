"""
Exception handling middleware.

Catches all exceptions and returns consistent JSON responses.
In production, returns generic error without stack trace.
In development, includes stack trace for debugging.
"""

import traceback

import structlog
from django.conf import settings
from django.http import HttpRequest, HttpResponse, JsonResponse

from apps.core.exceptions import APIException

logger = structlog.get_logger(__name__)


class ExceptionMiddleware:
    """Middleware for global exception handling."""

    def __init__(self, get_response):
        """Initializes the middleware."""
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Processes the request and handles any exceptions."""
        try:
            return self.get_response(request)
        except Exception as exc:
            return self._handle_exception(request, exc)

    def _handle_exception(self, request: HttpRequest, exc: Exception) -> JsonResponse:
        """Handle exception and return JSON response."""
        # Log the exception
        logger.exception(
            "unhandled_exception",
            exception_type=type(exc).__name__,
            exception_message=str(exc),
            path=request.path,
            method=request.method,
        )

        # Handle known API exceptions
        if isinstance(exc, APIException):
            return JsonResponse(
                {
                    "error": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
                status=exc.status_code,
            )

        # Handle unknown exceptions
        if settings.DEBUG:
            # Include stack trace in development
            return JsonResponse(
                {
                    "error": "internal_error",
                    "message": str(exc),
                    "details": {
                        "exception_type": type(exc).__name__,
                        "traceback": traceback.format_exc().split("\n"),
                    },
                },
                status=500,
            )
        else:
            # Generic error in production
            return JsonResponse(
                {
                    "error": "internal_error",
                    "message": "An unexpected error occurred",
                },
                status=500,
            )
