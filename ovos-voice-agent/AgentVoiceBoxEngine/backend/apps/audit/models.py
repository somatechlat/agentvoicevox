"""
Audit log models for tracking all system changes.

Audit logs are immutable - they cannot be updated or deleted.
"""
import uuid

from django.db import models
from django.utils import timezone

from apps.tenants.models import Tenant


class AuditLogManager(models.Manager):
    """Manager for AuditLog model."""

    def for_tenant(self, tenant: Tenant):
        """Get logs for a specific tenant."""
        return self.filter(tenant=tenant)

    def for_resource(self, resource_type: str, resource_id: str):
        """Get logs for a specific resource."""
        return self.filter(resource_type=resource_type, resource_id=resource_id)

    def for_actor(self, actor_id: str):
        """Get logs for a specific actor."""
        return self.filter(actor_id=actor_id)

    def recent(self, days: int = 30):
        """Get recent logs."""
        cutoff = timezone.now() - timezone.timedelta(days=days)
        return self.filter(created_at__gte=cutoff)


class AuditLog(models.Model):
    """
    Immutable audit log entry.

    Records all significant actions in the system.
    Cannot be updated or deleted after creation.
    """

    class Action(models.TextChoices):
        """Audit action types."""
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
        """Actor types."""
        USER = "user", "User"
        API_KEY = "api_key", "API Key"
        SYSTEM = "system", "System"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Timestamp (immutable)
    created_at = models.DateTimeField(
        default=timezone.now,
        editable=False,
        help_text="When the action occurred",
    )

    # Actor information
    actor_id = models.CharField(
        max_length=255,
        help_text="ID of the actor (user ID, API key ID, or 'system')",
    )
    actor_email = models.EmailField(
        blank=True,
        help_text="Email of the actor (if user)",
    )
    actor_type = models.CharField(
        max_length=20,
        choices=ActorType.choices,
        help_text="Type of actor",
    )

    # Tenant (nullable for system-level actions)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="Tenant context",
    )

    # Request information
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Client user agent",
    )
    request_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Request ID for correlation",
    )

    # Action details
    action = models.CharField(
        max_length=50,
        choices=Action.choices,
        help_text="Action performed",
    )
    resource_type = models.CharField(
        max_length=100,
        help_text="Type of resource affected",
    )
    resource_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID of resource affected",
    )
    description = models.TextField(
        blank=True,
        help_text="Human-readable description",
    )

    # Change tracking
    old_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="Previous values (for updates)",
    )
    new_values = models.JSONField(
        default=dict,
        blank=True,
        help_text="New values (for creates/updates)",
    )

    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context",
    )

    # Manager
    objects = AuditLogManager()

    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["actor_id"]),
            models.Index(fields=["actor_type"]),
            models.Index(fields=["action"]),
            models.Index(fields=["resource_type"]),
            models.Index(fields=["resource_id"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["tenant", "action"]),
        ]

    def __str__(self) -> str:
        return f"{self.action} {self.resource_type} by {self.actor_type}:{self.actor_id}"

    def save(self, *args, **kwargs):
        """
        Override save to enforce immutability.

        Only allows creation, not updates.
        """
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit logs cannot be modified after creation")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Override delete to prevent deletion.

        Audit logs are immutable and cannot be deleted.
        """
        raise ValueError("Audit logs cannot be deleted")

    @classmethod
    def log(
        cls,
        action: str,
        resource_type: str,
        actor_id: str,
        actor_type: str,
        tenant: Tenant = None,
        resource_id: str = "",
        actor_email: str = "",
        ip_address: str = None,
        user_agent: str = "",
        request_id: str = "",
        description: str = "",
        old_values: dict = None,
        new_values: dict = None,
        metadata: dict = None,
    ) -> "AuditLog":
        """
        Create an audit log entry.

        This is the primary method for creating audit logs.
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
        user,
        action: str,
        resource_type: str,
        resource_id: str = "",
        description: str = "",
        old_values: dict = None,
        new_values: dict = None,
        request=None,
    ) -> "AuditLog":
        """
        Log an action performed by a user.

        Convenience method that extracts user and request info.
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
        api_key,
        action: str,
        resource_type: str,
        resource_id: str = "",
        description: str = "",
        old_values: dict = None,
        new_values: dict = None,
        request=None,
    ) -> "AuditLog":
        """
        Log an action performed via API key.

        Convenience method for API key authenticated requests.
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
            actor_email="",
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
        tenant: Tenant = None,
        old_values: dict = None,
        new_values: dict = None,
        metadata: dict = None,
    ) -> "AuditLog":
        """
        Log a system-initiated action.

        For automated processes, scheduled tasks, etc.
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
