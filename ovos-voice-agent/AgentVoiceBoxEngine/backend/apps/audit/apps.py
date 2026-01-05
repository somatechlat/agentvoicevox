"""Django app configuration for audit."""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Audit app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.audit"
    verbose_name = "Audit Logging"

    def ready(self):
        """Import signals when app is ready."""
        pass
