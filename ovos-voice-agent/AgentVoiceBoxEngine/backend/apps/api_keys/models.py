"""
API Key Models for Programmatic Access
======================================

This module defines the `APIKey` model, which is used to provide secure,
programmatic access to the platform's Realtime API and other services.
API keys are tenant-scoped, hashed for security, and support features like
scopes, rate limiting, and revocation.
"""

import hashlib
import secrets
import uuid
from typing import TYPE_CHECKING, Optional

from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from apps.tenants.models import TenantScopedManager, TenantScopedModel

if TYPE_CHECKING:
    from apps.users.models import User


class APIKeyManager(TenantScopedManager):
    """
    Custom manager for the APIKey model.

    Inherits from `TenantScopedManager` to ensure all queries are filtered
    by the current tenant. Provides additional helper methods for querying
    active or specific keys.
    """

    def active(self):
        """
        Returns a queryset of active API keys for the current tenant.

        An API key is considered active if it has not been revoked and,
        if an `expires_at` date is set, has not yet expired.
        """
        now = timezone.now()
        return self.filter(revoked_at__isnull=True).exclude(
            expires_at__lt=now,
        )

    def get_by_prefix(self, prefix: str) -> Optional["APIKey"]:
        """
        Retrieves an API key by its unique prefix.

        This is typically used during authentication to quickly locate a key
        without revealing the full key.

        Args:
            prefix: The unique prefix of the API key (e.g., 'avb_xxxx').

        Returns:
            An APIKey instance if found, otherwise None.
        """
        try:
            return self.get(key_prefix=prefix)
        except APIKey.DoesNotExist:
            return None


