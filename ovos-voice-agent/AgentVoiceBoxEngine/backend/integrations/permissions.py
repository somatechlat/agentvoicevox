"""
Permission decorators for SpiceDB authorization.

Provides decorators for checking permissions on API endpoints.
"""
import asyncio
import functools
import logging
from typing import Callable, List, Optional, Union

from django.http import JsonResponse

from apps.core.exceptions import PermissionDeniedError
from apps.core.middleware.tenant import get_current_tenant
from integrations.spicedb import spicedb_client

logger = logging.getLogger(__name__)


def require_permission(
    resource_type: str,
    permission: str,
    resource_id_param: str = "id",
    resource_id_getter: Optional[Callable] = None,
):
    """
    Decorator to require SpiceDB permission for an endpoint.

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
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
            # Get user ID from request
            user_id = getattr(request, "user_id", None)
            if not user_id:
                raise PermissionDeniedError("Authentication required")

            # Get resource ID
            if resource_id_getter:
                resource_id = resource_id_getter(request)
            elif resource_id_param in kwargs:
                resource_id = str(kwargs[resource_id_param])
            else:
                # Try to get from tenant context
                tenant = get_current_tenant()
                if tenant and resource_type == "tenant":
                    resource_id = str(tenant.id)
                else:
                    raise PermissionDeniedError("Resource ID not found")

            # Check permission
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(
                    spicedb_client.check_permission(
                        resource_type=resource_type,
                        resource_id=resource_id,
                        relation=permission,
                        subject_type="user",
                        subject_id=str(user_id),
                    )
                )
            finally:
                loop.close()

            if not result.allowed:
                logger.warning(
                    f"Permission denied: user={user_id} "
                    f"resource={resource_type}:{resource_id} "
                    f"permission={permission}"
                )
                raise PermissionDeniedError(
                    f"Permission '{permission}' denied on {resource_type}"
                )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def require_role(roles: Union[str, List[str]]):
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
        @functools.wraps(func)
        def wrapper(request, *args, **kwargs):
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
            raise PermissionDeniedError(
                f"Required role: {', '.join(roles)}"
            )

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


async def check_permission_async(
    user_id: str,
    resource_type: str,
    resource_id: str,
    permission: str,
) -> bool:
    """
    Check permission asynchronously.

    Args:
        user_id: User ID
        resource_type: Type of resource
        resource_id: ID of the resource
        permission: Permission to check

    Returns:
        True if allowed, False otherwise
    """
    result = await spicedb_client.check_permission(
        resource_type=resource_type,
        resource_id=resource_id,
        relation=permission,
        subject_type="user",
        subject_id=user_id,
    )
    return result.allowed


async def grant_permission(
    user_id: str,
    resource_type: str,
    resource_id: str,
    relation: str,
) -> bool:
    """
    Grant a permission to a user.

    Args:
        user_id: User ID
        resource_type: Type of resource
        resource_id: ID of the resource
        relation: Relation to grant

    Returns:
        True if successful
    """
    return await spicedb_client.write_relationship(
        resource_type=resource_type,
        resource_id=resource_id,
        relation=relation,
        subject_type="user",
        subject_id=user_id,
    )


async def revoke_permission(
    user_id: str,
    resource_type: str,
    resource_id: str,
    relation: str,
) -> bool:
    """
    Revoke a permission from a user.

    Args:
        user_id: User ID
        resource_type: Type of resource
        resource_id: ID of the resource
        relation: Relation to revoke

    Returns:
        True if successful
    """
    return await spicedb_client.delete_relationship(
        resource_type=resource_type,
        resource_id=resource_id,
        relation=relation,
        subject_type="user",
        subject_id=user_id,
    )
