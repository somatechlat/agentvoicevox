"""
Request logging middleware.

Logs all HTTP requests with:
- request_id (unique per request)
- method, path, status_code
- duration_ms
- client_ip
- user_id, tenant_id (when available)

Returns X-Request-ID header in response.
"""
import time
import uuid
import structlog

from django.http import HttpRequest, HttpResponse

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware:
    """Middleware for logging all HTTP requests."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request: HttpRequest) -> HttpResponse:
        # Generate unique request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.request_id = request_id
        
        # Record start time
        start_time = time.perf_counter()
        
        # Bind request context to structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.path,
            client_ip=self._get_client_ip(request),
        )
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000
        
        # Add user/tenant context if available
        user_id = getattr(request, "user_id", None)
        tenant_id = getattr(request, "tenant_id", None)
        
        if user_id:
            structlog.contextvars.bind_contextvars(user_id=str(user_id))
        if tenant_id:
            structlog.contextvars.bind_contextvars(tenant_id=str(tenant_id))
        
        # Log request
        logger.info(
            "request_completed",
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
            content_length=len(response.content) if hasattr(response, "content") else 0,
        )
        
        # Add request ID to response headers
        response["X-Request-ID"] = request_id
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request headers."""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
