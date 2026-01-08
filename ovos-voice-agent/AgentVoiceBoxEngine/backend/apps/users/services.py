"""
User Service Layer
==================

This module contains all the business logic for user-related operations. It
provides a clear separation between the API endpoints and the data models,
handling user creation, updates, role changes, and synchronization with the
external identity provider (Keycloak).
"""

from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet

from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService

from .models import User


class UserService:
    """A service class encapsulating all business logic for User operations."""

    @staticmethod
    def get_by_id(user_id: UUID) -> User:
        """
        Retrieves a single user by their primary key (ID).

        Args:
            user_id: The UUID of the user to retrieve.

        Returns:
            The User instance.

        Raises:
            NotFoundError: If a user with the specified ID does not exist.
        """
        try:
            return User.objects.select_related("tenant").get(id=user_id)
        except User.DoesNotExist:
            raise NotFoundError(f"User {user_id} not found")

    @staticmethod
    def get_by_keycloak_id(keycloak_id: str) -> Optional[User]:
        """
        Retrieves a user by their unique Keycloak ID.

        Args:
            keycloak_id: The Keycloak 'sub' claim for the user.

        Returns:
            The User instance if found, otherwise None.
        """
        return User.objects.get_by_keycloak_id(keycloak_id)

    @staticmethod
    def get_by_email_and_tenant(email: str, tenant: Tenant) -> Optional[User]:
        """
        Retrieves a user by their email address within a specific tenant.

        Args:
            email: The user's email address.
            tenant: The tenant to scope the search to.

        Returns:
            The User instance if found, otherwise None.
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
    ) -> tuple[QuerySet, int]:
        """
        Provides a paginated and filterable list of users for a specific tenant.

        Args:
            tenant: The tenant whose users are to be listed.
            role: (Optional) Filter users by their role.
            is_active: (Optional) Filter users by their active status.
            search: (Optional) A search term to filter users by email, first name, or last name.
            page: The page number for pagination.
            page_size: The number of items per page.

        Returns:
            A tuple containing:
            - A queryset of User instances for the requested page.
            - An integer representing the total count of users matching the filters.
        """
        qs = User.objects.filter(tenant=tenant).select_related("tenant")

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

        total = qs.count()
        offset = (page - 1) * page_size
        paginated_qs = qs[offset : offset + page_size]

        return paginated_qs, total

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
        Creates a new user within a tenant, enforcing tenant-level limits.

        This method is transactional and ensures that a user is not created if
        it would exceed the tenant's user limit.

        Args:
            tenant: The tenant the user will belong to.
            email: The new user's email address.
            role: The user's role within the tenant (e.g., 'admin', 'viewer').
            first_name: (Optional) The user's first name.
            last_name: (Optional) The user's last name.
            keycloak_id: (Optional) The user's Keycloak ID.

        Returns:
            The newly created User instance.

        Raises:
            ConflictError: If a user with the same email already exists in the tenant.
            TenantLimitExceededError: If adding this user would exceed the tenant's user limit.
            ValidationError: If the provided role is invalid.
        """
        if role not in User.Role.values:
            raise ValidationError(f"Invalid role: {role}")

        # Enforce tenant user limit before creating the new user.
        TenantService.enforce_limit(tenant, "users")

        if User.objects.filter(email=email, tenant=tenant).exists():
            raise ConflictError(
                f"User with email '{email}' already exists in this tenant"
            )

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
    ) -> tuple[User, bool]:
        """
        Creates a new user or updates an existing one based on Keycloak data.

        This implements a Just-In-Time (JIT) provisioning strategy. When a user
        logs in via SSO, this service is called to ensure a corresponding local
        user record exists and is up-to-date.

        Args:
            keycloak_id: The user's unique ID from Keycloak.
            email: The user's email from Keycloak.
            tenant: The tenant the user belongs to.
            first_name: The user's first name from Keycloak.
            last_name: The user's last name from Keycloak.
            role: (Optional) The user's role, determined from JWT claims.

        Returns:
            A tuple containing:
            - The User instance (either newly created or updated).
            - A boolean indicating if the user was created (`True`) or updated (`False`).
        """
        user = User.objects.get_by_keycloak_id(keycloak_id)
        created = False

        if user:
            # Update fields for the existing user if they have changed.
            user.email = email
            user.first_name = first_name or user.first_name
            user.last_name = last_name or user.last_name
            if role and role in User.Role.values:
                user.role = role
            user.save()
        else:
            # If the user does not exist, create them.
            user = UserService.create_user(
                tenant=tenant,
                email=email,
                role=role or "viewer",
                first_name=first_name,
                last_name=last_name,
                keycloak_id=keycloak_id,
            )
            created = True

        return user, created

    @staticmethod
    @transaction.atomic
    def update_user(user_id: UUID, **kwargs: Any) -> User:
        """
        Updates an existing user's details.

        This method performs a partial update based on the provided keyword arguments.

        Args:
            user_id: The ID of the user to update.
            **kwargs: Keyword arguments corresponding to User model fields
                      (e.g., `first_name`, `last_name`, `role`, `is_active`).

        Returns:
            The updated User instance.

        Raises:
            NotFoundError: If the user is not found.
            ValidationError: If an invalid role is provided.
        """
        user = UserService.get_by_id(user_id)
        update_fields = ["updated_at"]

        for key, value in kwargs.items():
            if value is not None:
                # Special validation for the role field.
                if key == "role" and value not in User.Role.values:
                    raise ValidationError(f"Invalid role: {value}")
                setattr(user, key, value)
                update_fields.append(key)

        user.save(update_fields=update_fields)
        return user

    @staticmethod
    @transaction.atomic
    def delete_user(user_id: UUID) -> None:
        """
        Permanently deletes a user from the database.

        Args:
            user_id: The ID of the user to delete.

        Raises:
            NotFoundError: If the user is not found.
        """
        user = UserService.get_by_id(user_id)
        # In a real-world scenario, this might also trigger a call to delete
        # the user from the external identity provider (Keycloak).
        user.delete()

    @staticmethod
    @transaction.atomic
    def sync_from_jwt(jwt_data: dict[str, Any]) -> Optional[User]:
        """
        Synchronizes a user's data from a Keycloak JWT upon login.

        This is the primary entry point for JIT provisioning. It extracts user
        and tenant information from the JWT, determines the user's role, and then
        calls `create_or_update_from_keycloak` to sync the local database.

        Args:
            jwt_data: A dictionary of claims from the decoded JWT.

        Returns:
            The synchronized User instance, or None if essential data is missing
            from the JWT or the tenant does not exist.
        """
        keycloak_id = jwt_data.get("sub")  # 'sub' is the standard claim for user ID
        tenant_id = jwt_data.get("tenant_id")
        email = jwt_data.get("email")

        if not keycloak_id or not email or not tenant_id:
            return None

        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return None

        # Map roles from the JWT to the internal Role enumeration.
        # This assumes the JWT contains a 'roles' claim, which is a list of strings.
        jwt_roles = jwt_data.get("roles", [])
        role = "viewer"  # Assign 'viewer' as the default, least-privileged role.
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
            first_name=jwt_data.get("given_name", ""),
            last_name=jwt_data.get("family_name", ""),
            role=role,
        )

        user.update_last_login()
        return user

    # The following methods are thin wrappers around model methods or simple queries.
    # They are included to provide a consistent service-layer interface.

    @staticmethod
    def change_role(user_id: UUID, new_role: str) -> User:
        """Changes a user's role. Delegates to the model method."""
        user = UserService.get_by_id(user_id)
        user.change_role(new_role)
        return user

    @staticmethod
    def deactivate_user(user_id: UUID) -> User:
        """Deactivates a user. Delegates to the model method."""
        user = UserService.get_by_id(user_id)
        user.deactivate()
        return user

    @staticmethod
    def activate_user(user_id: UUID) -> User:
        """Activates a user. Delegates to the model method."""
        user = UserService.get_by_id(user_id)
        user.activate()
        return user

    @staticmethod
    def update_last_login(user_id: UUID) -> User:
        """Updates a user's last login time. Delegates to the model method."""
        user = UserService.get_by_id(user_id)
        user.update_last_login()
        return user

    @staticmethod
    def update_preferences(user_id: UUID, preferences: dict[str, Any]) -> User:
        """Updates a user's preferences. Delegates to the model method."""
        user = UserService.get_by_id(user_id)
        user.update_preferences(preferences)
        return user

    @staticmethod
    def get_users_by_role(tenant: Tenant, role: str) -> QuerySet:
        """Returns a queryset of all active users with a specific role in a tenant."""
        return User.objects.filter(tenant=tenant, role=role, is_active=True)

    @staticmethod
    def get_admins(tenant: Tenant) -> QuerySet:
        """Returns a queryset of all admin-level users in a tenant."""
        return User.objects.filter(
            tenant=tenant,
            role__in=[User.Role.SYSADMIN, User.Role.ADMIN],
            is_active=True,
        )

    @staticmethod
    def count_active_users(tenant: Tenant) -> int:
        """Counts the number of active users in a tenant."""
        return User.objects.filter(tenant=tenant, is_active=True).count()
