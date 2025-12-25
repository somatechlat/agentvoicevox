"""
Core app models.

Imports permission models from the permissions submodule to make them
discoverable by Django's migration system.
"""
from apps.core.permissions.models import (
    PlatformRole,
    ROLE_HIERARCHY,
    PermissionMatrix,
    TenantPermissionOverride,
    UserRoleAssignment,
)

__all__ = [
    "PlatformRole",
    "ROLE_HIERARCHY",
    "PermissionMatrix",
    "TenantPermissionOverride",
    "UserRoleAssignment",
]
