"""Django app configuration for themes."""
from django.apps import AppConfig


class ThemesConfig(AppConfig):
    """Themes app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.themes"
    verbose_name = "Theme Management"

    def ready(self):
        """Import signals when app is ready."""
        pass
