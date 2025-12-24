"""
API Key models for programmatic access.

API keys provide authentication for the Realtime API.
"""
import hashlib
import secrets
import uuid
from typing import Optional

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from apps.tenants.models import TenantScopedManager, TenantScopedModel


class APIKeyManager(TenantScopedManager):
    """Manager for APIKey model."""

    def active(self):
        """Return only active (non-revoked, non-expired) keys."""
        now = timezone.now()
        return self.filter(revoked_at__isnull=True).exclude(
            expires_at__lt=now,
        )

    def get_by_prefix(self, prefix: str) -> Optional["APIKey"]:
        """Get API key by prefix."""
        try:
            return self.get(key_prefix=prefix)
        except APIKey.DoesNotExist:
            return None


class APIKey(TenantScopedModel):
    """
    API key for programmatic access.

    Keys are hashed before storage. The full key is only
    returned once at creation time.
    """

    class Scope(models.TextChoices):
        """API key scopes."""
        REALTIME = "realtime", "Realtime API"
        BILLING = "billing", "Billing API"
        ADMIN = "admin", "Admin API"

    class RateLimitTier(models.TextChoices):
        """Rate limit tiers."""
        STANDARD = "standard", "Standard (60/min)"
        ELEVATED = "elevated", "Elevated (120/min)"
        UNLIMITED = "unlimited", "Unlimited"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Basic info
    name = models.CharField(
        max_length=255,
        help_text="API key name",
    )
    description = models.TextField(
        blank=True,
        help_text="API key description",
    )

    # Key data
    key_prefix = models.CharField(
        max_length=12,
        db_index=True,
        help_text="First 8 chars for identification (avb_xxxx)",
    )
    key_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash of the full key",
    )

    # Project association (optional)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="api_keys",
        help_text="Associated project (optional)",
    )

    # Scopes and permissions
    scopes = ArrayField(
        models.CharField(max_length=20),
        default=list,
        help_text="API key scopes",
    )
    rate_limit_tier = models.CharField(
        max_length=20,
        choices=RateLimitTier.choices,
        default=RateLimitTier.STANDARD,
        help_text="Rate limit tier",
    )

    # Expiration and revocation
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Key expiration time",
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Key revocation time",
    )
    revoked_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_api_keys",
        help_text="User who revoked the key",
    )
    revocation_reason = models.TextField(
        blank=True,
        help_text="Reason for revocation",
    )

    # Usage tracking
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Last usage time",
    )
    last_used_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Last usage IP address",
    )
    usage_count = models.PositiveIntegerField(
        default=0,
        help_text="Total usage count",
    )

    # Ownership
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_api_keys",
        help_text="User who created the key",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Manager
    objects = APIKeyManager()

    class Meta:
        db_table = "api_keys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["key_prefix"]),
            models.Index(fields=["key_hash"]),
            models.Index(fields=["expires_at"]),
            models.Index(fields=["revoked_at"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["tenant", "revoked_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.key_prefix}...)"

    @classmethod
    def generate_key(cls) -> tuple:
        """
        Generate a new API key.

        Returns:
            Tuple of (full_key, prefix, hash)
        """
        # Generate 32 random bytes (256 bits)
        random_bytes = secrets.token_bytes(32)
        random_hex = random_bytes.hex()

        # Format: avb_{64_hex_chars}
        full_key = f"avb_{random_hex}"

        # Prefix for identification (avb_ + first 8 chars)
        prefix = full_key[:12]

        # SHA-256 hash for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        return full_key, prefix, key_hash

    @classmethod
    def hash_key(cls, key: str) -> str:
        """Hash an API key for comparison."""
        return hashlib.sha256(key.encode()).hexdigest()

    @property
    def is_active(self) -> bool:
        """Check if key is active (not revoked, not expired)."""
        if self.revoked_at:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if not self.expires_at:
            return False
        return self.expires_at < timezone.now()

    @property
    def is_revoked(self) -> bool:
        """Check if key is revoked."""
        return self.revoked_at is not None

    def revoke(self, user=None, reason: str = "") -> None:
        """Revoke the API key."""
        self.revoked_at = timezone.now()
        self.revoked_by = user
        self.revocation_reason = reason
        self.save(update_fields=[
            "revoked_at",
            "revoked_by",
            "revocation_reason",
            "updated_at",
        ])

    def record_usage(self, ip_address: str = None) -> None:
        """Record API key usage."""
        self.last_used_at = timezone.now()
        if ip_address:
            self.last_used_ip = ip_address
        self.usage_count += 1
        self.save(update_fields=[
            "last_used_at",
            "last_used_ip",
            "usage_count",
            "updated_at",
        ])

    def has_scope(self, scope: str) -> bool:
        """Check if key has a specific scope."""
        return scope in self.scopes

    def get_rate_limit(self) -> int:
        """Get rate limit per minute based on tier."""
        limits = {
            self.RateLimitTier.STANDARD: 60,
            self.RateLimitTier.ELEVATED: 120,
            self.RateLimitTier.UNLIMITED: 0,  # 0 means unlimited
        }
        return limits.get(self.rate_limit_tier, 60)
