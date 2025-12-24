"""
Theme models for UI customization.

Stores theme configurations for the portal UI.
"""
import uuid

from django.db import models

from apps.tenants.models import TenantScopedManager, TenantScopedModel


class Theme(TenantScopedModel):
    """
    Theme model for UI customization.

    Stores CSS variables and branding for the portal.
    """

    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # Basic info
    name = models.CharField(
        max_length=255,
        help_text="Theme name",
    )
    description = models.TextField(
        blank=True,
        help_text="Theme description",
    )

    # Colors (AgentSkin CSS variables)
    primary_color = models.CharField(
        max_length=7,
        default="#6366f1",
        help_text="Primary color (--eog-primary)",
    )
    secondary_color = models.CharField(
        max_length=7,
        default="#8b5cf6",
        help_text="Secondary color (--eog-secondary)",
    )
    accent_color = models.CharField(
        max_length=7,
        default="#06b6d4",
        help_text="Accent color (--eog-accent)",
    )
    background_color = models.CharField(
        max_length=7,
        default="#0f172a",
        help_text="Background color (--eog-bg)",
    )
    surface_color = models.CharField(
        max_length=7,
        default="#1e293b",
        help_text="Surface color (--eog-surface)",
    )
    text_color = models.CharField(
        max_length=7,
        default="#f8fafc",
        help_text="Text color (--eog-text)",
    )
    text_muted_color = models.CharField(
        max_length=7,
        default="#94a3b8",
        help_text="Muted text color (--eog-text-muted)",
    )
    border_color = models.CharField(
        max_length=7,
        default="#334155",
        help_text="Border color (--eog-border)",
    )
    success_color = models.CharField(
        max_length=7,
        default="#22c55e",
        help_text="Success color (--eog-success)",
    )
    warning_color = models.CharField(
        max_length=7,
        default="#f59e0b",
        help_text="Warning color (--eog-warning)",
    )
    error_color = models.CharField(
        max_length=7,
        default="#ef4444",
        help_text="Error color (--eog-error)",
    )

    # Typography
    font_family = models.CharField(
        max_length=255,
        default="Inter, system-ui, sans-serif",
        help_text="Font family",
    )
    font_size_base = models.CharField(
        max_length=20,
        default="16px",
        help_text="Base font size",
    )

    # Spacing
    border_radius = models.CharField(
        max_length=20,
        default="0.5rem",
        help_text="Border radius",
    )

    # Custom CSS
    custom_css = models.TextField(
        blank=True,
        help_text="Additional custom CSS",
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether the theme is active",
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default theme",
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Managers
    objects = TenantScopedManager()
    all_objects = models.Manager()

    class Meta:
        db_table = "themes"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_theme_name_per_tenant",
            ),
        ]

    def __str__(self) -> str:
        return self.name

    def to_css_variables(self) -> dict:
        """Convert theme to CSS variables."""
        return {
            "--eog-primary": self.primary_color,
            "--eog-secondary": self.secondary_color,
            "--eog-accent": self.accent_color,
            "--eog-bg": self.background_color,
            "--eog-surface": self.surface_color,
            "--eog-text": self.text_color,
            "--eog-text-muted": self.text_muted_color,
            "--eog-border": self.border_color,
            "--eog-success": self.success_color,
            "--eog-warning": self.warning_color,
            "--eog-error": self.error_color,
            "--eog-font-family": self.font_family,
            "--eog-font-size-base": self.font_size_base,
            "--eog-border-radius": self.border_radius,
        }

    def to_css(self) -> str:
        """Generate CSS string from theme."""
        variables = self.to_css_variables()
        css_vars = "\n".join(f"  {k}: {v};" for k, v in variables.items())
        css = f":root {{\n{css_vars}\n}}"
        if self.custom_css:
            css += f"\n\n{self.custom_css}"
        return css
