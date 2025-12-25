"""
Granular RBAC Permissions Module.

Provides fine-grained resource:action permission control with:
- 8 platform roles with hierarchical inheritance
- 65+ resource:action permission tuples
- Tenant-level permission overrides
- @require_permission("resource:action") decorator
"""
from apps.core.permissions.models import (
    PlatformRole,
    PermissionMatrix,
    TenantPermissionOverride,
    UserRoleAssignment,
)
from apps.core.permissions.service import GranularPermissionService
from apps.core.permissions.decorators import require_permission, require_granular_role
from apps.core.permissions.auth_bearer import AuthBearer

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
