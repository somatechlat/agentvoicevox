"""
Granular RBAC Permissions Module.

Provides fine-grained resource:action permission control with:
- 8 platform roles with hierarchical inheritance
- 65+ resource:action permission tuples
- Tenant-level permission overrides
- @require_permission("resource:action") decorator
"""

from apps.core.permissions.auth_bearer import AuthBearer
from apps.core.permissions.decorators import require_granular_role, require_permission
from apps.core.permissions.models import (
    PermissionMatrix,
    PlatformRole,
    TenantPermissionOverride,
    UserRoleAssignment,
)
from apps.core.permissions.service import GranularPermissionService

__all__ = [
    "PlatformRole",
    "PermissionMatrix",
    "TenantPermissionOverride",
    "UserRoleAssignment",
    "GranularPermissionService",
    "require_permission",
    "require_granular_role",
    "AuthBearer",
]
