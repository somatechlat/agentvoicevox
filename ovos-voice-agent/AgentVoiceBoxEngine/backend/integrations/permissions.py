"""
Permission decorators using Django native authorization.

Provides decorators for checking permissions on API endpoints using
Django's built-in permission system with PermissionMatrix model.
"""

import functools
import logging
from collections.abc import Callable
from typing import Optional, Union

from apps.core.exceptions import PermissionDeniedError
from apps.core.middleware.tenant import get_current_tenant

logger = logging.getLogger(__name__)


def require_permission(
    resource_type: str,
    permission: str,
    resource_id_param: str = "id",
    resource_id_getter: Optional[Callable] = None,
):
    """
    Decorator to require permission for an endpoint using Django native permissions.

    Args:
        resource_type: Type of resource (e.g., "tenant", "project")
        permission: Permission to check (e.g., "view", "manage")
        resource_id_param: Name of the parameter containing resource ID
        resource_id_getter: Optional function to extract resource ID from request

    Usage:
        @require_permission("project", "view", resource_id_param="project_id")
        def get_project(request, project_id: UUID):
            ...

        @require_permission("tenant", "administrate", resource_id_getter=lambda r: str(r.tenant.id))
        def manage_tenant(request):
            ...
    """

    def decorator(func: Callable) -> Callable:
        """
        The actual decorator that takes the function to be wrapped.
        """

        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            """
            The wrapper function that executes the permission check before
            calling the original decorated function.
            """
            from apps.core.permissions.service import GranularPermissionService

            # Get user from request
            user = getattr(request, "user", None)
            user_id = getattr(request, "user_id", None)

            if not user and not user_id:
                raise PermissionDeniedError("Authentication required")

            # Get resource ID
            resource_id = None
            if resource_id_getter:
                resource_id = resource_id_getter(request)
            elif resource_id_param in kwargs:
                resource_id = str(kwargs[resource_id_param])
            else:
                # Try to get from tenant context
                tenant = get_current_tenant()
                if tenant and resource_type == "tenant":
                    resource_id = str(tenant.id)

            # Check permission using Django native permission service
            if user:
                allowed = GranularPermissionService.check_permission(
                    user=user,
                    resource=resource_type,
                    action=permission,
                    resource_id=resource_id,
                )
            else:
                # No user object, deny access
                allowed = False

            if not allowed:
                logger.warning(
                    f"Permission denied: user={user_id or user} "
                    f"resource={resource_type}:{resource_id} "
                    f"permission={permission}"
                )
                raise PermissionDeniedError(
                    f"Permission '{permission}' denied on {resource_type}"
                )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_role(roles: Union[str, list[str]]):
    """
    Decorator to require specific JWT roles for an endpoint.

    Args:
        roles: Single role or list of roles (any match allows access)

    Usage:
        @require_role("admin")
        def admin_only(request):
            ...

        @require_role(["admin", "developer"])
        def admin_or_developer(request):
            ...
    """
    if isinstance(roles, str):
        roles = [roles]

    def decorator(func: Callable) -> Callable:
        """
        The actual decorator that takes the function to be wrapped.
        """

        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            """
            The wrapper function that executes the role check before
            calling the original decorated function.
            """
            # Get roles from request
            jwt_roles = getattr(request, "jwt_roles", [])
            user = getattr(request, "user", None)

            # Check JWT roles
            if any(role in jwt_roles for role in roles):
                return func(request, *args, **kwargs)

            # Check user model role
            if user and hasattr(user, "role"):
                if user.role in roles:
                    return func(request, *args, **kwargs)

            # Check for superuser
            if user and getattr(user, "is_superuser", False):
                return func(request, *args, **kwargs)

            logger.warning(
                f"Role check failed: required={roles} "
                f"jwt_roles={jwt_roles} "
                f"user_role={getattr(user, 'role', None)}"
            )
            raise PermissionDeniedError(f"Required role: {', '.join(roles)}")

        return wrapper

    return decorator


