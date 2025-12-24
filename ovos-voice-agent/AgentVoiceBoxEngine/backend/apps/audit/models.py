"""
Audit log models.

Immutable audit logs for tracking all administrative actions.
Logs cannot be updated or deleted once created.
"""
from typing import Any, Dict, Optional
from uuid import UUID

from django.db import models
from django.utils import timezone

from apps.tenants.models import Tenant


class AuditLogManager(models.Manager):
    """Manager for AuditLog with convenience methods."""

    def log(
        self,
        tenant: Optional[Tenant],
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor_email: Optional[str] = None,
        actor_type: str = "user",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        description: str = "",
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
    ) -> "AuditLog":
        """
        Create an audit log entry.

        Args:
            tenant: Tenant the action was performed in
            action: Action type (create, update, delete, etc.)
            resource_type: Type of resource affected
            resource_id: ID of the resource affected
            actor_id: ID of the actor (user or API key)
            actor_email: Email of the actor
            actor_type: Type of actor (user, api_key, system)
            ip_address: IP address of the request
            user_agent: User agent of the request
            description: Human-readable description
            old_values: Previous values (for updates)
            new_values: New values (for creates/updates)

        Returns:
            Created AuditLog instance
        """
        return self.create(
            tenant=tenant,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_type=actor_type,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            old_values=old_values or {},
            new_values=new_values or {},
        )


class AuditLog(models.Model):
    """
    Immutable audit log model.

    Records all administrative actions for compliance and debugging.
    Logs cannot be updated or deleted once created.
    """

    class Action(models.TextChoices):
        """Audit log action types."""

        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        API_CALL = "api_call", "API Call"
        PERMISSION_CHANGE = "permission_change", "Permission Change"
        SETTINGS_CHANGE = "settings_change", "Settings Change"
        BILLING_EVENT = "billing_event", "Billing Event"
        KEY_CREATED = "key_created", "API Key Created"
        KEY_ROTATED = "key_rotated", "API Key Rotated"
        KEY_REVOKED = "key_revoked", "API Key Revoked"

    class ActorType(models.TextChoices):
        """Actor types."""

        USER = "user", "User"
        API_KEY = "api_key", "API Key"
        SYSTEM = "system", "System"

    # Primary key (auto-increment for performance)
    id = models.BigAutoField(primary_key=True)

    # Tenant association (nullable for system-level events)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
        help_text="Tenant this action was performed in",
    )

    # Actor information
    actor_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID of the actor (user ID or API key ID)",
    )
    actor_email = models.EmailField(
        blank=True,
        help_text="Email of the actor",
    )
    actor_type = models.CharField(
        max_length=20,
        choices=ActorType.choices,
        default=ActorType.USER,
        help_text="Type of actor",
    )

    # Request context
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the request",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent of the request",
    )

    # Action details
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
        help_text="Type of action performed",
    )
    resource_type = models.CharField(
        max_length=64,
        help_text="Type of resource affected",
    )
    resource_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID of the resource affected",
    )
    description = models.TextField(
        blank=True,
        help_text="Human-readable description of the action",
    )

    # Change tracking
    old_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Previous values before the change",
    )
    new_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="New values after the change",
    )

    # Timestamp (immutable)
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="When the action was performed",
    )

    # Manager
    objects = AuditLogManager()

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "action"]),
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["actor_id"]),
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.resource_type} by {self.actor_email or self.actor_id}"

    def save(self, *args, **kwargs):
        """
        Override save to enforce immutability.

        Audit logs can only be created, not updated.
        """
        if self.pk is not None:
            raise ValueError("Audit logs cannot be updated")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete to prevent deletion.

        Audit logs cannot be deleted.
        """
        raise ValueError("Audit logs cannot be deleted")
