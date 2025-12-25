"""
Granular Permission Models.

Defines the permission matrix and role assignment models for
fine-grained RBAC with tenant-level overrides.
"""
import uuid
from django.db import models
from django.contrib.postgres.fields import ArrayField


class PlatformRole(models.TextChoices):
    """
    8 platform roles with hierarchical inheritance.
    
    Role Hierarchy (highest to lowest):
    1. saas_admin - Full platform access, cross-tenant operations
    2. tenant_admin - Full tenant access, user management, settings
    3. agent_admin - Agent configuration, persona management
    4. supervisor - Monitor sessions, view analytics, manage operators
    5. operator - Handle live sessions, view assigned conversations
    6. agent_user - Interact with agents, view own conversations
    7. viewer - Read-only access to permitted resources
    8. billing_admin - Billing management, usage reports, invoices
    """
    SAAS_ADMIN = "saas_admin", "SaaS Administrator"
    TENANT_ADMIN = "tenant_admin", "Tenant Administrator"
    AGENT_ADMIN = "agent_admin", "Agent Administrator"
    SUPERVISOR = "supervisor", "Supervisor"
    OPERATOR = "operator", "Operator"
    AGENT_USER = "agent_user", "Agent User"
    VIEWER = "viewer", "Viewer"
    BILLING_ADMIN = "billing_admin", "Billing Administrator"


# Role hierarchy for permission inheritance
ROLE_HIERARCHY = {
    PlatformRole.SAAS_ADMIN: [
        PlatformRole.TENANT_ADMIN,
        PlatformRole.AGENT_ADMIN,
        PlatformRole.SUPERVISOR,
        PlatformRole.OPERATOR,
        PlatformRole.AGENT_USER,
        PlatformRole.VIEWER,
        PlatformRole.BILLING_ADMIN,
    ],
    PlatformRole.TENANT_ADMIN: [
        PlatformRole.AGENT_ADMIN,
        PlatformRole.SUPERVISOR,
        PlatformRole.OPERATOR,
        PlatformRole.AGENT_USER,
        PlatformRole.VIEWER,
    ],
    PlatformRole.AGENT_ADMIN: [
        PlatformRole.SUPERVISOR,
        PlatformRole.OPERATOR,
        PlatformRole.AGENT_USER,
        PlatformRole.VIEWER,
    ],
    PlatformRole.SUPERVISOR: [
        PlatformRole.OPERATOR,
        PlatformRole.AGENT_USER,
        PlatformRole.VIEWER,
    ],
    PlatformRole.OPERATOR: [
        PlatformRole.AGENT_USER,
        PlatformRole.VIEWER,
    ],
    PlatformRole.AGENT_USER: [
        PlatformRole.VIEWER,
    ],
    PlatformRole.VIEWER: [],
    PlatformRole.BILLING_ADMIN: [],  # Billing is a separate branch
}


class PermissionMatrix(models.Model):
    """
    Platform-level permission matrix mapping roles to resource:action tuples.
    Defines the default permissions for each role.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=30, choices=PlatformRole.choices)
    resource = models.CharField(max_length=50)  # e.g., "agents", "sessions", "billing"
    action = models.CharField(max_length=30)    # e.g., "create", "read", "delete"
    allowed = models.BooleanField(default=False)
    conditions = models.JSONField(default=dict, blank=True)  # Optional contextual conditions
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "permission_matrix"
        unique_together = ["role", "resource", "action"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["resource", "action"]),
        ]
        verbose_name = "Permission Matrix Entry"
        verbose_name_plural = "Permission Matrix Entries"
    
    def __str__(self):
        status = "✓" if self.allowed else "✗"
        return f"{self.role}: {self.resource}:{self.action} [{status}]"
    
    @property
    def permission_key(self) -> str:
        """Return the permission as resource:action string."""
        return f"{self.resource}:{self.action}"


class TenantPermissionOverride(models.Model):
    """
    Tenant-level permission overrides.
    Allows tenant admins to customize permissions within their tenant.
    
    Overrides take precedence over platform-level defaults.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="permission_overrides",
    )
    role = models.CharField(max_length=30, choices=PlatformRole.choices)
    resource = models.CharField(max_length=50)
    action = models.CharField(max_length=30)
    allowed = models.BooleanField()
    conditions = models.JSONField(default=dict, blank=True)
    
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="permission_overrides_created",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "tenant_permission_overrides"
        unique_together = ["tenant", "role", "resource", "action"]
        indexes = [
            models.Index(fields=["tenant", "role"]),
        ]
        verbose_name = "Tenant Permission Override"
        verbose_name_plural = "Tenant Permission Overrides"
    
    def __str__(self):
        status = "✓" if self.allowed else "✗"
        return f"{self.tenant.slug}/{self.role}: {self.resource}:{self.action} [{status}]"


class UserRoleAssignment(models.Model):
    """
    User role assignments within a tenant.
    Supports multiple roles per user with optional expiration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.CharField(max_length=30, choices=PlatformRole.choices)
    assigned_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="role_assignments_made",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "user_role_assignments"
        unique_together = ["tenant", "user", "role"]
        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["tenant", "role"]),
            models.Index(fields=["expires_at"]),
        ]
        verbose_name = "User Role Assignment"
        verbose_name_plural = "User Role Assignments"
    
    def __str__(self):
        return f"{self.user.email} -> {self.role} @ {self.tenant.slug}"
    
    @property
    def is_expired(self) -> bool:
        """Check if the role assignment has expired."""
        from django.utils import timezone
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
