"""
Project service layer.

Contains all business logic for project operations.
"""
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.db import transaction
from django.db.models import Q, QuerySet

from apps.core.exceptions import (
    ConflictError,
    NotFoundError,
    TenantLimitExceededError,
)
from apps.tenants.models import Tenant
from apps.tenants.services import TenantService
from apps.users.models import User

from .models import Project


class ProjectService:
    """Service class for project operations."""

    @staticmethod
    def get_by_id(project_id: UUID) -> Project:
        """
        Get project by ID.

        Raises:
            NotFoundError: If project not found
        """
        try:
            return Project.objects.select_related("tenant", "created_by").get(id=project_id)
        except Project.DoesNotExist:
            raise NotFoundError(f"Project {project_id} not found")

    @staticmethod
    def get_by_slug(slug: str) -> Project:
        """
        Get project by slug within current tenant.

        Raises:
            NotFoundError: If project not found
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
    ) -> Tuple[QuerySet, int]:
        """
        List projects with filtering and pagination.

        Returns:
            Tuple of (queryset, total_count)
        """
        if tenant:
            qs = Project.all_objects.filter(tenant=tenant)
        else:
            qs = Project.objects.all()

        qs = qs.select_related("tenant", "created_by")

        # Apply filters
        if is_active is not None:
            qs = qs.filter(is_active=is_active)
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(slug__icontains=search))

        # Get total count before pagination
        total = qs.count()

        # Apply pagination
        offset = (page - 1) * page_size
        qs = qs[offset : offset + page_size]

        return qs, total

    @staticmethod
    @transaction.atomic
    def create_project(
        tenant: Tenant,
        name: str,
        slug: str,
        created_by: User,
        description: str = "",
        **kwargs,
    ) -> Project:
        """
        Create a new project.

        Raises:
            ConflictError: If slug already exists in tenant
            TenantLimitExceededError: If tenant project limit reached
        """
        # Check tenant project limit
        current_count = Project.all_objects.filter(tenant=tenant).count()
        TenantService.enforce_limit(tenant, "projects", current_count)

        # Check for duplicate slug in tenant
        if Project.all_objects.filter(tenant=tenant, slug=slug).exists():
            raise ConflictError(f"Project with slug '{slug}' already exists")

        # Create project
        project = Project(
            tenant=tenant,
            name=name,
            slug=slug,
            description=description,
            created_by=created_by,
        )

        # Apply optional fields
        for field, value in kwargs.items():
            if hasattr(project, field) and value is not None:
                setattr(project, field, value)

        project.save()
        return project

    @staticmethod
    @transaction.atomic
    def update_project(project_id: UUID, **kwargs) -> Project:
        """
        Update project details.

        Raises:
            NotFoundError: If project not found
        """
        project = ProjectService.get_by_id(project_id)

        for field, value in kwargs.items():
            if hasattr(project, field) and value is not None:
                setattr(project, field, value)

        project.save()
        return project

    @staticmethod
    @transaction.atomic
    def update_voice_config(project_id: UUID, config: Dict[str, Any]) -> Project:
        """
        Update project voice configuration.

        Raises:
            NotFoundError: If project not found
        """
        project = ProjectService.get_by_id(project_id)
        project.update_voice_config(config)
        return project

    @staticmethod
    @transaction.atomic
    def deactivate_project(project_id: UUID) -> Project:
        """
        Deactivate a project.

        Raises:
            NotFoundError: If project not found
        """
        project = ProjectService.get_by_id(project_id)
        project.deactivate()
        return project

    @staticmethod
    @transaction.atomic
    def activate_project(project_id: UUID) -> Project:
        """
        Activate a project.

        Raises:
            NotFoundError: If project not found
        """
        project = ProjectService.get_by_id(project_id)
        project.activate()
        return project

    @staticmethod
    @transaction.atomic
    def delete_project(project_id: UUID) -> None:
        """
        Delete a project permanently.

        Raises:
            NotFoundError: If project not found
        """
        project = ProjectService.get_by_id(project_id)
        project.delete()

    @staticmethod
    def get_project_stats(project_id: UUID) -> Dict[str, Any]:
        """
        Get project statistics.

        Returns:
            Dictionary with project stats
        """
        project = ProjectService.get_by_id(project_id)

        from apps.api_keys.models import APIKey
        from apps.sessions.models import Session

        return {
            "project_id": str(project.id),
            "name": project.name,
            "is_active": project.is_active,
            "api_keys": {
                "total": APIKey.all_objects.filter(
                    tenant=project.tenant,
                    project=project,
                ).count(),
                "active": APIKey.all_objects.filter(
                    tenant=project.tenant,
                    project=project,
                    revoked_at__isnull=True,
                ).count(),
            },
            "sessions": {
                "total": Session.all_objects.filter(project=project).count(),
                "active": Session.all_objects.filter(
                    project=project,
                    status="active",
                ).count(),
            },
        }

    @staticmethod
    def count_active_projects(tenant: Tenant) -> int:
        """
        Count active projects in a tenant.
        """
        return Project.all_objects.filter(tenant=tenant, is_active=True).count()
