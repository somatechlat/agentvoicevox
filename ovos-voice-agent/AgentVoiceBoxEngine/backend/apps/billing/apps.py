"""Django app configuration for billing."""
from django.apps import AppConfig


class BillingConfig(AppConfig):
    """Billing app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.billing"
    verbose_name = "Billing Integration"

    def ready(self):
        """Import signals when app is ready."""
        pass
