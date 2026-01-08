"""
Permission Decorators.

Provides @require_permission("resource:action") decorator for
granular permission enforcement on API endpoints.
"""

import logging
from collections.abc import Callable
from functools import wraps
from typing import Optional, Union

from django.http import HttpRequest

from apps.core.exceptions import PermissionDeniedError

logger = logging.getLogger(__name__)


def require_permission(
    permission: str,
    resource_id_param: Optional[str] = None,
):
    """
    Decorator to require granular resource:action permission.

    Checks the permission matrix (with tenant overrides) to determine
    if the user has the required permission.

    Args:
        permission: Permission string in format "resource:action"
                   (e.g., "agents:create", "sessions:read")
        resource_id_param: Optional parameter name containing resource ID
                          for ownership-based permission checks

    Usage:
        @require_permission("agents:create")
        def create_agent(request):
            ...

        @require_permission("sessions:read", resource_id_param="session_id")
        def get_session(request, session_id: UUID):
            ...

        @require_permission("conversations:read")
        def list_conversations(request):
            ...

    Raises:
        PermissionDeniedError: If user lacks the required permission
    """

    def decorator(func: Callable) -> Callable:
        """
        The actual decorator that takes the function to be wrapped.
        """

        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            """
            The wrapper function that executes the permission check before
            calling the original decorated function.
            """
            from apps.core.permissions.service import GranularPermissionService

            # Get user from request
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                raise PermissionDeniedError(
                    "Authentication required",
                    details={"required_permission": permission},
                )

            # Parse permission string
            parts = permission.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid permission format: {permission}")

            resource, action = parts

            # Get resource ID if specified
            resource_id = None
            if resource_id_param:
                resource_id = kwargs.get(resource_id_param)
                if resource_id:
                    resource_id = str(resource_id)

            # Check permission
            if not GranularPermissionService.check_permission(
                user=user,
                resource=resource,
                action=action,
                resource_id=resource_id,
            ):
                logger.warning(
                    f"Permission denied: user={user.id} "
                    f"permission={permission} resource_id={resource_id}"
                )
                raise PermissionDeniedError(
                    f"Permission '{permission}' denied",
                    details={"required_permission": permission},
                )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_granular_role(roles: Union[str, list[str]]):
    """
    Decorator to require specific platform roles.

    Checks if the user has any of the specified roles within
    the current tenant context.

    Args:
        roles: Single role or list of roles (any match allows access)

    Usage:
        @require_granular_role("tenant_admin")
        def admin_only(request):
            ...

        @require_granular_role(["tenant_admin", "agent_admin"])
        def admin_or_agent_admin(request):
            ...

    Raises:
        PermissionDeniedError: If user lacks any of the required roles
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(func: Callable) -> Callable:
        """
        The actual decorator that takes the function to be wrapped.
        """

        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            """
            The wrapper function that executes the role check before
            calling the original decorated function.
            """
            from apps.core.permissions.service import GranularPermissionService

            # Get user from request
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                raise PermissionDeniedError(
                    "Authentication required", details={"required_roles": roles}
                )

            # Get user's roles
            user_roles = GranularPermissionService.get_user_roles(user)

            # Check if user has any of the required roles
            if any(role in user_roles for role in roles):
                return func(request, *args, **kwargs)

            # Check for superuser
            if getattr(user, "is_superuser", False):
                return func(request, *args, **kwargs)

            logger.warning(
                f"Role check failed: user={user.id} "
                f"required={roles} actual={user_roles}"
            )
            raise PermissionDeniedError(
                f"Required role: {', '.join(roles)}",
                details={"required_roles": roles, "user_roles": user_roles},
            )

        return wrapper

    return decorator


def require_any_permission(*permissions: str):
    """
    Decorator to require any of the specified permissions.

    User must have at least one of the listed permissions.

    Args:
        *permissions: Variable number of permission strings

    Usage:
        @require_any_permission("agents:read", "agents:create")
        def view_or_create_agent(request):
            ...

    Raises:
        PermissionDeniedError: If user lacks all of the permissions
    """

    def decorator(func: Callable) -> Callable:
        """
        The actual decorator that takes the function to be wrapped.
        """

        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            """
            The wrapper function that executes the "any permission" check before
            calling the original decorated function.
            """
            from apps.core.permissions.service import GranularPermissionService

            # Get user from request
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                raise PermissionDeniedError(
                    "Authentication required",
                    details={"required_permissions": list(permissions)},
                )

            # Check each permission
            for permission in permissions:
                parts = permission.split(":")
                if len(parts) != 2:
                    continue

                resource, action = parts

                if GranularPermissionService.check_permission(
                    user=user,
                    resource=resource,
                    action=action,
                ):
                    return func(request, *args, **kwargs)

            logger.warning(
                f"Permission denied: user={user.id} " f"required_any={permissions}"
            )
            raise PermissionDeniedError(
                f"Required one of: {', '.join(permissions)}",
                details={"required_permissions": list(permissions)},
            )

        return wrapper

    return decorator


def require_all_permissions(*permissions: str):
    """
    Decorator to require all of the specified permissions.

    User must have all of the listed permissions.

    Args:
        *permissions: Variable number of permission strings

    Usage:
        @require_all_permissions("agents:read", "agents:update")
        def read_and_update_agent(request):
            ...

    Raises:
        PermissionDeniedError: If user lacks any of the permissions
    """

    def decorator(func: Callable) -> Callable:
        """
        The actual decorator that takes the function to be wrapped.
        """

        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            """
            The wrapper function that executes the "all permissions" check before
            calling the original decorated function.
            """
            from apps.core.permissions.service import GranularPermissionService

            # Get user from request
            user = getattr(request, "user", None)
            if not user or not getattr(user, "is_authenticated", False):
                raise PermissionDeniedError(
                    "Authentication required",
                    details={"required_permissions": list(permissions)},
                )

            # Check each permission
            missing = []
            for permission in permissions:
                parts = permission.split(":")
                if len(parts) != 2:
                    missing.append(permission)
                    continue

                resource, action = parts

                if not GranularPermissionService.check_permission(
                    user=user,
                    resource=resource,
                    action=action,
                ):
                    missing.append(permission)

            if missing:
                logger.warning(
                    f"Permission denied: user={user.id} " f"missing={missing}"
                )
                raise PermissionDeniedError(
                    f"Missing permissions: {', '.join(missing)}",
                    details={
                        "required_permissions": list(permissions),
                        "missing_permissions": missing,
                    },
                )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator
