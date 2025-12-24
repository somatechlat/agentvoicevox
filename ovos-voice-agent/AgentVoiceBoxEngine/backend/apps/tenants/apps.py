"""Tenants app configuration."""
from django.apps import AppConfig


class TenantsConfig(AppConfig):
    """Configuration for the tenants app."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.tenants"
    label = "tenants"
    verbose_name = "Tenants"
    
    def ready(self):
        """Initialize app when Django starts."""
        # Import signals to register them
        from . import signals  # noqa: F401
