"""
User models for authentication and authorization.

Custom user model extending Django's AbstractBaseUser with Keycloak integration.
"""
import uuid
from typing import Optional

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

from apps.tenants.models import Tenant


class UserManager(BaseUserManager):
    """Custom user manager for User model."""

    def create_user(
        self,
        email: str,
        tenant: Tenant,
        password: Optional[str] = None,
        **extra_fields,
    ):
        """
        Create and save a regular user.

        Args:
            email: User email address
            tenant: Tenant the user belongs to
            password: Optional password (not used with Keycloak)
            **extra_fields: Additional fields

        Returns:
            Created user instance
        """
        if not email:
            raise ValueError("Email is required")
        if not tenant:
            raise ValueError("Tenant is required")

        email = self.normalize_email(email)
        user = self.model(email=email, tenant=tenant, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(
        self,
        email: str,
        password: Optional[str] = None,
        **extra_fields,
    ):
        """
        Create and save a superuser.

        Note: Superusers are system-level and not tenant-scoped.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        email = self.normalize_email(email)
        user = self.model(email=email, tenant=None, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def get_by_keycloak_id(self, keycloak_id: str) -> Optional["User"]:
        """Get user by Keycloak ID."""
        try:
            return self.get(keycloak_id=keycloak_id)
        except User.DoesNotExist:
            return None

    def get_by_email_and_tenant(self, email: str, tenant: Tenant) -> Optional["User"]:
        """Get user by email within a tenant."""
        try:
            return self.get(email=email, tenant=tenant)
        except User.DoesNotExist:
            return None

    def active(self):
        """Return only active users."""
        return self.filter(is_active=True)

    def for_tenant(self, tenant: Tenant):
        """Return users for a specific tenant."""
        return self.filter(tenant=tenant)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model with Keycloak integration.

    Users are scoped to tenants and authenticated via Keycloak.
    Local password authentication is disabled by default.
    """

    class Role(models.TextChoices):
        """User roles within a tenant."""
        SYSADMIN = "sysadmin", "System Administrator"
        ADMIN = "admin", "Administrator"
        DEVELOPER = "developer", "Developer"
        OPERATOR = "operator", "Operator"
        VIEWER = "viewer", "Viewer"
        BILLING = "billing", "Billing"

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Keycloak integration
    keycloak_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Keycloak user ID (sub claim)",
    )

    # Basic info
    email = models.EmailField(
        max_length=255,
        unique=True,
        help_text="User email address",
    )
    first_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="First name",
    )
    last_name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Last name",
    )
    avatar_url = models.URLField(
        blank=True,
        help_text="User avatar URL",
    )

    # Tenant association (nullable for superusers)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
        help_text="Tenant the user belongs to",
    )

    # Role within tenant
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.VIEWER,
        help_text="User role within the tenant",
    )

    # Status flags
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the user account is active",
    )
    is_staff = models.BooleanField(
        default=False,
        help_text="Whether the user can access Django admin",
    )

    # User preferences (JSON)
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences and settings",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    email_verified_at = models.DateTimeField(null=True, blank=True)

    # Manager
    objects = UserManager()

    # Auth configuration
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["keycloak_id"]),
            models.Index(fields=["email"]),
            models.Index(fields=["tenant", "is_active"]),
            models.Index(fields=["role"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.tenant.slug if self.tenant else 'system'})"

    @property
    def full_name(self) -> str:
        """Return user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email

    @property
    def is_sysadmin(self) -> bool:
        """Check if user is a system administrator."""
        return self.role == self.Role.SYSADMIN or self.is_superuser

    @property
    def is_admin(self) -> bool:
        """Check if user is an administrator (tenant or system)."""
        return self.role in [self.Role.SYSADMIN, self.Role.ADMIN] or self.is_superuser

    @property
    def is_developer(self) -> bool:
        """Check if user has developer role or higher."""
        return self.role in [
            self.Role.SYSADMIN,
            self.Role.ADMIN,
            self.Role.DEVELOPER,
        ] or self.is_superuser

    @property
    def is_operator(self) -> bool:
        """Check if user has operator role or higher."""
        return self.role in [
            self.Role.SYSADMIN,
            self.Role.ADMIN,
            self.Role.DEVELOPER,
            self.Role.OPERATOR,
        ] or self.is_superuser

    @property
    def is_billing_user(self) -> bool:
        """Check if user has billing access."""
        return self.role in [
            self.Role.SYSADMIN,
            self.Role.ADMIN,
            self.Role.BILLING,
        ] or self.is_superuser

    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = timezone.now()
        self.save(update_fields=["last_login_at", "updated_at"])

    def deactivate(self) -> None:
        """Deactivate user account."""
        self.is_active = False
        self.save(update_fields=["is_active", "updated_at"])

    def activate(self) -> None:
        """Activate user account."""
        self.is_active = True
        self.save(update_fields=["is_active", "updated_at"])

    def change_role(self, new_role: str) -> None:
        """Change user role."""
        if new_role not in self.Role.values:
            raise ValueError(f"Invalid role: {new_role}")
        self.role = new_role
        self.save(update_fields=["role", "updated_at"])

    def update_preferences(self, preferences: dict) -> None:
        """Update user preferences."""
        self.preferences.update(preferences)
        self.save(update_fields=["preferences", "updated_at"])
