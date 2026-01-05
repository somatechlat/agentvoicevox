"""
Cache service with tenant isolation.

Provides tenant-prefixed cache operations for complete data isolation.

**Implements: Requirements 10.1, 10.2, 10.3**
"""

import functools
from collections.abc import Callable
from typing import Any, Optional, TypeVar, Union

from django.core.cache import cache

from apps.core.middleware.tenant import get_current_tenant_id

T = TypeVar("T")


class CacheService:
    """
    Cache service with tenant isolation.

    All cache keys are automatically prefixed with tenant ID
    to ensure complete isolation between tenants.

    **Implements: Requirement 10.1**
    """

    @staticmethod
    def _build_key(key: str, tenant_id: Optional[str] = None) -> str:
        """
        Build tenant-prefixed cache key.

        Args:
            key: The base cache key
            tenant_id: Optional tenant ID (uses current tenant if not provided)

        Returns:
            Tenant-prefixed cache key in format: tenant:{tenant_id}:{key}
        """
        if tenant_id is None:
            current_tenant_id = get_current_tenant_id()
            tenant_id = str(current_tenant_id) if current_tenant_id else None

        if tenant_id:
            return f"tenant:{tenant_id}:{key}"
        return f"global:{key}"

    @classmethod
    def get(
        cls,
        key: str,
        default: Any = None,
        tenant_id: Optional[str] = None,
    ) -> Any:
        """
        Get value from cache.

        Args:
            key: Cache key
            default: Default value if key not found
            tenant_id: Optional tenant ID override

        Returns:
            Cached value or default

        **Implements: Requirement 10.2**
        """
        prefixed_key = cls._build_key(key, tenant_id)
        return cache.get(prefixed_key, default)

    @classmethod
    def set(
        cls,
        key: str,
        value: Any,
        timeout: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            timeout: TTL in seconds (None for default)
            tenant_id: Optional tenant ID override

        Returns:
            True if successful

        **Implements: Requirement 10.2**
        """
        prefixed_key = cls._build_key(key, tenant_id)
        cache.set(prefixed_key, value, timeout)
        return True

    @classmethod
    def delete(
        cls,
        key: str,
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key
            tenant_id: Optional tenant ID override

        Returns:
            True if successful

        **Implements: Requirement 10.2**
        """
        prefixed_key = cls._build_key(key, tenant_id)
        cache.delete(prefixed_key)
        return True

    @classmethod
    def get_or_set(
        cls,
        key: str,
        default: Union[Any, Callable[[], Any]],
        timeout: Optional[int] = None,
        tenant_id: Optional[str] = None,
    ) -> Any:
        """
        Get value from cache, or set it if not present.

        Args:
            key: Cache key
            default: Default value or callable that returns value
            timeout: TTL in seconds (None for default)
            tenant_id: Optional tenant ID override

        Returns:
            Cached or computed value

        **Implements: Requirement 10.2**
        """
        prefixed_key = cls._build_key(key, tenant_id)

        value = cache.get(prefixed_key)
        if value is not None:
            return value

        # Compute value if callable
        if callable(default):
            value = default()
        else:
            value = default

        cache.set(prefixed_key, value, timeout)
        return value

    @classmethod
    def clear_tenant(cls, tenant_id: str) -> None:
        """
        Clear all cache entries for a tenant.

        Note: This requires Redis SCAN which may be slow for large datasets.

        Args:
            tenant_id: Tenant ID to clear cache for
        """
        # Django's cache backend doesn't support pattern deletion
        # This would need to be implemented with raw Redis client
        # For now, this is a placeholder
        pass

    @classmethod
    def get_key_prefix(cls, tenant_id: Optional[str] = None) -> str:
        """
        Get the key prefix for a tenant.

        Args:
            tenant_id: Optional tenant ID (uses current tenant if not provided)

        Returns:
            Key prefix string
        """
        if tenant_id is None:
            current_tenant_id = get_current_tenant_id()
            tenant_id = str(current_tenant_id) if current_tenant_id else None

        if tenant_id:
            return f"tenant:{tenant_id}:"
        return "global:"


def cached(
    key: str,
    timeout: Optional[int] = 300,
    tenant_aware: bool = True,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for caching function results.

    Args:
        key: Cache key template (can include {arg_name} placeholders)
        timeout: TTL in seconds (default 5 minutes)
        tenant_aware: Whether to prefix with tenant ID (default True)

    Returns:
        Decorated function

    **Implements: Requirement 10.3**

    Example:
        @cached("user:{user_id}", timeout=60)
        def get_user(user_id: str) -> User:
            return User.objects.get(id=user_id)
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        """The decorator that wraps the function."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            """The wrapper that implements the caching logic."""
            # Build cache key from template
            cache_key = key.format(**kwargs)

            # Get tenant ID if tenant-aware
            tenant_id = None
            if tenant_aware:
                tenant_id = str(get_current_tenant_id()) if get_current_tenant_id() else None

            # Try to get from cache
            cached_value = CacheService.get(cache_key, tenant_id=tenant_id)
            if cached_value is not None:
                return cached_value

            # Call function and cache result
            result = func(*args, **kwargs)
            CacheService.set(cache_key, result, timeout=timeout, tenant_id=tenant_id)
            return result

        return wrapper

    return decorator