def require_sysadmin(func: Callable) -> Callable:
    """Decorator to require SYSADMIN role."""
    return require_role("sysadmin")(func)


def require_admin(func: Callable) -> Callable:
    """Decorator to require ADMIN or SYSADMIN role."""
    return require_role(["sysadmin", "admin"])(func)


def require_developer(func: Callable) -> Callable:
    """Decorator to require DEVELOPER, ADMIN, or SYSADMIN role."""
    return require_role(["sysadmin", "admin", "developer"])(func)


def require_operator(func: Callable) -> Callable:
    """Decorator to require OPERATOR or higher role."""
    return require_role(["sysadmin", "admin", "developer", "operator"])(func)


def require_billing(func: Callable) -> Callable:
    """Decorator to require BILLING, ADMIN, or SYSADMIN role."""
    return require_role(["sysadmin", "admin", "billing"])(func)


def require_tenant_permission(permission: str):
    """
    Decorator to require a permission on the current tenant.

    Args:
        permission: Permission to check (e.g., "view", "administrate")

    Usage:
        @require_tenant_permission("administrate")
        def manage_tenant_settings(request):
            ...
    """

    def resource_id_getter(request):
        """
        Retrieves the tenant ID from the current request context.

        Args:
            request: The current HttpRequest object.

        Returns:
            The ID of the current tenant as a string.

        Raises:
            PermissionDeniedError: If no tenant context is found.
        """
        tenant = get_current_tenant()
        if not tenant:
            raise PermissionDeniedError("Tenant context required")
        return str(tenant.id)

    return require_permission(
        resource_type="tenant",
        permission=permission,
        resource_id_getter=resource_id_getter,
    )


def require_project_permission(permission: str, project_id_param: str = "project_id"):
    """
    Decorator to require a permission on a project.

    Args:
        permission: Permission to check (e.g., "view", "manage")
        project_id_param: Name of the parameter containing project ID

    Usage:
        @require_project_permission("manage")
        def update_project(request, project_id: UUID):
            ...
    """
    return require_permission(
        resource_type="project",
        permission=permission,
        resource_id_param=project_id_param,
    )


def check_permission_sync(
    user,
    resource_type: str,
    resource_id: str,
    permission: str,
) -> bool:
    """
    Check permission synchronously using Django native permissions.

    Args:
        user: User object
        resource_type: Type of resource
        resource_id: ID of the resource
        permission: Permission to check

    Returns:
        True if allowed, False otherwise
    """
    from apps.core.permissions.service import GranularPermissionService

    return GranularPermissionService.check_permission(
        user=user,
        resource=resource_type,
        action=permission,
        resource_id=resource_id,
    )


def grant_permission(
    user,
    role: str,
    tenant=None,
) -> bool:
    """
    Grant a role to a user using Django native permissions.

    Args:
        user: User object
        role: Role to assign
        tenant: Tenant context (uses current tenant if not provided)

    Returns:
        True if successful
    """
    from apps.core.middleware.tenant import get_current_tenant
    from apps.core.permissions.service import GranularPermissionService

    if tenant is None:
        tenant = get_current_tenant()

    if not tenant:
        return False

    GranularPermissionService.assign_role(
        user=user,
        role=role,
        tenant=tenant,
    )
    return True


def revoke_permission(
    user,
    role: str,
    tenant=None,
) -> bool:
    """
    Revoke a role from a user using Django native permissions.

    Args:
        user: User object
        role: Role to revoke
        tenant: Tenant context (uses current tenant if not provided)

    Returns:
        True if successful
    """
    from apps.core.middleware.tenant import get_current_tenant
    from apps.core.permissions.service import GranularPermissionService

    if tenant is None:
        tenant = get_current_tenant()

    if not tenant:
        return False

    return GranularPermissionService.revoke_role(
        user=user,
        role=role,
        tenant=tenant,
    )
