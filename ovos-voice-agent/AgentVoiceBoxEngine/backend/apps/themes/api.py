"""
Theme API endpoints.

Provides REST API for theme management.
"""
from uuid import UUID

from django.http import HttpResponse
from ninja import Query, Router

from apps.core.exceptions import NotFoundError

from .schemas import (
    ThemeCSSOut,
    ThemeCSSVariablesOut,
    ThemeCreate,
    ThemeListOut,
    ThemeOut,
    ThemeUpdate,
)
from .services import ThemeService

router = Router()


def _theme_to_out(t) -> ThemeOut:
    """Convert Theme model to output schema."""
    return ThemeOut(
        id=t.id,
        tenant_id=t.tenant_id,
        name=t.name,
        description=t.description,
        primary_color=t.primary_color,
        secondary_color=t.secondary_color,
        accent_color=t.accent_color,
        background_color=t.background_color,
        surface_color=t.surface_color,
        text_color=t.text_color,
        text_muted_color=t.text_muted_color,
        border_color=t.border_color,
        success_color=t.success_color,
        warning_color=t.warning_color,
        error_color=t.error_color,
        font_family=t.font_family,
        font_size_base=t.font_size_base,
        border_radius=t.border_radius,
        custom_css=t.custom_css,
        is_active=t.is_active,
        is_default=t.is_default,
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


@router.get("", response=ThemeListOut)
def list_themes(
    request,
    active_only: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List themes for current tenant."""
    tenant = request.tenant
    themes, total = ThemeService.list_themes(
        tenant=tenant,
        active_only=active_only,
        page=page,
        page_size=page_size,
    )
    return ThemeListOut(
        items=[_theme_to_out(t) for t in themes],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response={201: ThemeOut})
def create_theme(request, payload: ThemeCreate):
    """Create a new theme."""
    tenant = request.tenant
    theme = ThemeService.create_theme(tenant=tenant, data=payload.dict())
    return 201, _theme_to_out(theme)


@router.get("/default", response=ThemeOut)
def get_default_theme(request):
    """Get the default theme for current tenant."""
    tenant = request.tenant
    theme = ThemeService.get_default_theme(tenant)
    if not theme:
        raise NotFoundError("No default theme configured")
    return _theme_to_out(theme)


@router.get("/default/css")
def get_default_theme_css(request):
    """Get CSS for the default theme (returns text/css)."""
    tenant = request.tenant
    theme = ThemeService.get_default_theme(tenant)
    if not theme:
        return HttpResponse("", content_type="text/css")
    css = ThemeService.get_css(theme)
    return HttpResponse(css, content_type="text/css")


@router.get("/{theme_id}", response=ThemeOut)
def get_theme(request, theme_id: UUID):
    """Get a theme by ID."""
    theme = ThemeService.get_theme(theme_id)
    if not theme:
        raise NotFoundError(f"Theme {theme_id} not found")
    return _theme_to_out(theme)


@router.get("/{theme_id}/variables", response=ThemeCSSVariablesOut)
def get_theme_variables(request, theme_id: UUID):
    """Get CSS variables for a theme."""
    theme = ThemeService.get_theme(theme_id)
    if not theme:
        raise NotFoundError(f"Theme {theme_id} not found")
    variables = ThemeService.get_css_variables(theme)
    return ThemeCSSVariablesOut(variables=variables)


@router.get("/{theme_id}/css", response=ThemeCSSOut)
def get_theme_css(request, theme_id: UUID):
    """Get generated CSS for a theme."""
    theme = ThemeService.get_theme(theme_id)
    if not theme:
        raise NotFoundError(f"Theme {theme_id} not found")
    css = ThemeService.get_css(theme)
    return ThemeCSSOut(css=css)


@router.patch("/{theme_id}", response=ThemeOut)
def update_theme(request, theme_id: UUID, payload: ThemeUpdate):
    """Update a theme."""
    theme = ThemeService.get_theme(theme_id)
    if not theme:
        raise NotFoundError(f"Theme {theme_id} not found")
    theme = ThemeService.update_theme(theme, payload.dict(exclude_unset=True))
    return _theme_to_out(theme)


@router.post("/{theme_id}/set-default", response=ThemeOut)
def set_default_theme(request, theme_id: UUID):
    """Set a theme as the default."""
    theme = ThemeService.get_theme(theme_id)
    if not theme:
        raise NotFoundError(f"Theme {theme_id} not found")
    theme = ThemeService.update_theme(theme, {"is_default": True})
    return _theme_to_out(theme)


@router.delete("/{theme_id}", response={204: None})
def delete_theme(request, theme_id: UUID):
    """Delete a theme."""
    theme = ThemeService.get_theme(theme_id)
    if not theme:
        raise NotFoundError(f"Theme {theme_id} not found")
    ThemeService.delete_theme(theme)
    return 204, None
