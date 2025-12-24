"""Django app configuration for projects."""
from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    """Projects app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.projects"
    verbose_name = "Project Management"

    def ready(self):
        """Import signals when app is ready."""
        pass
