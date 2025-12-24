"""
Theme management services.

Business logic for theme CRUD and CSS generation.
"""
from typing import Optional
from uuid import UUID

from django.db import transaction

from apps.tenants.models import Tenant
from apps.themes.models import Theme


class ThemeService:
    """Service for managing themes."""

    @staticmethod
    def list_themes(
        tenant: Tenant,
        active_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Theme], int]:
        """
        List themes for a tenant.

        Returns tuple of (themes, total_count).
        """
        qs = Theme.objects.filter(tenant=tenant)
        if active_only:
            qs = qs.filter(is_active=True)

        total = qs.count()
        offset = (page - 1) * page_size
        themes = list(qs.order_by("-is_default", "-created_at")[offset : offset + page_size])

        return themes, total

    @staticmethod
    def get_theme(theme_id: UUID) -> Optional[Theme]:
        """Get a theme by ID."""
        try:
            return Theme.objects.get(id=theme_id)
        except Theme.DoesNotExist:
            return None

    @staticmethod
    def get_default_theme(tenant: Tenant) -> Optional[Theme]:
        """Get the default theme for a tenant."""
        try:
            return Theme.objects.get(tenant=tenant, is_default=True, is_active=True)
        except Theme.DoesNotExist:
            return Theme.objects.filter(tenant=tenant, is_active=True).first()

    @staticmethod
    @transaction.atomic
    def create_theme(tenant: Tenant, data: dict) -> Theme:
        """Create a new theme."""
        if data.get("is_default"):
            Theme.objects.filter(tenant=tenant, is_default=True).update(
                is_default=False
            )

        theme = Theme.objects.create(tenant=tenant, **data)
        return theme

    @staticmethod
    @transaction.atomic
    def update_theme(theme: Theme, data: dict) -> Theme:
        """Update a theme."""
        if data.get("is_default") and not theme.is_default:
            Theme.objects.filter(tenant=theme.tenant, is_default=True).update(
                is_default=False
            )

        for key, value in data.items():
            if value is not None:
                setattr(theme, key, value)
        theme.save()
        return theme

    @staticmethod
    def delete_theme(theme: Theme) -> None:
        """Delete a theme."""
        theme.delete()

    @staticmethod
    def get_css(theme: Theme) -> str:
        """Get full CSS for a theme."""
        return theme.to_css()

    @staticmethod
    def get_css_variables(theme: Theme) -> dict:
        """Get CSS variables dictionary for a theme."""
        return theme.to_css_variables()
