"""
Core Application Models
=======================

This module serves as a central point for consolidating models from various
submodules within the `core` app, making them discoverable by Django's
migration system and ensuring they are correctly registered as part of the
`core` application.

It primarily re-exports models related to the platform's permission system.
"""

from apps.core.permissions.models import (
    ROLE_HIERARCHY,
    PermissionMatrix,
    PlatformRole,
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
