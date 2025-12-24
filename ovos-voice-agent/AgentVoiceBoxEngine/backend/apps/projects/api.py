"""
Project API endpoints.

Public project endpoints for tenant-scoped operations.
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

router = Router()


@router.get("", response=ProjectListResponse)
def list_projects(
    request,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name or slug"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List projects in the current tenant.

    Requires at least VIEWER role.
    """
    tenant = get_current_tenant()

    projects, total = ProjectService.list_projects(
        tenant=tenant,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )

    pages = (total + page_size - 1) // page_size

    return ProjectListResponse(
        items=[ProjectResponse.from_orm(p) for p in projects],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{project_id}", response=ProjectResponse)
def get_project(request, project_id: UUID):
    """
    Get project by ID.

    Requires at least VIEWER role.
    """
    tenant = get_current_tenant()
    project = ProjectService.get_by_id(project_id)

    # Ensure project belongs to current tenant
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant")

    return ProjectResponse.from_orm(project)


@router.get("/{project_id}/voice-config", response=ProjectVoiceConfigResponse)
def get_project_voice_config(request, project_id: UUID):
    """
    Get project voice configuration.

    Requires at least VIEWER role.
    """
    tenant = get_current_tenant()
    project = ProjectService.get_by_id(project_id)

    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant")

    return ProjectVoiceConfigResponse.from_project(project)


@router.post("", response=ProjectResponse)
def create_project(request, payload: ProjectCreate):
    """
    Create a new project.

    Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to create projects")

    project = ProjectService.create_project(
        tenant=tenant,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        created_by=user,
        stt_model=payload.stt_model,
        stt_language=payload.stt_language,
        tts_model=payload.tts_model,
        tts_voice=payload.tts_voice,
        tts_speed=payload.tts_speed,
        llm_provider=payload.llm_provider,
        llm_model=payload.llm_model,
        llm_temperature=payload.llm_temperature,
        llm_max_tokens=payload.llm_max_tokens,
        system_prompt=payload.system_prompt,
        turn_detection_enabled=payload.turn_detection_enabled,
        max_session_duration=payload.max_session_duration,
        max_concurrent_sessions=payload.max_concurrent_sessions,
    )

    return ProjectResponse.from_orm(project)


@router.patch("/{project_id}", response=ProjectResponse)
def update_project(request, project_id: UUID, payload: ProjectUpdate):
    """
    Update a project.

    Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to update projects")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant")

    updated_project = ProjectService.update_project(
        project_id=project_id,
        **payload.dict(exclude_none=True),
    )

    return ProjectResponse.from_orm(updated_project)


@router.patch("/{project_id}/voice-config", response=ProjectVoiceConfigResponse)
def update_project_voice_config(request, project_id: UUID, payload: VoiceConfig):
    """
    Update project voice configuration.

    Requires DEVELOPER role or higher.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_developer:
        raise PermissionDeniedError("Developer role required to update voice config")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant")

    config = payload.dict(exclude_none=True)
    updated_project = ProjectService.update_voice_config(project_id, config)

    return ProjectVoiceConfigResponse.from_project(updated_project)


@router.post("/{project_id}/deactivate", response=ProjectResponse)
def deactivate_project(request, project_id: UUID):
    """
    Deactivate a project.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_admin:
        raise PermissionDeniedError("Admin role required to deactivate projects")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant")

    updated_project = ProjectService.deactivate_project(project_id)
    return ProjectResponse.from_orm(updated_project)


@router.post("/{project_id}/activate", response=ProjectResponse)
def activate_project(request, project_id: UUID):
    """
    Activate a project.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_admin:
        raise PermissionDeniedError("Admin role required to activate projects")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant")

    updated_project = ProjectService.activate_project(project_id)
    return ProjectResponse.from_orm(updated_project)


@router.delete("/{project_id}", response={204: None})
def delete_project(request, project_id: UUID):
    """
    Delete a project permanently.

    Requires ADMIN role.
    """
    tenant = get_current_tenant()
    user = request.user

    if not user.is_admin:
        raise PermissionDeniedError("Admin role required to delete projects")

    project = ProjectService.get_by_id(project_id)
    if project.tenant_id != tenant.id:
        raise PermissionDeniedError("Project not found in this tenant")

    ProjectService.delete_project(project_id)
    return 204, None