class APIKey(TenantScopedModel):
    """
    Represents an API key used for authenticating programmatic access.

    For security, the full API key is never stored directly in the database.
    Instead, a hash of the key is stored, and the full key is only returned
    once at creation time. API keys are associated with a tenant and optionally
    a specific project, and can have scopes, rate limit tiers, and expiration/revocation
    rules.
    """

    class Scope(models.TextChoices):
        """Defines the permissions or functionalities an API key grants access to."""

        REALTIME = "realtime", "Realtime API"  # Access to real-time voice sessions.
        BILLING = "billing", "Billing API"  # Access to billing and usage data.
        ADMIN = (
            "admin",
            "Admin API",
        )  # Administrative operations (e.g., user management).

    class RateLimitTier(models.TextChoices):
        """Defines the rate limiting policy applied to an API key."""

        STANDARD = "standard", "Standard (60 requests/minute)"
        ELEVATED = "elevated", "Elevated (120 requests/minute)"
        UNLIMITED = "unlimited", "Unlimited"  # No rate limit applied.

    # --- Core Identification ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=255, help_text="A human-readable name for the API key."
    )
    description = models.TextField(
        blank=True, help_text="An optional description of the API key's purpose."
    )

    # --- Key Data (Securely Stored) ---
    key_prefix = models.CharField(
        max_length=12,
        unique=True,  # Ensures quick lookup and uniqueness.
        db_index=True,
        help_text="The first few characters of the full API key, used for identification (e.g., 'avb_xxxx').",
    )
    key_hash = models.CharField(
        max_length=64,
        help_text="The SHA-256 hash of the full API key, used for secure storage and verification.",
    )

    # --- Association and Permissions ---
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="api_keys",
        help_text="The specific project this API key grants access to. If null, grants access across the tenant.",
    )
    scopes = ArrayField(
        models.CharField(max_length=20),
        default=list,
        blank=True,  # Allow empty list if no specific scopes are granted.
        help_text="A list of specific API scopes this key is authorized for (e.g., 'realtime').",
    )
    rate_limit_tier = models.CharField(
        max_length=20,
        choices=RateLimitTier.choices,
        default=RateLimitTier.STANDARD,
        help_text="The rate limit tier applied to requests made with this key.",
    )

    # --- Expiration and Revocation Management ---
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time after which the API key becomes invalid.",
    )
    revoked_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="The date and time this API key was explicitly revoked.",
    )
    revoked_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_api_keys",
        help_text="The user who performed the revocation, if applicable.",
    )
    revocation_reason = models.TextField(
        blank=True,
        help_text="An optional text description for the reason of revocation.",
    )

    # --- Usage Tracking and Ownership ---
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of the last successful API call made with this key.",
    )
    last_used_ip = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address from which the last successful API call was made.",
    )
    usage_count = models.PositiveIntegerField(
        default=0, help_text="Total number of API calls made using this key."
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_api_keys",
        help_text="The user who initially created this API key.",
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # --- Django Manager ---
    objects = APIKeyManager()

    class Meta:
        """Model metadata options."""

        db_table = "api_keys"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["key_prefix"]),
            models.Index(fields=["key_hash"]),  # For reverse lookup / key verification.
            models.Index(fields=["expires_at"]),
            models.Index(fields=["revoked_at"]),
            models.Index(
                fields=["tenant", "revoked_at"]
            ),  # Optimize active key queries for a tenant.
            models.Index(fields=["tenant", "project"]),  # Optimize keys per project.
        ]

    def __str__(self) -> str:
        """Returns a string representation of the API key."""
        return f"{self.name} ({self.key_prefix}...)"

    @classmethod
    def generate_key(cls) -> tuple[str, str, str]:
        """
        Generates a new, cryptographically strong API key, its prefix, and its hash.

        The generated key is a 64-character hexadecimal string prefixed with "avb_".
        The full key is only exposed at this point and should be securely presented
        to the user, as it is not stored directly in the database.

        Returns:
            A tuple containing:
            - `full_key` (str): The complete, plaintext API key.
            - `prefix` (str): The first 12 characters of the full key (e.g., "avb_xxxxxxxx").
            - `key_hash` (str): The SHA-256 hash of the full key.
        """
        random_bytes = secrets.token_bytes(32)  # 32 bytes = 256 bits of randomness.
        full_key = f"avb_{random_bytes.hex()}"  # Format: avb_{64_hex_chars}
        prefix = full_key[:12]  # "avb_" + 8 hex chars.
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()  # Hash for storage.
        return full_key, prefix, key_hash

    @classmethod
    def hash_key(cls, key: str) -> str:
        """
        Computes the SHA-256 hash of a given plaintext API key.

        This method is used to verify a provided API key against its stored hash
        without needing to store the plaintext key.

        Args:
            key: The plaintext API key string.

        Returns:
            The SHA-256 hexadecimal hash of the key.
        """
        return hashlib.sha256(key.encode()).hexdigest()

    @property
    def is_active(self) -> bool:
        """
        Checks if the API key is currently active (not revoked and not expired).
        """
        if self.revoked_at:
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    @property
    def is_expired(self) -> bool:
        """
        Checks if the API key has passed its expiration date.
        Returns False if `expires_at` is not set.
        """
        if not self.expires_at:
            return False
        return self.expires_at < timezone.now()

    @property
    def is_revoked(self) -> bool:
        """
        Checks if the API key has been explicitly revoked.
        """
        return self.revoked_at is not None

    def revoke(self, user: Optional["User"] = None, reason: str = "") -> None:
        """
        Revokes the API key, making it inactive immediately.

        Records the time of revocation, the user who initiated it, and an optional reason.

        Args:
            user: (Optional) The User instance who revoked the key.
            reason: (Optional) A text description for the reason of revocation.
        """
        self.revoked_at = timezone.now()
        self.revoked_by = user
        self.revocation_reason = reason
        self.save(
            update_fields=[
                "revoked_at",
                "revoked_by",
                "revocation_reason",
                "updated_at",
            ]
        )

    def record_usage(self, ip_address: Optional[str] = None) -> None:
        """
        Records a single usage event for the API key.

        Updates the `last_used_at` timestamp, `last_used_ip` (if provided),
        and increments the `usage_count`.

        Args:
            ip_address: (Optional) The IP address from which the API call originated.
        """
        self.last_used_at = timezone.now()
        if ip_address:
            self.last_used_ip = ip_address
        self.usage_count += 1
        self.save(
            update_fields=[
                "last_used_at",
                "last_used_ip",
                "usage_count",
                "updated_at",
            ]
        )

    def has_scope(self, scope: str) -> bool:
        """
        Checks if the API key has a specific scope.

        Args:
            scope: The scope string to check against (e.g., 'realtime').

        Returns:
            True if the key has the specified scope, False otherwise.
        """
        return scope in self.scopes

    def get_rate_limit(self) -> int:
        """
        Determines the maximum number of requests per minute allowed for this API key.

        The limit is based on the `rate_limit_tier` setting. A return value of 0
        indicates no rate limit.

        Returns:
            An integer representing the rate limit in requests per minute.
        """
        limits = {
            self.RateLimitTier.STANDARD: 60,
            self.RateLimitTier.ELEVATED: 120,
            self.RateLimitTier.UNLIMITED: 0,
        }
        return limits.get(self.rate_limit_tier, 60)
