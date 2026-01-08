"""
Management command to seed the permission matrix.

Seeds 65+ resource:action permission tuples for all 8 platform roles.

Usage:
    python manage.py seed_permission_matrix
    python manage.py seed_permission_matrix --clear  # Clear existing and reseed
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.permissions.models import PermissionMatrix, PlatformRole

# Permission matrix definition
# Format: (resource, action, {role: allowed, ...})
# "own" in conditions means user can only access their own resources
PERMISSION_MATRIX = [
    # ==========================================================================
    # TENANT RESOURCES
    # ==========================================================================
    (
        "tenants",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.AGENT_USER: True,
            PlatformRole.VIEWER: True,
            PlatformRole.BILLING_ADMIN: True,
        },
    ),
    (
        "tenants",
        "update",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "tenants",
        "delete",
        {
            PlatformRole.SAAS_ADMIN: True,
        },
    ),
    (
        "tenants",
        "manage_users",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "tenants",
        "manage_settings",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "tenants",
        "view_audit",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # USER RESOURCES
    # ==========================================================================
    (
        "users",
        "create",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "users",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "users",
        "update",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "users",
        "delete",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "users",
        "assign_roles",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # AGENT RESOURCES
    # ==========================================================================
    (
        "agents",
        "create",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "agents",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.AGENT_USER: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "agents",
        "update",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "agents",
        "delete",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "agents",
        "deploy",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "agents",
        "configure",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # PERSONA RESOURCES
    # ==========================================================================
    (
        "personas",
        "create",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "personas",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.AGENT_USER: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "personas",
        "update",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "personas",
        "delete",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "personas",
        "assign",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
        },
    ),
    # ==========================================================================
    # SESSION RESOURCES
    # ==========================================================================
    (
        "sessions",
        "create",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.AGENT_USER: True,
        },
    ),
    (
        "sessions",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.VIEWER: True,
        },
        {"own_only": False},
    ),  # agent_user handled separately with own_only
    (
        "sessions",
        "update",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
        },
    ),
    (
        "sessions",
        "terminate",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
        },
    ),
    (
        "sessions",
        "monitor",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "sessions",
        "takeover",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
        },
    ),
    # ==========================================================================
    # CONVERSATION RESOURCES
    # ==========================================================================
    (
        "conversations",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "conversations",
        "export",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
        },
    ),
    (
        "conversations",
        "delete",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "conversations",
        "annotate",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
        },
    ),
    # ==========================================================================
    # API KEY RESOURCES
    # ==========================================================================
    (
        "api_keys",
        "create",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "api_keys",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "api_keys",
        "revoke",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "api_keys",
        "rotate",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # PROJECT RESOURCES
    # ==========================================================================
    (
        "projects",
        "create",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "projects",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.AGENT_USER: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "projects",
        "update",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "projects",
        "delete",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "projects",
        "manage_members",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # VOICE RESOURCES
    # ==========================================================================
    (
        "voice",
        "configure",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "voice",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.AGENT_USER: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "voice",
        "test",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
        },
    ),
    (
        "voice",
        "deploy",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # THEME RESOURCES
    # ==========================================================================
    (
        "themes",
        "create",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "themes",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.AGENT_USER: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "themes",
        "update",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "themes",
        "delete",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "themes",
        "apply",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # BILLING RESOURCES
    # ==========================================================================
    (
        "billing",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.BILLING_ADMIN: True,
        },
    ),
    (
        "billing",
        "manage",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.BILLING_ADMIN: True,
        },
    ),
    (
        "billing",
        "export",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.BILLING_ADMIN: True,
        },
    ),
    (
        "billing",
        "configure_plans",
        {
            PlatformRole.SAAS_ADMIN: True,
        },
    ),
    # ==========================================================================
    # ANALYTICS RESOURCES
    # ==========================================================================
    (
        "analytics",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.VIEWER: True,
            PlatformRole.BILLING_ADMIN: True,
        },
    ),
    (
        "analytics",
        "export",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.BILLING_ADMIN: True,
        },
    ),
    (
        "analytics",
        "configure",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # AUDIT RESOURCES
    # ==========================================================================
    (
        "audit",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "audit",
        "export",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    # ==========================================================================
    # NOTIFICATION RESOURCES
    # ==========================================================================
    (
        "notifications",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.AGENT_USER: True,
            PlatformRole.VIEWER: True,
            PlatformRole.BILLING_ADMIN: True,
        },
    ),
    (
        "notifications",
        "configure",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
        },
    ),
    (
        "notifications",
        "send",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
        },
    ),
    # ==========================================================================
    # WORKFLOW RESOURCES
    # ==========================================================================
    (
        "workflows",
        "create",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
        },
    ),
    (
        "workflows",
        "read",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
            PlatformRole.VIEWER: True,
        },
    ),
    (
        "workflows",
        "execute",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
            PlatformRole.OPERATOR: True,
        },
    ),
    (
        "workflows",
        "cancel",
        {
            PlatformRole.SAAS_ADMIN: True,
            PlatformRole.TENANT_ADMIN: True,
            PlatformRole.AGENT_ADMIN: True,
            PlatformRole.SUPERVISOR: True,
        },
    ),
    # ==========================================================================
    # ADMIN RESOURCES (SaaS Admin only)
    # ==========================================================================
    (
        "admin",
        "platform_settings",
        {
            PlatformRole.SAAS_ADMIN: True,
        },
    ),
    (
        "admin",
        "tenant_management",
        {
            PlatformRole.SAAS_ADMIN: True,
        },
    ),
    (
        "admin",
        "user_impersonation",
        {
            PlatformRole.SAAS_ADMIN: True,
        },
    ),
    (
        "admin",
        "system_health",
        {
            PlatformRole.SAAS_ADMIN: True,
        },
    ),
]


class Command(BaseCommand):
    """
    Management command to seed the permission matrix with predefined rules.

    This command populates the `PermissionMatrix` table with a comprehensive set
    of resource-action permissions for various platform roles. It ensures that
    the application's Role-Based Access Control (RBAC) system has a foundational
    set of rules.
    """

    help = "Seed the permission matrix with 65+ resource:action permission tuples"

    def add_arguments(self, parser):
        """
        Adds command-line arguments to the management command.

        Args:
            parser: The argument parser object.
        """
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing permission matrix before seeding",
        )

    def handle(self, *args, **options):
        """
        Executes the command to seed or reseed the permission matrix.

        This method orchestrates the creation and update of permission entries
        based on the `PERMISSION_MATRIX` constant. It also handles clearing
        existing entries if the `--clear` option is provided.
        """
        clear = options.get("clear", False)

        with transaction.atomic():
            if clear:
                deleted_count, _ = PermissionMatrix.objects.all().delete()
                self.stdout.write(
                    self.style.WARNING(f"Cleared {deleted_count} existing permissions")
                )

            created_count = 0
            updated_count = 0
            skipped_count = 0

            for entry in PERMISSION_MATRIX:
                if len(entry) == 3:
                    resource, action, role_permissions = entry
                    conditions = {}
                elif len(entry) == 4:
                    resource, action, role_permissions, conditions = entry
                else:
                    self.stdout.write(
                        self.style.ERROR(f"Invalid entry format: {entry}")
                    )
                    continue

                for role, allowed in role_permissions.items():
                    perm, created = PermissionMatrix.objects.update_or_create(
                        role=role,
                        resource=resource,
                        action=action,
                        defaults={
                            "allowed": allowed,
                            "conditions": conditions,
                        },
                    )

                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

            # Also create entries for roles not explicitly listed (as denied)
            all_roles = [r.value for r in PlatformRole]
            for entry in PERMISSION_MATRIX:
                if len(entry) >= 3:
                    resource, action, role_permissions = entry[:3]
                    conditions = entry[3] if len(entry) == 4 else {}

                    for role in all_roles:
                        if role not in role_permissions:
                            perm, created = PermissionMatrix.objects.get_or_create(
                                role=role,
                                resource=resource,
                                action=action,
                                defaults={
                                    "allowed": False,
                                    "conditions": {},
                                },
                            )
                            if created:
                                skipped_count += 1

            total = PermissionMatrix.objects.count()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Permission matrix seeded successfully!\n"
                    f"  Created: {created_count}\n"
                    f"  Updated: {updated_count}\n"
                    f"  Denied entries: {skipped_count}\n"
                    f"  Total: {total}"
                )
            )

            # Print summary by role
            self.stdout.write("\nPermissions by role:")
            for role in PlatformRole:
                allowed = PermissionMatrix.objects.filter(
                    role=role.value, allowed=True
                ).count()
                self.stdout.write(f"  {role.label}: {allowed} permissions")
