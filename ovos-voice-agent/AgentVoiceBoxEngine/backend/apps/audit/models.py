"""
Audit Log Models for System Activity Tracking
=============================================

This module defines the `AuditLog` model, which is a critical component for
tracking all significant actions and changes within the system. These audit
logs are designed to be immutable, meaning they cannot be altered or deleted
after creation, ensuring a reliable record for security, compliance, and
debugging purposes.
"""

from __future__ import annotations  # For postponed evaluation of type annotations.

import uuid
from typing import TYPE_CHECKING, Any, Optional

from django.db import models
from django.utils import timezone

from apps.tenants.models import Tenant

if TYPE_CHECKING:
    # Avoid circular imports for type hints.
    from apps.api_keys.models import APIKey
    from apps.users.models import User


class AuditLogQuerySet(models.QuerySet):
    """
    Custom QuerySet for the `AuditLog` model.

    Provides convenient, chainable methods for filtering audit logs based on
    common criteria such as tenant, resource, actor, and recency.
    """

    def for_tenant(self, tenant: Tenant) -> AuditLogQuerySet:
        """Filters logs to include only those associated with a specific tenant."""
        return self.filter(tenant=tenant)

    def for_resource(self, resource_type: str, resource_id: str) -> AuditLogQuerySet:
        """Filters logs for actions related to a specific resource."""
        return self.filter(resource_type=resource_type, resource_id=resource_id)

    def for_actor(self, actor_id: str) -> AuditLogQuerySet:
        """Filters logs for actions performed by a specific actor (user ID, API key ID, or 'system')."""
        return self.filter(actor_id=actor_id)

    def recent(self, days: int = 30) -> AuditLogQuerySet:
        """Filters logs to include only those created within the last `days`."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)


class AuditLogManager(models.Manager):
    """
    Custom manager for the `AuditLog` model.

    Utilizes `AuditLogQuerySet` to provide enhanced filtering capabilities
    directly from the manager.
    """

    def get_queryset(self) -> AuditLogQuerySet:
        """Returns the custom `AuditLogQuerySet` for this manager."""
        return AuditLogQuerySet(self.model, using=self._db)

    def for_tenant(self, tenant: Tenant) -> AuditLogQuerySet:
        """Proxy method to `AuditLogQuerySet.for_tenant`."""
        return self.get_queryset().for_tenant(tenant)

    def for_resource(self, resource_type: str, resource_id: str) -> AuditLogQuerySet:
        """Proxy method to `AuditLogQuerySet.for_resource`."""
        return self.get_queryset().for_resource(resource_type, resource_id)

    def for_actor(self, actor_id: str) -> AuditLogQuerySet:
        """Proxy method to `AuditLogQuerySet.for_actor`."""
        return self.get_queryset().for_actor(actor_id)

    def recent(self, days: int = 30) -> AuditLogQuerySet:
        """Proxy method to `AuditLogQuerySet.recent`."""
        return self.get_queryset().recent(days)


class AuditLog(models.Model):
    """
    An immutable record of a significant action performed within the system.

    Audit logs are central to security and compliance, providing a tamper-proof
    history of "who did what, when, and where." Once created, an `AuditLog` entry
    cannot be modified or deleted.
    """

    class Action(models.TextChoices):
        """Defines the types of actions that can be recorded in an audit log."""

        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        API_CALL = "api_call", "API Call"
        PERMISSION_CHANGE = "permission_change", "Permission Change"
        SETTINGS_CHANGE = "settings_change", "Settings Change"
        BILLING_EVENT = "billing_event", "Billing Event"
        SESSION_START = "session_start", "Session Start"
        SESSION_END = "session_end", "Session End"
        KEY_CREATED = "key_created", "API Key Created"
        KEY_REVOKED = "key_revoked", "API Key Revoked"
        KEY_ROTATED = "key_rotated", "API Key Rotated"

    class ActorType(models.TextChoices):
        """Defines the type of entity that performed the action."""

        USER = "user", "User"  # An authenticated user.
        API_KEY = "api_key", "API Key"  # An action via an API key.
        SYSTEM = "system", "System"  # An automated system process.

    # --- Core Identification ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- Timestamp (Immutable) ---
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,  # Ensured to be immutable after creation.
        help_text="The exact UTC timestamp when the auditable action occurred.",
    )

    # --- Actor Information ---
    actor_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The unique identifier of the actor (User ID, API Key ID, or 'system' string).",
    )
    actor_email = models.EmailField(
        blank=True,
        help_text="The email address of the actor, if the actor is a user.",
    )
    actor_type = models.CharField(
        max_length=20,
        choices=ActorType.choices,
        db_index=True,
        help_text="The type of entity that performed the action (User, API_KEY, or System).",
    )

    # --- Contextual Information ---
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,  # If tenant is deleted, logs remain but link is nullified.
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="The tenant associated with the action, or null for system-level actions.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="The IP address from which the request originated.",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="The User-Agent string of the client application making the request.",
    )
    request_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="A unique identifier for the request, useful for correlating logs across services.",
    )

    # --- Action Details ---
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
        db_index=True,
        help_text="The specific action performed (e.g., 'create', 'update', 'login').",
    )
    resource_type = models.CharField(
        max_length=100,
        db_index=True,
        help_text="The type of resource affected by the action (e.g., 'Project', 'User', 'APIKey').",
    )
    resource_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="The ID of the specific resource affected (e.g., UUID of a Project).",
    )
    description = models.TextField(
        blank=True,
        help_text="A human-readable summary or explanation of the action.",
    )

    # --- Change Tracking (for updates) ---
    old_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="A JSON object containing the values of fields *before* an update action.",
    )
    new_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="A JSON object containing the values of fields *after* a create or update action.",
    )

    # --- Additional Metadata ---
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="A flexible JSON field for additional contextual data related to the event.",
    )

    # --- Django Manager ---
    objects = AuditLogManager()

    class Meta:
        """Model metadata options."""

        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor_id"]),
            models.Index(fields=["actor_type"]),
            models.Index(fields=["action"]),
            models.Index(fields=["resource_type"]),
            models.Index(fields=["resource_id"]),
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["tenant", "action"]),
        ]

    def __str__(self) -> str:
        """Returns a string representation of the audit log."""
        tenant_str = f" @ {self.tenant.slug}" if self.tenant else ""
        return f"[{self.created_at.isoformat()}] {self.action} {self.resource_type}:{self.resource_id} by {self.actor_type}:{self.actor_id}{tenant_str}"

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to enforce immutability.

        An `AuditLog` instance can only be created. Any attempt to update
        an existing instance will raise a `ValueError`.
        """
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit logs cannot be modified after creation.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Overrides the default delete method to prevent deletion.

        Audit logs are immutable and cannot be deleted from the system.
        """
        raise ValueError("Audit logs cannot be deleted.")

    @classmethod
    def log(
        cls,
        action: str,
        resource_type: str,
        actor_id: str,
        actor_type: str,
        tenant: Optional[Tenant] = None,
        resource_id: str = "",
        actor_email: str = "",
        ip_address: Optional[str] = None,
        user_agent: str = "",
        request_id: str = "",
        description: str = "",
        old_values: Optional[dict[str, Any]] = None,
        new_values: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Creates and saves a new `AuditLog` entry.

        This is the most general method for creating audit logs. It requires
        explicit specification of all audit trail fields.

        Args:
            action: The type of action performed (from `AuditLog.Action`).
            resource_type: The type of resource affected (e.g., 'Project').
            actor_id: The ID of the entity that performed the action.
            actor_type: The type of actor ('User', 'API_KEY', 'System').
            tenant: (Optional) The Tenant associated with the action.
            resource_id: (Optional) The ID of the specific resource affected.
            actor_email: (Optional) The email of the actor.
            ip_address: (Optional) The IP address of the client.
            user_agent: (Optional) The User-Agent string of the client.
            request_id: (Optional) A correlation ID for the request.
            description: (Optional) A human-readable description of the action.
            old_values: (Optional) Dictionary of values before a change.
            new_values: (Optional) Dictionary of values after a change.
            metadata: (Optional) Additional contextual data.

        Returns:
            The newly created AuditLog instance.
        """
        return cls.objects.create(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=actor_id,
            actor_email=actor_email,
            actor_type=actor_type,
            tenant=tenant,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            description=description,
            old_values=old_values or {},
            new_values=new_values or {},
            metadata=metadata or {},
        )

    @classmethod
    def log_user_action(
        cls,
        user: User,
        action: str,
        resource_type: str,
        resource_id: str = "",
        description: str = "",
        old_values: Optional[dict[str, Any]] = None,
        new_values: Optional[dict[str, Any]] = None,
        request: Optional[Any] = None,
    ) -> AuditLog:
        """
        Creates an audit log entry for an action performed by an authenticated user.

        This convenience method automatically extracts relevant actor and request
        information from the provided `user` and `request` objects.

        Args:
            user: The `User` instance who performed the action.
            action: The type of action performed (from `AuditLog.Action`).
            resource_type: The type of resource affected.
            resource_id: (Optional) The ID of the specific resource affected.
            description: (Optional) A human-readable description.
            old_values: (Optional) Dictionary of values before a change.
            new_values: (Optional) Dictionary of values after a change.
            request: (Optional) The HttpRequest object for extracting IP/User-Agent.

        Returns:
            The newly created AuditLog instance.
        """
        ip_address = None
        user_agent = ""
        request_id = ""

        if request:
            ip_address = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            request_id = getattr(request, "request_id", "")

        return cls.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=str(user.id),
            actor_email=user.email,
            actor_type=cls.ActorType.USER,
            tenant=user.tenant,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
        )

    @classmethod
    def log_api_key_action(
        cls,
        api_key: APIKey,
        action: str,
        resource_type: str,
        resource_id: str = "",
        description: str = "",
        old_values: Optional[dict[str, Any]] = None,
        new_values: Optional[dict[str, Any]] = None,
        request: Optional[Any] = None,
    ) -> AuditLog:
        """
        Creates an audit log entry for an action performed via an API key.

        This convenience method automatically extracts relevant actor and request
        information from the provided `api_key` and `request` objects.

        Args:
            api_key: The `APIKey` instance used for authentication.
            action: The type of action performed (from `AuditLog.Action`).
            resource_type: The type of resource affected.
            resource_id: (Optional) The ID of the specific resource affected.
            description: (Optional) A human-readable description.
            old_values: (Optional) Dictionary of values before a change.
            new_values: (Optional) Dictionary of values after a change.
            request: (Optional) The HttpRequest object for extracting IP/User-Agent.

        Returns:
            The newly created AuditLog instance.
        """
        ip_address = None
        user_agent = ""
        request_id = ""

        if request:
            ip_address = request.META.get("REMOTE_ADDR")
            user_agent = request.META.get("HTTP_USER_AGENT", "")
            request_id = getattr(request, "request_id", "")

        return cls.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id=str(api_key.id),
            actor_email="",  # API keys do not have associated emails.
            actor_type=cls.ActorType.API_KEY,
            tenant=api_key.tenant,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            description=description,
            old_values=old_values,
            new_values=new_values,
        )

    @classmethod
    def log_system_action(
        cls,
        action: str,
        resource_type: str,
        resource_id: str = "",
        description: str = "",
        tenant: Optional[Tenant] = None,
        old_values: Optional[dict[str, Any]] = None,
        new_values: Optional[dict[str, Any]] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Creates an audit log entry for a system-initiated action.

        This method is used for actions performed by automated processes,
        background tasks, or scheduled jobs.

        Args:
            action: The type of action performed (from `AuditLog.Action`).
            resource_type: The type of resource affected.
            resource_id: (Optional) The ID of the specific resource affected.
            description: (Optional) A human-readable description.
            tenant: (Optional) The Tenant associated with the action (e.g., if a system task affects a specific tenant).
            old_values: (Optional) Dictionary of values before a change.
            new_values: (Optional) Dictionary of values after a change.
            metadata: (Optional) Additional contextual data.

        Returns:
            The newly created AuditLog instance.
        """
        return cls.log(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            actor_id="system",
            actor_email="",
            actor_type=cls.ActorType.SYSTEM,
            tenant=tenant,
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata,
        )
