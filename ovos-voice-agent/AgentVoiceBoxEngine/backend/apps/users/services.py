"""
User service layer.

Contains all business logic for user operations.
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
    TenantLimitExceededError,
    ValidationError,
)
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService

from .models import User


class UserService:
    """Service class for user operations."""

    @staticmethod
    def get_by_id(user_id: UUID) -> User:
        """
        Get user by ID.

        Raises:
            NotFoundError: If user not found
        """
        try:
            return User.objects.select_related("tenant").get(id=user_id)
        except User.DoesNotExist:
            raise NotFoundError(f"User {user_id} not found")

    @staticmethod
    def get_by_keycloak_id(keycloak_id: str) -> Optional[User]:
        """
        Get user by Keycloak ID.

        Returns:
            User or None if not found
        """
        return User.objects.get_by_keycloak_id(keycloak_id)

    @staticmethod
    def get_by_email_and_tenant(email: str, tenant: Tenant) -> Optional[User]:
        """
        Get user by email within a tenant.

        Returns:
            User or None if not found
        """
        return User.objects.get_by_email_and_tenant(email, tenant)

    @staticmethod
    def list_users(
        tenant: Tenant,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[QuerySet, int]:
        """
        List users for a tenant with filtering and pagination.

        Returns:
            Tuple of (queryset, total_count)
        """
        qs = User.objects.filter(tenant=tenant).select_related("tenant")

        # Apply filters
        if role:
            qs = qs.filter(role=role)
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(
                Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
            )

        # Get total count before pagination
        total = qs.count()

        # Apply pagination
        offset = (page - 1) * page_size
        qs = qs[offset : offset + page_size]

        return qs, total

    @staticmethod
    @transaction.atomic
    def create_user(
        tenant: Tenant,
        email: str,
        role: str = "viewer",
        first_name: str = "",
        last_name: str = "",
        keycloak_id: Optional[str] = None,
    ) -> User:
        """
        Create a new user within a tenant.

        Raises:
            ConflictError: If email already exists in tenant
            TenantLimitExceededError: If tenant user limit reached
            ValidationError: If role is invalid
        """
        # Validate role
        if role not in User.Role.values:
            raise ValidationError(f"Invalid role: {role}")

        # Check tenant user limit
        current_count = User.objects.filter(tenant=tenant, is_active=True).count()
        TenantService.enforce_limit(tenant, "users", current_count)

        # Check for duplicate email in tenant
        if User.objects.filter(email=email, tenant=tenant).exists():
            raise ConflictError(f"User with email '{email}' already exists in this tenant")

        # Create user
        user = User.objects.create_user(
            email=email,
            tenant=tenant,
            role=role,
            first_name=first_name,
            last_name=last_name,
            keycloak_id=keycloak_id,
        )

        return user

    @staticmethod
    @transaction.atomic
    def create_or_update_from_keycloak(
        keycloak_id: str,
        email: str,
        tenant: Tenant,
        first_name: str = "",
        last_name: str = "",
        role: Optional[str] = None,
    ) -> Tuple[User, bool]:
        """
        Create or update user from Keycloak authentication.

        Returns:
            Tuple of (user, created)
        """
        user = User.objects.get_by_keycloak_id(keycloak_id)

        if user:
            # Update existing user
            user.email = email
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            if role and role in User.Role.values:
                user.role = role
            user.save()
            return user, False

        # Create new user
        user = UserService.create_user(
            tenant=tenant,
            email=email,
            role=role or "viewer",
            first_name=first_name,
            last_name=last_name,
            keycloak_id=keycloak_id,
        )
        return user, True

    @staticmethod
    @transaction.atomic
    def update_user(
        user_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> User:
        """
        Update user details.

        Raises:
            NotFoundError: If user not found
            ValidationError: If role is invalid
        """
        user = UserService.get_by_id(user_id)

        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if role is not None:
            if role not in User.Role.values:
                raise ValidationError(f"Invalid role: {role}")
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        if preferences is not None:
            user.preferences.update(preferences)

        user.save()
        return user

    @staticmethod
    @transaction.atomic
    def change_role(user_id: UUID, new_role: str) -> User:
        """
        Change user role.

        Raises:
            NotFoundError: If user not found
            ValidationError: If role is invalid
        """
        if new_role not in User.Role.values:
            raise ValidationError(f"Invalid role: {new_role}")

        user = UserService.get_by_id(user_id)
        user.change_role(new_role)
        return user

    @staticmethod
    @transaction.atomic
    def deactivate_user(user_id: UUID) -> User:
        """
        Deactivate a user.

        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_by_id(user_id)
        user.deactivate()
        return user

    @staticmethod
    @transaction.atomic
    def activate_user(user_id: UUID) -> User:
        """
        Activate a user.

        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_by_id(user_id)
        user.activate()
        return user

    @staticmethod
    @transaction.atomic
    def delete_user(user_id: UUID) -> None:
        """
        Delete a user permanently.

        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_by_id(user_id)
        user.delete()

    @staticmethod
    def update_last_login(user_id: UUID) -> User:
        """
        Update user's last login timestamp.

        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_by_id(user_id)
        user.update_last_login()
        return user

    @staticmethod
    def update_preferences(user_id: UUID, preferences: Dict[str, Any]) -> User:
        """
        Update user preferences.

        Raises:
            NotFoundError: If user not found
        """
        user = UserService.get_by_id(user_id)
        user.update_preferences(preferences)
        return user

    @staticmethod
    def get_users_by_role(tenant: Tenant, role: str) -> QuerySet:
        """
        Get all users with a specific role in a tenant.
        """
        return User.objects.filter(tenant=tenant, role=role, is_active=True)

    @staticmethod
    def get_admins(tenant: Tenant) -> QuerySet:
        """
        Get all admin users in a tenant.
        """
        return User.objects.filter(
            tenant=tenant,
            role__in=[User.Role.SYSADMIN, User.Role.ADMIN],
            is_active=True,
        )

    @staticmethod
    def count_active_users(tenant: Tenant) -> int:
        """
        Count active users in a tenant.
        """
        return User.objects.filter(tenant=tenant, is_active=True).count()

    @staticmethod
    @transaction.atomic
    def sync_from_jwt(jwt_data: Dict[str, Any]) -> Optional[User]:
        """
        Sync user from JWT claims.

        Creates or updates user based on Keycloak JWT data.

        Args:
            jwt_data: Dictionary with user_id, tenant_id, email, first_name, last_name, roles

        Returns:
            User instance or None if tenant not found
        """
        keycloak_id = jwt_data.get("user_id")
        tenant_id = jwt_data.get("tenant_id")
        email = jwt_data.get("email")

        if not keycloak_id or not email:
            return None

        # Get tenant
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
            except Tenant.DoesNotExist:
                return None
        else:
            return None

        # Determine role from JWT roles
        jwt_roles = jwt_data.get("roles", [])
        role = "viewer"  # Default role
        if "sysadmin" in jwt_roles:
            role = "sysadmin"
        elif "admin" in jwt_roles:
            role = "admin"
        elif "developer" in jwt_roles:
            role = "developer"
        elif "operator" in jwt_roles:
            role = "operator"
        elif "billing" in jwt_roles:
            role = "billing"

        user, created = UserService.create_or_update_from_keycloak(
            keycloak_id=keycloak_id,
            email=email,
            tenant=tenant,
            first_name=jwt_data.get("first_name", ""),
            last_name=jwt_data.get("last_name", ""),
            role=role,
        )

        # Update last login
        if not created:
            user.update_last_login()

        return user
