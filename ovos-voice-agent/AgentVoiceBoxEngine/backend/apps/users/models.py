"""
User and Authentication Models
==============================

This module defines the custom user model for the application, which integrates
with Keycloak for identity management and is designed to support the multi-tenant
architecture. It replaces Django's default `User` model.
"""

import uuid
from typing import Optional

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone

from apps.tenants.models import Tenant


class UserManager(BaseUserManager):
    """
    A custom manager for the User model.

    It provides methods for creating standard users (which must be associated
    with a tenant) and superusers (which are system-level and have no tenant).
    """

    def create_user(
        self,
        email: str,
        tenant: Tenant,
        password: Optional[str] = None,
        **extra_fields,
    ) -> "User":
        """
        Creates and saves a regular user associated with a specific tenant.

        Since authentication is primarily handled by Keycloak, the password is
        not expected to be used for local authentication and is set to an
        unusable state if not provided.

        Args:
            email: The user's email address (will be normalized).
            tenant: The Tenant instance the user belongs to.
            password: (Optional) The user's password.
            **extra_fields: Additional fields for the User model.

        Returns:
            The newly created User instance.
        """
        if not email:
            raise ValueError("The Email field is required")
        if not tenant:
            raise ValueError("A Tenant is required for a regular user")

        email = self.normalize_email(email)
        user = self.model(email=email, tenant=tenant, **extra_fields)
        if password:
            user.set_password(password)
        else:
            # For SSO-based users, a usable local password is not necessary.
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields,
    ) -> "User":
        """
        Creates and saves a superuser.

        Superusers are system-level administrators and are not associated with
        any tenant (`tenant` is None).

        Args:
            email: The superuser's email address.
            password: The superuser's password.
            **extra_fields: Additional fields for the User model.

        Returns:
            The newly created superuser instance.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        email = self.normalize_email(email)
        # Superusers are not tied to a specific tenant.
        user = self.model(email=email, tenant=None, **extra_fields)
        if password:
            user.set_password(password)
        else:
            raise ValueError("Superuser must have a password.")
        user.save(using=self._db)
        return user

    def get_by_keycloak_id(self, keycloak_id: str) -> Optional["User"]:
        """Retrieves a user by their unique Keycloak ID."""
        try:
            return self.get(keycloak_id=keycloak_id)
        except User.DoesNotExist:
            return None

    def get_by_email_and_tenant(self, email: str, tenant: Tenant) -> Optional["User"]:
        """Retrieves a user by their email within a specific tenant."""
        try:
            return self.get(email=email, tenant=tenant)
        except User.DoesNotExist:
            return None

    def active(self):
        """Returns a queryset of all active users."""
        return self.filter(is_active=True)

    def for_tenant(self, tenant: Tenant):
        """Returns a queryset of users for a specific tenant."""
        return self.filter(tenant=tenant)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model for the application.

    This model represents a user account, which is typically linked to a `Tenant`
    and a corresponding user in an external identity provider (Keycloak).
    Authentication is handled by the external provider, while this model stores
    application-specific user details, roles, and preferences.
    """

    class Role(models.TextChoices):
        """
        Enumeration for user roles within a tenant, defining their permissions.
        The roles are hierarchical.
        """

        SYSADMIN = (
            "sysadmin",
            "System Administrator",
        )  # Highest level, system-wide access
        ADMIN = "admin", "Administrator"  # Full access within a tenant
        DEVELOPER = "developer", "Developer"  # Can manage projects and API keys
        OPERATOR = "operator", "Operator"  # Can manage sessions and view data
        VIEWER = "viewer", "Viewer"  # Read-only access within a tenant
        BILLING = "billing", "Billing"  # Access to billing and subscription info

    # --- Core Identification & External Integration ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keycloak_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text="The unique identifier (sub claim) from the Keycloak JWT.",
    )

    # --- Personal Information ---
    email = models.EmailField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="The user's unique email address.",
    )
    first_name = models.CharField(
        max_length=150, blank=True, help_text="User's first name."
    )
    last_name = models.CharField(
        max_length=150, blank=True, help_text="User's last name."
    )
    avatar_url = models.URLField(
        blank=True, help_text="URL for the user's profile picture."
    )

    # --- Tenancy and Authorization ---
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,  # Null for system-level users like superusers
        blank=True,
        help_text="The tenant this user belongs to.",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text="The user's role, which determines their permissions within the tenant.",
    )

    # --- Django-specific Status Flags ---
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into the Django admin site.",
    )

    # --- User-specific Settings ---
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="A JSON field for storing user-specific UI preferences and settings.",
    )

    # --- Timestamps ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp of the user's last login."
    )
    email_verified_at = models.DateTimeField(
        null=True, blank=True, help_text="Timestamp when the user's email was verified."
    )

    # --- Model Configuration ---
    objects = UserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        """Model metadata options."""

        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        """Returns a string representation of the user."""
        return f"{self.email} ({self.tenant.slug if self.tenant else 'System'})"

    @property
    def full_name(self) -> str:
        """Returns the user's full name, or their email as a fallback."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email

    # --- Hierarchical Role-based Permission Properties ---

    @property
    def is_sysadmin(self) -> bool:
        """Checks if the user has system-level admin privileges."""
        return self.role == self.Role.SYSADMIN or self.is_superuser

    @property
    def is_admin(self) -> bool:
        """Checks if the user is an admin. Includes tenant and system admins."""
        return self.role in [self.Role.SYSADMIN, self.Role.ADMIN] or self.is_superuser

    @property
    def is_developer(self) -> bool:
        """Checks if the user has Developer permissions or higher."""
        return (
            self.role in [self.Role.SYSADMIN, self.Role.ADMIN, self.Role.DEVELOPER]
            or self.is_superuser
        )

    @property
    def is_operator(self) -> bool:
        """Checks if the user has Operator permissions or higher."""
        return (
            self.role
            in [
                self.Role.SYSADMIN,
                self.Role.ADMIN,
                self.Role.DEVELOPER,
                self.Role.OPERATOR,
            ]
            or self.is_superuser
        )

    @property
    def is_billing_user(self) -> bool:
        """Checks if the user has permissions to view billing information."""
        return (
            self.role in [self.Role.SYSADMIN, self.Role.ADMIN, self.Role.BILLING]
            or self.is_superuser
        )

    # --- Instance Methods for Lifecycle Management ---

    def update_last_login(self) -> None:
        """Updates the `last_login_at` timestamp to the current time."""
        self.last_login_at = timezone.now()
        self.save(update_fields=["last_login_at", "updated_at"])

    def deactivate(self) -> None:
        """Deactivates the user's account by setting `is_active` to False."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def activate(self) -> None:
        """Activates the user's account by setting `is_active` to True."""
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])

    def change_role(self, new_role: str) -> None:
        """
        Changes the user's role within the tenant.

        Args:
            new_role: The new role, which must be a valid choice from `User.Role`.

        Raises:
            ValueError: If `new_role` is not a valid role.
        """
        if new_role not in self.Role.values:
            raise ValueError(f"Invalid role: {new_role}")
        self.role = new_role
        self.save(update_fields=["role", "updated_at"])

    def update_preferences(self, preferences: dict) -> None:
        """
        Updates the user's preferences JSON field.

        Args:
            preferences: A dictionary of preferences to merge into the existing ones.
        """
        self.preferences.update(preferences)
        self.save(update_fields=["preferences", "updated_at"])
