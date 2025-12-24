"""Django app configuration for workflows."""
from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    """Workflows app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workflows"
    verbose_name = "Temporal Workflows"

    def ready(self):
        """Import signals when app is ready."""
        pass
