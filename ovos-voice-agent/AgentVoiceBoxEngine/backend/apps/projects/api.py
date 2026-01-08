"""
Project Management API Endpoints
================================

This module provides the tenant-scoped API endpoints for managing projects.
It allows users to create, list, update, and delete projects within their
tenant, subject to their role-based permissions.
"""

from typing import Optional
from uuid import UUID

from ninja import Query, Router

from apps.core.exceptions import PermissionDeniedError
from apps.core.middleware.tenant import get_current_tenant

from .schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
    ProjectVoiceConfigResponse,
    VoiceConfig,
)
from .services import ProjectService

# Router for project management endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Projects"])


@router.get("", response=ProjectListResponse, summary="List Projects in Tenant")
def list_projects(
    request,
    is_active: Optional[bool] = Query(
        None, description="Filter projects by active status."
    ),
    search: Optional[str] = Query(
        None, description="Search term for project name or slug."
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Lists all projects within the current user's tenant.

    This endpoint supports pagination and filtering by active status or a search term.

    **Permissions:** Available to any authenticated user in the tenant (implicit viewer role).
    """
    tenant = get_current_tenant(request)
    projects, total = ProjectService.list_projects(
        tenant=tenant,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    pages = (total + page_size - 1) // page_size if total > 0 else 1

    return ProjectListResponse(
        items=[ProjectResponse.from_orm(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{project_id}", response=ProjectResponse, summary="Get a Project by ID")
def get_project(request, project_id: UUID):
    """
    Retrieves a specific project by its ID.

    The project must belong to the current user's tenant.

    **Permissions:** Available to any authenticated user in the tenant.
    """
    tenant = get_current_tenant(request)
    project = ProjectService.get_by_id(project_id)

    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant.")

    return ProjectResponse.from_orm(project)


@router.get(
    "/{project_id}/voice-config",
    response=ProjectVoiceConfigResponse,
    summary="Get Project Voice Configuration",
)
def get_project_voice_config(request, project_id: UUID):
    """
    Retrieves the structured voice configuration for a specific project.

    The project must belong to the current user's tenant.

    **Permissions:** Available to any authenticated user in the tenant.
    """
    tenant = get_current_tenant(request)
    project = ProjectService.get_by_id(project_id)

    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant.")

    return ProjectVoiceConfigResponse.from_project(project)


@router.post("", response=ProjectResponse, summary="Create a New Project")
def create_project(request, payload: ProjectCreate):
    """
    Creates a new project within the current user's tenant.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to create projects.")

    project = ProjectService.create_project(
        tenant=tenant,
        created_by=user,
        **payload.dict(),
    )
    return ProjectResponse.from_orm(project)


@router.patch("/{project_id}", response=ProjectResponse, summary="Update a Project")
def update_project(request, project_id: UUID, payload: ProjectUpdate):
    """
    Updates a project's details with partial data.

    The project must belong to the current user's tenant.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to update projects.")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant.")

    updated_project = ProjectService.update_project(
        project_id=project_id, **payload.dict(exclude_unset=True)
    )
    return ProjectResponse.from_orm(updated_project)


@router.patch(
    "/{project_id}/voice-config",
    response=ProjectVoiceConfigResponse,
    summary="Update Project Voice Configuration",
)
def update_project_voice_config(request, project_id: UUID, payload: VoiceConfig):
    """
    Updates a project's voice configuration from a structured dictionary.

    The project must belong to the current user's tenant.

    **Permissions:** Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to update voice config.")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant.")

    config = payload.dict(exclude_unset=True)
    updated_project = ProjectService.update_voice_config(project_id, config)
    return ProjectVoiceConfigResponse.from_project(updated_project)


@router.post(
    "/{project_id}/deactivate", response=ProjectResponse, summary="Deactivate a Project"
)
def deactivate_project(request, project_id: UUID):
    """
    Deactivates a project, disabling its API keys.

    The project must belong to the current user's tenant.

    **Permissions:** Requires ADMIN role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_admin:
        raise PermissionDeniedError("Admin role required to deactivate projects.")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant.")

    updated_project = ProjectService.deactivate_project(project_id)
    return ProjectResponse.from_orm(updated_project)


@router.post(
    "/{project_id}/activate", response=ProjectResponse, summary="Activate a Project"
)
def activate_project(request, project_id: UUID):
    """
    Activates an inactive project.

    The project must belong to the current user's tenant.

    **Permissions:** Requires ADMIN role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_admin:
        raise PermissionDeniedError("Admin role required to activate projects.")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant.")

    updated_project = ProjectService.activate_project(project_id)
    return ProjectResponse.from_orm(updated_project)


@router.delete("/{project_id}", response={204: None}, summary="Delete a Project")
def delete_project(request, project_id: UUID):
    """
    Permanently deletes a project and all its associated resources.

    The project must belong to the current user's tenant.

    **Permissions:** Requires ADMIN role or higher.
    """
    tenant = get_current_tenant(request)
    user = request.user

    if not user.is_admin:
        raise PermissionDeniedError("Admin role required to delete projects.")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant.")

    ProjectService.delete_project(project_id)
    return 204, None
