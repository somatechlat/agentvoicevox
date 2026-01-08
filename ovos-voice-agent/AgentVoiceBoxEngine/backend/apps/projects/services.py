"""
Project Service Layer
=====================

This module contains all the business logic for project-related operations.
It enforces business rules such as tenant resource limits and ensures that
database operations are performed atomically.
"""

from typing import Any, Optional
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet

from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
)
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService
from apps.users.models import User

from .models import Project


class ProjectService:
    """A service class encapsulating all business logic for Project operations."""

    @staticmethod
    def get_by_id(project_id: UUID) -> Project:
        """
        Retrieves a single project by its primary key (ID).

        Args:
            project_id: The UUID of the project to retrieve.

        Returns:
            The Project instance.

        Raises:
            NotFoundError: If a project with the specified ID does not exist.
        """
        try:
            return Project.objects.select_related("tenant", "created_by").get(
                id=project_id
            )
        except Project.DoesNotExist:
            raise NotFoundError(f"Project {project_id} not found")

    @staticmethod
    def get_by_slug(slug: str) -> Project:
        """
        Retrieves a project by its slug, scoped to the current user's tenant.

        Note: This uses the default tenant-scoped manager.

        Args:
            slug: The URL-friendly slug of the project.

        Returns:
            The Project instance.

        Raises:
            NotFoundError: If a project with the specified slug does not exist in the current tenant.
        """
        try:
            return Project.objects.select_related("tenant", "created_by").get(slug=slug)
        except Project.DoesNotExist:
            raise NotFoundError(f"Project with slug '{slug}' not found")

    @staticmethod
    def list_projects(
        tenant: Optional[Tenant] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[QuerySet, int]:
        """
        Provides a paginated and filterable list of projects.

        If a `tenant` is provided, it lists projects for that specific tenant
        (admin use). If `tenant` is None, it uses the default tenant-scoped
        manager to list projects for the current user's tenant.

        Args:
            tenant: (Optional) The tenant for which to list projects.
            is_active: (Optional) Filter projects by their active status.
            search: (Optional) A search term to filter projects by name or slug.
            page: The page number for pagination.
            page_size: The number of items per page.

        Returns:
            A tuple containing:
            - A queryset of Project instances for the requested page.
            - An integer representing the total count of matching projects.
        """
        if tenant:
            # Use the unscoped manager for explicit tenant filtering (admin action).
            qs = Project.all_objects.filter(tenant=tenant)
        else:
            # Use the default tenant-scoped manager.
            qs = Project.objects.all()

        qs = qs.select_related("tenant", "created_by")

        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))

        total = qs.count()
        offset = (page - 1) * page_size
        paginated_qs = qs[offset : offset + page_size]

        return paginated_qs, total

    @staticmethod
    @transaction.atomic
    def create_project(
        tenant: Tenant,
        name: str,
        slug: str,
        created_by: User,
        description: str = "",
        **kwargs: Any,
    ) -> Project:
        """
        Creates a new project within a tenant, enforcing tenant-level limits.

        This method is transactional and ensures a project is not created if it
        would exceed the tenant's project limit. It also uses `**kwargs` to allow
        setting any additional `Project` model fields during creation.

        Args:
            tenant: The tenant the project will belong to.
            name: The name of the new project.
            slug: The URL-friendly slug for the new project.
            created_by: The user creating the project.
            description: (Optional) A description for the project.
            **kwargs: Additional keyword arguments corresponding to `Project` model fields.

        Returns:
            The newly created Project instance.

        Raises:
            ConflictError: If a project with the same slug already exists in the tenant.
            TenantLimitExceededError: If adding this project would exceed the tenant's project limit.
        """
        TenantService.enforce_limit(tenant, "projects")

        if Project.all_objects.filter(tenant=tenant, slug=slug).exists():
            raise ConflictError(
                f"Project with slug '{slug}' already exists in this tenant."
            )

        project = Project(
            tenant=tenant,
            name=name,
            slug=slug,
            description=description,
            created_by=created_by,
        )

        # Apply any optional fields from kwargs.
        for field, value in kwargs.items():
            if hasattr(project, field) and value is not None:
                setattr(project, field, value)

        project.save()
        return project

    @staticmethod
    @transaction.atomic
    def update_project(project_id: UUID, **kwargs: Any) -> Project:
        """
        Updates an existing project's details.

        This method performs a partial update based on the provided keyword arguments.
        It can update any field on the `Project` model.

        Args:
            project_id: The ID of the project to update.
            **kwargs: Key-value pairs of fields to update.

        Returns:
            The updated Project instance.

        Raises:
            NotFoundError: If the project is not found.
        """
        project = ProjectService.get_by_id(project_id)

        for field, value in kwargs.items():
            # Ensure we don't try to set a protected attribute.
            if hasattr(project, field) and not field.startswith("_"):
                setattr(project, field, value)

        project.save()
        return project

    @staticmethod
    @transaction.atomic
    def update_voice_config(project_id: UUID, config: dict[str, Any]) -> Project:
        """
        Updates a project's voice configuration from a dictionary.

        This is a convenience method that delegates to the `update_voice_config`
        method on the Project model instance.

        Args:
            project_id: The ID of the project to update.
            config: A dictionary containing the new voice configuration values.

        Returns:
            The updated Project instance.
        """
        project = ProjectService.get_by_id(project_id)
        project.update_voice_config(config)
        return project

    @staticmethod
    @transaction.atomic
    def deactivate_project(project_id: UUID) -> Project:
        """Deactivates a project. Delegates to the model method."""
        project = ProjectService.get_by_id(project_id)
        project.deactivate()
        return project

    @staticmethod
    @transaction.atomic
    def activate_project(project_id: UUID) -> Project:
        """Activates a project. Delegates to the model method."""
        project = ProjectService.get_by_id(project_id)
        project.activate()
        return project

    @staticmethod
    @transaction.atomic
    def delete_project(project_id: UUID) -> None:
        """
        Permanently deletes a project from the database.

        Args:
            project_id: The ID of the project to delete.
        """
        project = ProjectService.get_by_id(project_id)
        project.delete()

    @staticmethod
    def get_project_stats(project_id: UUID) -> dict[str, Any]:
        """
        Gathers and returns usage statistics for a given project.

        This is useful for dashboards to show activity related to a project,
        such as API key and session counts.

        Args:
            project_id: The ID of the project for which to gather stats.

        Returns:
            A dictionary containing project usage statistics.
        """
        project = ProjectService.get_by_id(project_id)

        # Import locally to avoid circular dependency issues at the module level.
        from apps.api_keys.models import APIKey
        from apps.sessions.models import Session

        return {
            "project_id": str(project.id),
            "name": project.name,
            "is_active": project.is_active,
            "api_keys": {
                "total": APIKey.all_objects.filter(project=project).count(),
                "active": APIKey.all_objects.filter(
                    project=project, revoked_at__isnull=True
                ).count(),
            },
            "sessions": {
                "total": Session.all_objects.filter(project=project).count(),
                "active": Session.all_objects.filter(
                    project=project, status="active"
                ).count(),
            },
        }

    @staticmethod
    def count_active_projects(tenant: Tenant) -> int:
        """Counts the number of active projects in a tenant."""
        return Project.all_objects.filter(tenant=tenant, is_active=True).count()
