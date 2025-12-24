"""
Tenant models for multi-tenancy support.

All tenant-scoped models should inherit from TenantScopedModel.
"""
import uuid
from typing import Optional

from django.db import models
from django.db.models import QuerySet
from django.utils import timezone

from apps.core.middleware.tenant import get_current_tenant, get_current_tenant_id


class TenantManager(models.Manager):
    """Manager for Tenant model."""
    
    def active(self) -> QuerySet:
        """Return only active tenants."""
        return self.filter(status=Tenant.Status.ACTIVE)
    
    def get_by_slug(self, slug: str) -> Optional["Tenant"]:
        """Get tenant by slug."""
        try:
            return self.get(slug=slug)
        except Tenant.DoesNotExist:
            return None


class Tenant(models.Model):
    """
    Multi-tenant organization model.
    
    Each tenant represents an organization with isolated data.
    Tenants have tiers that determine their limits and features.
    """
    
    class Tier(models.TextChoices):
        FREE = "free", "Free"
        STARTER = "starter", "Starter"
        PRO = "pro", "Professional"
        ENTERPRISE = "enterprise", "Enterprise"
    
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        PENDING = "pending", "Pending Activation"
        DELETED = "deleted", "Deleted"
    
    # Tier limits configuration
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
    
    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # Basic info
    name = models.CharField(max_length=255, help_text="Organization name")
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-friendly identifier",
    )
    
    # Status and tier
    tier = models.CharField(
        max_length=20,
        choices=Tier.choices,
        default=Tier.FREE,
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )

    # External integrations
    billing_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Lago customer ID",
    )
    keycloak_group_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Keycloak group ID",
    )
    
    # Settings (JSON)
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Tenant-specific settings",
    )
    
    # Tier-based limits (can be overridden per tenant)
    max_users = models.PositiveIntegerField(default=5)
    max_projects = models.PositiveIntegerField(default=3)
    max_api_keys = models.PositiveIntegerField(default=10)
    max_sessions_per_month = models.PositiveIntegerField(default=1000)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Manager
    objects = TenantManager()
    
    class Meta:
        db_table = "tenants"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["tier"]),
            models.Index(fields=["billing_id"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} ({self.slug})"
    
    def save(self, *args, **kwargs):
        """Override save to set tier limits on creation."""
        if not self.pk:
            # Set default limits based on tier
            limits = self.TIER_LIMITS.get(self.tier, self.TIER_LIMITS[self.Tier.FREE])
            self.max_users = limits["max_users"]
            self.max_projects = limits["max_projects"]
            self.max_api_keys = limits["max_api_keys"]
            self.max_sessions_per_month = limits["max_sessions_per_month"]
        super().save(*args, **kwargs)
    
    def activate(self) -> None:
        """Activate the tenant."""
        self.status = self.Status.ACTIVE
        self.activated_at = timezone.now()
        self.save(update_fields=["status", "activated_at", "updated_at"])
    
    def suspend(self, reason: str = "") -> None:
        """Suspend the tenant."""
        self.status = self.Status.SUSPENDED
        self.suspended_at = timezone.now()
        if reason:
            self.settings["suspension_reason"] = reason
        self.save(update_fields=["status", "suspended_at", "settings", "updated_at"])
    
    def soft_delete(self) -> None:
        """Soft delete the tenant."""
        self.status = self.Status.DELETED
        self.deleted_at = timezone.now()
        self.save(update_fields=["status", "deleted_at", "updated_at"])
    
    def upgrade_tier(self, new_tier: str) -> None:
        """Upgrade tenant to a new tier."""
        if new_tier not in self.Tier.values:
            raise ValueError(f"Invalid tier: {new_tier}")
        
        self.tier = new_tier
        limits = self.TIER_LIMITS.get(new_tier, self.TIER_LIMITS[self.Tier.FREE])
        self.max_users = limits["max_users"]
        self.max_projects = limits["max_projects"]
        self.max_api_keys = limits["max_api_keys"]
        self.max_sessions_per_month = limits["max_sessions_per_month"]
        self.save()
    
    @property
    def is_active(self) -> bool:
        """Check if tenant is active."""
        return self.status == self.Status.ACTIVE
    
    @property
    def is_suspended(self) -> bool:
        """Check if tenant is suspended."""
        return self.status == self.Status.SUSPENDED


class TenantSettings(models.Model):
    """
    Extended tenant settings for branding, defaults, and security.
    
    One-to-one relationship with Tenant.
    """
    
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name="extended_settings",
    )
    
    # Branding
    logo_url = models.URLField(blank=True, help_text="Logo URL")
    favicon_url = models.URLField(blank=True, help_text="Favicon URL")
    primary_color = models.CharField(
        max_length=7,
        default="#6366f1",
        help_text="Primary brand color (hex)",
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#8b5cf6",
        help_text="Secondary brand color (hex)",
    )
    
    # Voice defaults
    default_voice_id = models.CharField(
        max_length=100,
        default="af_heart",
        help_text="Default Kokoro voice ID",
    )
    default_stt_model = models.CharField(
        max_length=100,
        default="tiny",
        help_text="Default Whisper STT model",
    )
    default_tts_model = models.CharField(
        max_length=100,
        default="kokoro",
        help_text="Default TTS model",
    )
    default_llm_provider = models.CharField(
        max_length=50,
        default="groq",
        help_text="Default LLM provider",
    )
    default_llm_model = models.CharField(
        max_length=100,
        default="llama-3.3-70b-versatile",
        help_text="Default LLM model",
    )
    
    # Notification preferences
    webhook_url = models.URLField(
        blank=True,
        help_text="Webhook URL for notifications",
    )
    webhook_secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Webhook signing secret (encrypted)",
    )
    email_notifications = models.BooleanField(
        default=True,
        help_text="Enable email notifications",
    )
    slack_webhook_url = models.URLField(
        blank=True,
        help_text="Slack webhook URL",
    )
    
    # Security settings
    require_mfa = models.BooleanField(
        default=False,
        help_text="Require MFA for all users",
    )
    session_timeout_minutes = models.PositiveIntegerField(
        default=1440,  # 24 hours
        help_text="Session timeout in minutes",
    )
    allowed_ip_ranges = models.JSONField(
        default=list,
        blank=True,
        help_text="Allowed IP ranges (CIDR notation)",
    )
    api_key_expiry_days = models.PositiveIntegerField(
        default=365,
        help_text="Default API key expiry in days",
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = "tenant_settings"
        verbose_name = "Tenant Settings"
        verbose_name_plural = "Tenant Settings"
    
    def __str__(self) -> str:
        return f"Settings for {self.tenant.name}"


class TenantScopedManager(models.Manager):
    """
    Manager that automatically filters by current tenant.
    
    All queries through this manager will only return records
    belonging to the current tenant.
    """
    
    def get_queryset(self) -> QuerySet:
        """Filter queryset by current tenant."""
        qs = super().get_queryset()
        tenant_id = get_current_tenant_id()
        if tenant_id:
            return qs.filter(tenant_id=tenant_id)
        return qs
    
    def all_tenants(self) -> QuerySet:
        """Return queryset without tenant filtering (admin use only)."""
        return super().get_queryset()


class TenantScopedModel(models.Model):
    """
    Abstract base model for tenant-scoped data.
    
    All models that should be isolated per tenant should inherit from this.
    Automatically sets tenant on save and filters queries by tenant.
    """
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="%(class)s_set",
        editable=False,
    )
    
    # Use tenant-scoped manager by default
    objects = TenantScopedManager()
    
    # Keep unscoped manager for admin access
    all_objects = models.Manager()
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Auto-set tenant from context if not provided."""
        if not self.tenant_id:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                raise ValueError("Tenant context required for TenantScopedModel")
        super().save(*args, **kwargs)
