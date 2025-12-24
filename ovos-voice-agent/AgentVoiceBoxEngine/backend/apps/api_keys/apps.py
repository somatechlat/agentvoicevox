"""Django app configuration for API keys."""
from django.apps import AppConfig


class ApiKeysConfig(AppConfig):
    """API Keys app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.api_keys"
    verbose_name = "API Key Management"

    def ready(self):
        """Import signals when app is ready."""
        pass
