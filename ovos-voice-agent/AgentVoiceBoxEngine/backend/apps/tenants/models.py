"""
Tenant Models for Multi-Tenancy Architecture
===========================================

This module is the cornerstone of the application's multi-tenancy architecture.
It defines the `Tenant` model, which represents an isolated customer account,
and the abstract `TenantScopedModel` and `TenantScopedManager` that enforce
data separation throughout the application.
"""

import uuid
from typing import Optional

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from apps.core.middleware.tenant import get_current_tenant, get_current_tenant_id


class TenantManager(models.Manager):
    """
    Custom manager for the Tenant model itself.

    Provides helper methods for querying tenants, such as filtering for active
    tenants or retrieving a tenant by its unique slug.
    """

    def active(self) -> QuerySet:
        """Returns a queryset containing only active tenants."""
        return self.filter(status=Tenant.Status.ACTIVE)

    def get_by_slug(self, slug: str) -> Optional["Tenant"]:
        """
        Retrieves a tenant by its URL-friendly slug.

        Args:
            slug: The unique slug of the tenant.

        Returns:
            A Tenant instance if found, otherwise None.
        """
        try:
            return self.get(slug=slug)
        except Tenant.DoesNotExist:
            return None


class Tenant(models.Model):
    """
    Represents a single tenant, typically an organization or a customer account.

    Each tenant's data is isolated from others via the `TenantScopedModel` and
    `TenantScopedManager`. This model stores the tenant's identity, status,
    billing tier, and integration IDs for external services like billing and
    authentication providers.
    """

    class Tier(models.TextChoices):
        """Enumeration for tenant billing/subscription tiers."""

        FREE = "free", "Free"
        STARTER = "starter", "Starter"
        PRO = "pro", "Professional"
        ENTERPRISE = "enterprise", "Enterprise"

    class Status(models.TextChoices):
        """Enumeration for the lifecycle status of a tenant account."""

        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        PENDING = "pending", "Pending Activation"
        DELETED = "deleted", "Deleted"

    # Static mapping of tiers to their default resource limits.
    TIER_LIMITS = {
        Tier.FREE: {
            "max_users": 3,
            "max_projects": 1,
            "max_api_keys": 5,
            "max_sessions_per_month": 100,
        },
        Tier.STARTER: {
            "max_users": 10,
            "max_projects": 5,
            "max_api_keys": 20,
            "max_sessions_per_month": 1000,
        },
        Tier.PRO: {
            "max_users": 50,
            "max_projects": 20,
            "max_api_keys": 100,
            "max_sessions_per_month": 10000,
        },
        Tier.ENTERPRISE: {
            "max_users": 500,
            "max_projects": 100,
            "max_api_keys": 500,
            "max_sessions_per_month": 100000,
        },
    }

    # --- Core Identification ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255, help_text="The legal or display name of the organization."
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="A URL-friendly identifier for the tenant, used in subdomains or paths.",
    )

    # --- Status and Billing Tier ---
    tier = models.CharField(
        max_length=20,
        choices=Tier.choices,
        default=Tier.FREE,
        help_text="The current subscription tier of the tenant.",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="The current lifecycle status of the tenant account.",
    )

    # --- External Service Integration IDs ---
    billing_id = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="The customer ID from the external billing system (e.g., Lago, Stripe).",
    )
    keycloak_group_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="The corresponding group ID in Keycloak used to manage user membership.",
    )

    # --- Configuration and Limits ---
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="A flexible JSON field for storing miscellaneous tenant-specific settings.",
    )
    max_users = models.PositiveIntegerField(
        default=5,
        help_text="The maximum number of users this tenant can have. Overrides the tier default.",
    )
    max_projects = models.PositiveIntegerField(
        default=3, help_text="The maximum number of projects this tenant can create."
    )
    max_api_keys = models.PositiveIntegerField(
        default=10, help_text="The maximum number of active API keys this tenant can have."
    )
    max_sessions_per_month = models.PositiveIntegerField(
        default=1000, help_text="The monthly session usage limit for this tenant."
    )

    # --- Timestamps for Lifecycle Events ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when the tenant first became active."
    )
    suspended_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when the tenant was last suspended."
    )
    deleted_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when the tenant was soft-deleted."
    )

    # --- Django Manager ---
    objects = TenantManager()

    class Meta:
        """Model metadata options."""

        db_table = "tenants"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["tier"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """Returns a string representation of the tenant."""
        return f"{self.name} ({self.slug})"

    def save(self, *args, **kwargs):
        """
        Overrides the default save method to set initial tier limits upon creation.

        When a new Tenant is created (i.e., it has no primary key), this method
        populates its resource limits (`max_users`, etc.) based on the default
        values defined in the `TIER_LIMITS` dictionary for its assigned tier.
        """
        if not self.pk:
            limits = self.TIER_LIMITS.get(self.tier, self.TIER_LIMITS[self.Tier.FREE])
            self.max_users = limits["max_users"]
            self.max_projects = limits["max_projects"]
            self.max_api_keys = limits["max_api_keys"]
            self.max_sessions_per_month = limits["max_sessions_per_month"]
        super().save(*args, **kwargs)

    def activate(self) -> None:
        """Sets the tenant's status to 'ACTIVE' and records the activation time."""
        self.status = self.Status.ACTIVE
        self.activated_at = timezone.now()
        self.save(update_fields=["status", "activated_at", "updated_at"])

    def suspend(self, reason: str = "") -> None:
        """
        Sets the tenant's status to 'SUSPENDED' and records the suspension time.

        Args:
            reason: (Optional) A string explaining why the tenant was suspended.
        """
        self.status = self.Status.SUSPENDED
        self.suspended_at = timezone.now()
        if reason:
            self.settings["suspension_reason"] = reason
        self.save(update_fields=["status", "suspended_at", "settings", "updated_at"])

    def soft_delete(self) -> None:
        """Performs a soft delete by setting the status to 'DELETED'."""
        self.status = self.Status.DELETED
        self.deleted_at = timezone.now()
        self.save(update_fields=["status", "deleted_at", "updated_at"])

    def upgrade_tier(self, new_tier: str) -> None:
        """
        Upgrades or downgrades the tenant to a new tier and updates resource limits.

        Args:
            new_tier: The target tier, which must be a valid choice from `Tenant.Tier`.

        Raises:
            ValueError: If `new_tier` is not a valid tier.
        """
        if new_tier not in self.Tier.values:
            raise ValueError(f"Invalid tier: {new_tier}")

        self.tier = new_tier
        limits = self.TIER_LIMITS.get(self.Tier(new_tier), self.TIER_LIMITS[self.Tier.FREE])
        self.max_users = limits["max_users"]
        self.max_projects = limits["max_projects"]
        self.max_api_keys = limits["max_api_keys"]
        self.max_sessions_per_month = limits["max_sessions_per_month"]
        self.save()

    @property
    def is_active(self) -> bool:
        """Returns True if the tenant's status is 'ACTIVE'."""
        return self.status == self.Status.ACTIVE

    @property
    def is_suspended(self) -> bool:
        """Returns True if the tenant's status is 'SUSPENDED'."""
        return self.status == self.Status.SUSPENDED


class TenantSettings(models.Model):
    """
    Stores extended, optional settings for a tenant.

    This model uses a OneToOneField to the `Tenant` model to provide a separate
    table for settings related to branding, feature defaults, notifications, and
    security policies. This keeps the core `Tenant` model cleaner.
    """

    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="extended_settings",
    )

    # --- Branding Customization ---
    logo_url = models.URLField(blank=True, help_text="URL for a custom logo to display in the UI.")
    favicon_url = models.URLField(blank=True, help_text="URL for a custom favicon.")
    primary_color = models.CharField(
        max_length=7,
        default="#6366f1",
        help_text="Primary brand color in hex format (e.g., #6366f1).",
    )
    secondary_color = models.CharField(
        max_length=7, default="#8b5cf6", help_text="Secondary brand color in hex format."
    )

    # --- Feature Defaults: Voice ---
    default_voice_id = models.CharField(
        max_length=100, default="af_heart", help_text="Default TTS voice ID for new personas."
    )
    default_stt_model = models.CharField(
        max_length=100, default="tiny", help_text="Default STT model for new personas."
    )
    default_stt_language = models.CharField(
        max_length=10, default="en", help_text="Default STT language for new personas."
    )
    stt_vad_enabled = models.BooleanField(
        default=True, help_text="Default state for voice activity detection."
    )
    stt_beam_size = models.PositiveIntegerField(
        default=5, help_text="Default beam search size for STT processing."
    )
    default_tts_model = models.CharField(
        max_length=100, default="kokoro", help_text="Default TTS provider/model."
    )
    default_llm_provider = models.CharField(
        max_length=50, default="groq", help_text="Default LLM provider for new personas."
    )
    default_llm_model = models.CharField(
        max_length=100,
        default="llama-3.3-70b-versatile",
        help_text="Default LLM model for new personas.",
    )
    default_llm_temperature = models.FloatField(default=0.7, help_text="Default LLM temperature.")
    default_llm_max_tokens = models.PositiveIntegerField(
        default=1024, help_text="Default LLM max tokens."
    )

    # --- Notification Settings ---
    webhook_url = models.URLField(blank=True, help_text="URL to send event notifications to.")
    webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Signing secret to verify webhook payloads (should be stored encrypted).",
    )
    email_notifications = models.BooleanField(
        default=True, help_text="Master switch for enabling or disabling email notifications."
    )
    slack_webhook_url = models.URLField(
        blank=True, help_text="URL for sending notifications to a Slack channel."
    )

    # --- Security Policies ---
    require_mfa = models.BooleanField(
        default=False,
        help_text="If true, all users in the tenant must have multi-factor authentication enabled.",
    )
    session_timeout_minutes = models.PositiveIntegerField(
        default=1440, help_text="Idle session timeout for users in this tenant."
    )
    allowed_ip_ranges = models.JSONField(
        default=list,
        blank=True,
        help_text="A list of allowed IP addresses or CIDR ranges for accessing the tenant's resources.",
    )
    api_key_expiry_days = models.PositiveIntegerField(
        default=365, help_text="The default lifespan in days for newly generated API keys."
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata options."""

        db_table = "tenant_settings"
        verbose_name = "Tenant Settings"
        verbose_name_plural = "Tenant Settings"

    def __str__(self) -> str:
        """Returns a string representation of the tenant settings."""
        return f"Settings for {self.tenant.name}"


class TenantScopedManager(models.Manager):
    """
    A Django model manager that enforces tenant isolation at the query level.

    When used as the default manager (`objects`) on a `TenantScopedModel`, all
    queries (e.g., `MyModel.objects.all()`, `MyModel.objects.filter(...)`) are
    automatically filtered to include only records belonging to the currently
    active tenant. The current tenant is retrieved from middleware context.
    """

    def get_queryset(self) -> QuerySet:
        """
        Overrides the default queryset to apply tenant filtering.

        It retrieves the current tenant's ID from the request context (via middleware)
        and injects a `.filter(tenant_id=...)` clause into every query.
        If no tenant ID is found in the context (e.g., in a background task or
        system-level operation), it returns the unfiltered queryset, which should
        be handled with care.
        """
        qs = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id:
            return qs.filter(tenant_id=tenant_id)
        return qs


class TenantScopedModel(models.Model):
    """
    An abstract base model that provides automatic tenant scoping.

    Any model that inherits from `TenantScopedModel` will automatically get:
    1.  A non-nullable `tenant` ForeignKey to the `Tenant` model.
    2.  A default manager (`objects`) of type `TenantScopedManager`, which
        restricts all queries to the current tenant.
    3.  A secondary manager (`all_objects`) that bypasses tenant scoping,
        intended for administrative or system-level use.
    4.  An overridden `save()` method that automatically assigns the current
        tenant when a new object is created.

    This is the primary mechanism for ensuring data isolation in the application.
    """

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        editable=False,
    )

    # The default manager that enforces tenant isolation.
    objects = TenantScopedManager()
    # An "escape hatch" manager to query across all tenants.
    all_objects = models.Manager()

    class Meta:
        """Model metadata options."""

        abstract = True

    def save(self, *args, **kwargs):
        """
        Overrides the default save to automatically associate the model
        instance with the current tenant upon creation.
        """
        # If the object is new (`self.tenant_id` is not set)
        if not self.tenant_id:
            # Retrieve the current tenant from middleware context.
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                # This check prevents creating "orphaned" records without a tenant.
                raise ValueError("Tenant context is required to save a TenantScopedModel instance.")
        super().save(*args, **kwargs)
