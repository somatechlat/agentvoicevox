"""
Rate limiting middleware.

Implements token bucket rate limiting with:
- Per-IP limits for unauthenticated requests
- Per-user limits for authenticated requests
- Per-API-key limits for API key requests

Returns rate limit headers:
- X-RateLimit-Limit
- X-RateLimit-Remaining
- X-RateLimit-Reset
"""

import time

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse


class RateLimitMiddleware:
    """Middleware for rate limiting requests."""

    def __init__(self, get_response):
        """Initializes the middleware."""
        self.get_response = get_response
        self.rate_limits = settings.RATE_LIMITS

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """
        Processes the request, checks rate limits, and adds
        rate limit headers to the response.
        """
        # Get rate limit key and limit
        key, limit = self._get_rate_limit_params(request)

        # Check rate limit
        allowed, remaining, reset_time = self._check_rate_limit(key, limit)

        if not allowed:
            response = JsonResponse(
                {
                    "error": "rate_limit_exceeded",
                    "message": "Rate limit exceeded",
                    "details": {
                        "retry_after": reset_time - int(time.time()),
                    },
                },
                status=429,
            )
            self._add_rate_limit_headers(response, limit, 0, reset_time)
            return response

        # Process request
        response = self.get_response(request)

        # Add rate limit headers
        self._add_rate_limit_headers(response, limit, remaining, reset_time)

        return response

    def _get_rate_limit_params(self, request: HttpRequest) -> tuple[str, int]:
        """Get rate limit key and limit based on request context."""
        # Admin users get higher limits
        if hasattr(request, "jwt_roles") and "admin" in request.jwt_roles:
            key = f"ratelimit:admin:{request.user_id}"
            return key, self.rate_limits["ADMIN"]

        # API key requests
        if hasattr(request, "api_key_id"):
            key = f"ratelimit:apikey:{request.api_key_id}"
            return key, self.rate_limits["API_KEY"]

        # Authenticated users
        if hasattr(request, "user_id") and request.user_id:
            key = f"ratelimit:user:{request.user_id}"
            return key, self.rate_limits["DEFAULT"]

        # Unauthenticated - rate limit by IP
        client_ip = self._get_client_ip(request)
        key = f"ratelimit:ip:{client_ip}"
        return key, self.rate_limits["DEFAULT"]

    def _check_rate_limit(self, key: str, limit: int) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.

        Returns:
            Tuple of (allowed, remaining, reset_time)
        """
        now = int(time.time())
        window_start = now - (now % 60)  # 1-minute window
        reset_time = window_start + 60

        # Get current count
        count_key = f"{key}:{window_start}"
        current_count = cache.get(count_key, 0)

        if current_count >= limit:
            return False, 0, reset_time

        # Increment count
        new_count = cache.incr(count_key, 1) if current_count > 0 else 1
        if new_count == 1:
            cache.set(count_key, 1, timeout=120)  # 2 minutes TTL

        remaining = max(0, limit - new_count)
        return True, remaining, reset_time

    def _add_rate_limit_headers(
        self,
        response: HttpResponse,
        limit: int,
        remaining: int,
        reset_time: int,
    ) -> None:
        """Add rate limit headers to response."""
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(remaining)
        response["X-RateLimit-Reset"] = str(reset_time)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
