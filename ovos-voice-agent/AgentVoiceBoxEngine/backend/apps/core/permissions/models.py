"""
Granular Permission Models for Role-Based Access Control (RBAC)
================================================================

This module defines the core models and logic for the application's Role-Based
Access Control (RBAC) system. It supports a hierarchical role structure,
platform-level default permissions, and tenant-specific permission overrides,
enabling fine-grained control over user access to resources and actions.
"""

import uuid

from django.db import models


class PlatformRole(models.TextChoices):
    """
    Defines the set of platform-wide roles available to users.

    These roles have a hierarchical relationship, meaning a higher-level role
    implicitly grants the permissions of lower-level roles within its branch
    of the hierarchy (as defined in `ROLE_HIERARCHY`).
    """

    SAAS_ADMIN = (
        "saas_admin",
        "SaaS Administrator",
    )  # Full platform access, cross-tenant operations.
    TENANT_ADMIN = "tenant_admin", "Tenant Administrator"  # Full access within a specific tenant.
    AGENT_ADMIN = (
        "agent_admin",
        "Agent Administrator",
    )  # Manages agent configurations, personas, etc.
    SUPERVISOR = (
        "supervisor",
        "Supervisor",
    )  # Monitors sessions, views analytics, manages operators.
    OPERATOR = "operator", "Operator"  # Handles live sessions, views assigned conversations.
    AGENT_USER = "agent_user", "Agent User"  # Interacts with agents, views own conversations.
    VIEWER = "viewer", "Viewer"  # Read-only access to permitted resources.
    BILLING_ADMIN = (
        "billing_admin",
        "Billing Administrator",
    )  # Manages billing, usage reports (separate hierarchy).


# Defines the explicit hierarchy of roles.
# A role implicitly inherits all permissions granted to roles lower in its list.
# For example, a SAAS_ADMIN inherits permissions of all other roles.
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
    PlatformRole.VIEWER: [],  # Viewer has no roles below it in this hierarchy.
    PlatformRole.BILLING_ADMIN: [],  # Billing Admin has its own specific permissions and doesn't inherit others.
}


class PermissionMatrix(models.Model):
    """
    Defines the default, platform-level permission rules.

    Each entry in this matrix specifies whether a particular `PlatformRole` is
    `allowed` or `denied` to perform a specific `action` on a given `resource`
    across the entire platform. These serve as the baseline permissions, which
    can be overridden at the tenant level by `TenantPermissionOverride` entries.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(
        max_length=30,
        choices=PlatformRole.choices,
        db_index=True,
        help_text="The platform role to which this permission applies.",
    )
    resource = models.CharField(
        max_length=50,
        db_index=True,
        help_text="The type of resource (e.g., 'projects', 'sessions', 'users', 'billing').",
    )
    action = models.CharField(
        max_length=30,
        db_index=True,
        help_text="The action that can be performed (e.g., 'create', 'read', 'update', 'delete', 'list').",
    )
    allowed = models.BooleanField(
        default=False,
        help_text="True if the role is allowed to perform the action, False otherwise.",
    )
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional contextual conditions (e.g., {'status': 'active'}) under which the permission applies. (Future use)",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata options."""

        db_table = "permission_matrix"
        unique_together = ["role", "resource", "action"]  # Ensures no duplicate permission rules.
        indexes = [
            models.Index(fields=["resource", "action"]),
        ]
        verbose_name = "Permission Matrix Entry"
        verbose_name_plural = "Permission Matrix Entries"

    def __str__(self):
        """Returns a string representation of the permission matrix entry."""
        status = "✓" if self.allowed else "✗"
        return f"{self.role}: {self.resource}:{self.action} [{status}]"

    @property
    def permission_key(self) -> str:
        """
        Returns a string representation of the resource-action pair.
        This is useful for quick lookups in permission checks (e.g., "projects:read").
        """
        return f"{self.resource}:{self.action}"


class TenantPermissionOverride(models.Model):
    """
    Allows tenant administrators to customize default platform permissions
    specifically for their tenant.

    Entries in this model take precedence over the global `PermissionMatrix`
    settings for the associated tenant, providing flexibility for tenant-specific
    access control policies.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,  # If the tenant is deleted, its overrides are also deleted.
        related_name="permission_overrides",
        help_text="The tenant to which this override applies.",
    )
    role = models.CharField(
        max_length=30,
        choices=PlatformRole.choices,
        db_index=True,
        help_text="The role whose permission is being overridden.",
    )
    resource = models.CharField(
        max_length=50, help_text="The resource type (e.g., 'users', 'projects')."
    )
    action = models.CharField(
        max_length=30, help_text="The action (e.g., 'create', 'update', 'delete')."
    )
    allowed = models.BooleanField(
        help_text="True to allow the permission, False to explicitly deny it."
    )
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Optional contextual conditions under which the override applies. (Future use)",
    )

    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,  # Keep the override if the creator user is deleted.
        null=True,
        related_name="permission_overrides_created",
        help_text="The user who created this override.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata options."""

        db_table = "tenant_permission_overrides"
        unique_together = [
            "tenant",
            "role",
            "resource",
            "action",
        ]  # Ensures no duplicate overrides for a tenant.
        indexes = [
            models.Index(fields=["tenant", "role"]),
            models.Index(fields=["tenant", "resource", "action"]),
        ]
        verbose_name = "Tenant Permission Override"
        verbose_name_plural = "Tenant Permission Overrides"

    def __str__(self):
        """Returns a string representation of the tenant permission override."""
        status = "✓" if self.allowed else "✗"
        return f"{self.tenant.slug}/{self.role}: {self.resource}:{self.action} [{status}]"


class UserRoleAssignment(models.Model):
    """
    Manages explicit role assignments for users within a specific tenant.

    While a user's primary role is stored on the `User` model, this table
    allows for additional, temporary, or resource-specific role assignments.
    It supports multiple roles per user per tenant and optional expiration dates.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        "tenants.Tenant",
        on_delete=models.CASCADE,
        related_name="role_assignments",
        help_text="The tenant in which this role is assigned.",
    )
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,  # If the user is deleted, their role assignments are also deleted.
        related_name="role_assignments",
        help_text="The user to whom this role is assigned.",
    )
    role = models.CharField(
        max_length=30,
        choices=PlatformRole.choices,
        db_index=True,
        help_text="The assigned platform role.",
    )
    assigned_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,  # Keep the assignment if the assigner user is deleted.
        null=True,
        related_name="role_assignments_made",
        help_text="The user who assigned this role.",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        null=True, blank=True, help_text="The date and time when this role assignment expires."
    )

    class Meta:
        """Model metadata options."""

        db_table = "user_role_assignments"
        unique_together = [
            "tenant",
            "user",
            "role",
        ]  # Ensures a user has a unique role assignment per tenant.
        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["tenant", "role"]),
            models.Index(fields=["expires_at"]),
        ]
        verbose_name = "User Role Assignment"
        verbose_name_plural = "User Role Assignments"

    def __str__(self):
        """Returns a string representation of the user role assignment."""
        return f"{self.user.email} -> {self.role} @ {self.tenant.slug}"

    @property
    def is_expired(self) -> bool:
        """
        Checks if the role assignment has passed its `expires_at` date.
        Returns False if `expires_at` is not set.
        """
        from django.utils import timezone

        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at
