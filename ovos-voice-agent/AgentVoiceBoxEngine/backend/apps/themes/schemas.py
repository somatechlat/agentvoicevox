"""
Pydantic schemas for theme management API.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from ninja import Schema


# ==========================================================================
# THEME SCHEMAS
# ==========================================================================
class ThemeCreate(Schema):
    """Schema for creating a theme."""

    name: str
    description: str = ""

    # Colors (AgentSkin CSS variables)
    primary_color: str = "#6366f1"
    secondary_color: str = "#8b5cf6"
    accent_color: str = "#06b6d4"
    background_color: str = "#0f172a"
    surface_color: str = "#1e293b"
    text_color: str = "#f8fafc"
    text_muted_color: str = "#94a3b8"
    border_color: str = "#334155"
    success_color: str = "#22c55e"
    warning_color: str = "#f59e0b"
    error_color: str = "#ef4444"

    # Typography
    font_family: str = "Inter, system-ui, sans-serif"
    font_size_base: str = "16px"

    # Spacing
    border_radius: str = "0.5rem"

    # Custom CSS
    custom_css: str = ""

    # Status
    is_active: bool = True
    is_default: bool = False


class ThemeUpdate(Schema):
    """Schema for updating a theme."""

    name: Optional[str] = None
    description: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    surface_color: Optional[str] = None
    text_color: Optional[str] = None
    text_muted_color: Optional[str] = None
    border_color: Optional[str] = None
    success_color: Optional[str] = None
    warning_color: Optional[str] = None
    error_color: Optional[str] = None
    font_family: Optional[str] = None
    font_size_base: Optional[str] = None
    border_radius: Optional[str] = None
    custom_css: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class ThemeOut(Schema):
    """Schema for theme response."""

    id: UUID
    tenant_id: UUID
    name: str
    description: str
    primary_color: str
    secondary_color: str
    accent_color: str
    background_color: str
    surface_color: str
    text_color: str
    text_muted_color: str
    border_color: str
    success_color: str
    warning_color: str
    error_color: str
    font_family: str
    font_size_base: str
    border_radius: str
    custom_css: str
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime


class ThemeListOut(Schema):
    """Schema for paginated theme list."""

    items: list[ThemeOut]
    total: int
    page: int
    page_size: int


class ThemeCSSOut(Schema):
    """Schema for theme CSS output."""

    css: str


class ThemeCSSVariablesOut(Schema):
    """Schema for theme CSS variables output."""

    variables: dict[str, str]
