"""
Realtime session rate limiting using Django cache.
"""

from __future__ import annotations

import time

from django.conf import settings
from django.core.cache import cache


class RealtimeRateLimiter:
    """Rate limiter for realtime session requests and tokens."""

    def __init__(self) -> None:
        """Initializes the RealtimeRateLimiter with configured limits."""
        self._limits = settings.REALTIME_RATE_LIMITS

    def _window_seconds(self) -> int:
        """
        Returns the duration of the rate limiting window in seconds.

        Returns:
            int: The window duration in seconds.
        """
        return int(self._limits["WINDOW_SECONDS"])

    def _window_start(self, now: int) -> int:
        """
        Calculates the start timestamp of the current rate limiting window.

        Args:
            now: The current timestamp.

        Returns:
            int: The timestamp representing the start of the current window.
        """
        window = self._window_seconds()
        return now - (now % window)

    def _key(self, session_id: str, metric: str, window_start: int) -> str:
        """
        Constructs a unique cache key for a given session, metric, and window.

        Args:
            session_id: The ID of the realtime session.
            metric: The metric being rate-limited (e.g., "requests", "tokens").
            window_start: The start timestamp of the current rate limiting window.

        Returns:
            str: The constructed cache key.
        """
        return f"realtime:ratelimit:{session_id}:{metric}:{window_start}"

    def check_limit(self, session_id: str, tokens: int = 0) -> tuple[bool, dict]:
        """Check if the session is within limits."""
        now = int(time.time())
        window_start = self._window_start(now)
        window_seconds = self._window_seconds()
        reset_seconds = max(0, window_seconds - (now - window_start))

        requests_key = self._key(session_id, "requests", window_start)
        tokens_key = self._key(session_id, "tokens", window_start)

        requests_used = cache.get(requests_key, 0)
        tokens_used = cache.get(tokens_key, 0)

        requests_limit = int(self._limits["REQUESTS_PER_MINUTE"])
        tokens_limit = int(self._limits["TOKENS_PER_MINUTE"])

        allowed = (requests_used < requests_limit) and (tokens_used + tokens <= tokens_limit)

        return allowed, {
            "requests_limit": requests_limit,
            "requests_remaining": max(0, requests_limit - requests_used),
            "tokens_limit": tokens_limit,
            "tokens_remaining": max(0, tokens_limit - tokens_used - tokens),
            "reset_seconds": reset_seconds,
        }

    def consume(self, session_id: str, tokens: int = 0) -> None:
        """Consume request and token quota for a session."""
        now = int(time.time())
        window_start = self._window_start(now)
        ttl = self._window_seconds() * 2

        requests_key = self._key(session_id, "requests", window_start)
        tokens_key = self._key(session_id, "tokens", window_start)

        self._increment_key(requests_key, 1, ttl)
        if tokens:
            self._increment_key(tokens_key, tokens, ttl)

    def _increment_key(self, key: str, amount: int, ttl: int) -> None:
        """
        Increments a cache key by a specified amount, setting a TTL if it's a new key.

        Args:
            key: The cache key to increment.
            amount: The amount to increment by.
            ttl: The Time-To-Live (in seconds) for the key if it's newly created.
        """
        existing = cache.get(key)
        if existing is None:
            cache.set(key, amount, timeout=ttl)
            return
        cache.incr(key, amount)
