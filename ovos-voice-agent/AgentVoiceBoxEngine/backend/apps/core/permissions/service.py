"""
Granular Permission Service.

Implements hierarchical permission resolution with tenant overrides.
Uses Django's native permission system with PermissionMatrix model.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from django.db.models import Q
from django.utils import timezone

if TYPE_CHECKING:
    from apps.core.permissions.models import TenantPermissionOverride, UserRoleAssignment
    from apps.tenants.models import Tenant
    from apps.users.models import User

logger = logging.getLogger(__name__)


class GranularPermissionService:
    """
    Service for checking granular resource:action permissions.

    Resolution order:
    1. Check tenant-level overrides
    2. Fall back to platform-level defaults

    Permission Check Flow:
    Request → Extract roles from user → Check tenant overrides →
    Fall back to platform defaults → Check conditions → Allow/Deny
    """

    @staticmethod
    def check_permission(
        user: "User",
        resource: str,
        action: str,
        resource_id: Optional[str] = None,
        tenant: Optional["Tenant"] = None,
    ) -> bool:
        """
        Check if user has permission for resource:action.

        Args:
            user: The user to check permissions for
            resource: Resource type (e.g., "agents", "sessions")
            action: Action name (e.g., "create", "read", "delete")
            resource_id: Optional resource ID for ownership checks
            tenant: Optional tenant context (uses current tenant if not provided)

        Returns:
            True if permission is granted, False otherwise
        """
        from apps.core.middleware.tenant import get_current_tenant
        from apps.core.permissions.models import (
            PermissionMatrix,
            TenantPermissionOverride,
        )

        # Get tenant context
        if tenant is None:
            tenant = get_current_tenant()

        if not tenant:
            logger.warning(
                f"Permission check failed: no tenant context for "
                f"user={user.id if user else None} resource={resource}:{action}"
            )
            return False

        # Get user's roles
        user_roles = GranularPermissionService.get_user_roles(user, tenant)

        if not user_roles:
            logger.warning(
                f"Permission check failed: no roles for "
                f"user={user.id} tenant={tenant.id} resource={resource}:{action}"
            )
            return False

        for role in user_roles:
            # Check tenant override first
            override = TenantPermissionOverride.objects.filter(
                tenant=tenant,
                role=role,
                resource=resource,
                action=action,
            ).first()

            if override is not None:
                if override.allowed:
                    if GranularPermissionService._check_conditions(
                        override.conditions, user, resource_id
                    ):
                        logger.debug(
                            f"Permission granted via tenant override: "
                            f"user={user.id} role={role} {resource}:{action}"
                        )
                        return True
                # Explicitly denied at tenant level, check next role
                continue

            # Fall back to platform default
            platform_perm = PermissionMatrix.objects.filter(
                role=role,
                resource=resource,
                action=action,
            ).first()

            if platform_perm and platform_perm.allowed:
                if GranularPermissionService._check_conditions(
                    platform_perm.conditions, user, resource_id
                ):
                    logger.debug(
                        f"Permission granted via platform default: "
                        f"user={user.id} role={role} {resource}:{action}"
                    )
                    return True

        logger.info(
            f"Permission denied: user={user.id} roles={user_roles} " f"resource={resource}:{action}"
        )
        return False

    @staticmethod
    def get_user_roles(
        user: "User",
        tenant: Optional["Tenant"] = None,
    ) -> list[str]:
        """
        Get all roles assigned to a user within a tenant.

        Args:
            user: The user to get roles for
            tenant: Optional tenant context (uses current tenant if not provided)

        Returns:
            List of role names
        """
        from apps.core.middleware.tenant import get_current_tenant
        from apps.core.permissions.models import UserRoleAssignment

        if tenant is None:
            tenant = get_current_tenant()

        if not tenant:
            return []

        # Get roles from UserRoleAssignment (not expired)
        now = timezone.now()
        assignments = (
            UserRoleAssignment.objects.filter(
                tenant=tenant,
                user=user,
            )
            .filter(Q(expires_at__isnull=True) | Q(expires_at__gt=now))
            .values_list("role", flat=True)
        )

        roles = list(assignments)

        # Add primary role from user model if exists
        if hasattr(user, "role") and user.role:
            if user.role not in roles:
                roles.append(user.role)

        # Add roles from JWT claims if available
        jwt_roles = getattr(user, "_jwt_roles", None)
        if jwt_roles:
            for role in jwt_roles:
                if role not in roles:
                    roles.append(role)

        return roles

    @staticmethod
    def get_effective_permissions(
        user: "User",
        tenant: Optional["Tenant"] = None,
    ) -> list[str]:
        """
        Get all effective permissions for a user as resource:action strings.

        Args:
            user: The user to get permissions for
            tenant: Optional tenant context

        Returns:
            Sorted list of permission strings (e.g., ["agents:create", "agents:read"])
        """
        from apps.core.middleware.tenant import get_current_tenant
        from apps.core.permissions.models import (
            PermissionMatrix,
            TenantPermissionOverride,
        )

        if tenant is None:
            tenant = get_current_tenant()

        if not tenant:
            return []

        user_roles = GranularPermissionService.get_user_roles(user, tenant)
        permissions = set()

        for role in user_roles:
            # Get platform permissions for this role
            platform_perms = PermissionMatrix.objects.filter(
                role=role,
                allowed=True,
            ).values_list("resource", "action")

            for resource, action in platform_perms:
                perm_key = f"{resource}:{action}"

                # Check if overridden at tenant level
                override = TenantPermissionOverride.objects.filter(
                    tenant=tenant,
                    role=role,
                    resource=resource,
                    action=action,
                ).first()

                if override is None or override.allowed:
                    permissions.add(perm_key)

        return sorted(permissions)

    @staticmethod
    def get_role_permissions(role: str) -> list[str]:
        """
        Get all platform-level permissions for a role.

        Args:
            role: The role name

        Returns:
            List of permission strings
        """
        from apps.core.permissions.models import PermissionMatrix

        perms = PermissionMatrix.objects.filter(
            role=role,
            allowed=True,
        ).values_list("resource", "action")

        return [f"{r}:{a}" for r, a in perms]

    @staticmethod
    def override_permission(
        tenant: "Tenant",
        role: str,
        resource: str,
        action: str,
        allowed: bool,
        conditions: Optional[dict[str, Any]] = None,
        created_by: Optional["User"] = None,
    ) -> "TenantPermissionOverride":
        """
        Create or update a tenant-level permission override.

        Args:
            tenant: The tenant to create override for
            role: The role to override
            resource: The resource type
            action: The action
            allowed: Whether to allow or deny
            conditions: Optional conditions
            created_by: The user creating the override

        Returns:
            The created or updated TenantPermissionOverride
        """
        from apps.core.permissions.models import TenantPermissionOverride

        override, created = TenantPermissionOverride.objects.update_or_create(
            tenant=tenant,
            role=role,
            resource=resource,
            action=action,
            defaults={
                "allowed": allowed,
                "conditions": conditions or {},
                "created_by": created_by,
            },
        )

        action_str = "Created" if created else "Updated"
        logger.info(
            f"{action_str} permission override: tenant={tenant.id} "
            f"role={role} {resource}:{action} allowed={allowed}"
        )

        return override

    @staticmethod
    def assign_role(
        user: "User",
        role: str,
        tenant: "Tenant",
        assigned_by: Optional["User"] = None,
        expires_at: Optional[datetime] = None,
    ) -> "UserRoleAssignment":
        """
        Assign a role to a user within a tenant.

        Args:
            user: The user to assign the role to
            role: The role to assign
            tenant: The tenant context
            assigned_by: The user making the assignment
            expires_at: Optional expiration datetime

        Returns:
            The created UserRoleAssignment
        """
        from apps.core.permissions.models import UserRoleAssignment

        assignment, created = UserRoleAssignment.objects.update_or_create(
            tenant=tenant,
            user=user,
            role=role,
            defaults={
                "assigned_by": assigned_by,
                "expires_at": expires_at,
            },
        )

        action_str = "Assigned" if created else "Updated"
        logger.info(
            f"{action_str} role: user={user.id} role={role} "
            f"tenant={tenant.id} expires_at={expires_at}"
        )

        return assignment

    @staticmethod
    def revoke_role(
        user: "User",
        role: str,
        tenant: "Tenant",
    ) -> bool:
        """
        Revoke a role from a user within a tenant.

        Args:
            user: The user to revoke the role from
            role: The role to revoke
            tenant: The tenant context

        Returns:
            True if role was revoked, False if not found
        """
        from apps.core.permissions.models import UserRoleAssignment

        deleted, _ = UserRoleAssignment.objects.filter(
            tenant=tenant,
            user=user,
            role=role,
        ).delete()

        if deleted:
            logger.info(f"Revoked role: user={user.id} role={role} tenant={tenant.id}")
            return True

        return False

    @staticmethod
    def _check_conditions(
        conditions: dict[str, Any],
        user: "User",
        resource_id: Optional[str],
    ) -> bool:
        """
        Check contextual conditions for permission.

        Supported conditions:
        - own_only: User can only access their own resources
        - tenant_match: Resource must belong to user's tenant

        Args:
            conditions: Condition dictionary
            user: The user
            resource_id: Optional resource ID

        Returns:
            True if conditions are met, False otherwise
        """
        if not conditions:
            return True

        # Handle "own_only" condition - user can only access their own resources
        if conditions.get("own_only"):
            if resource_id and str(user.id) != resource_id:
                logger.debug(
                    f"Condition failed: own_only - user={user.id} " f"resource_id={resource_id}"
                )
                return False

        return True
