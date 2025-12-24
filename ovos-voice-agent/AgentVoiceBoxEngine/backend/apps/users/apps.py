"""Django app configuration for users."""
from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Users app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.users"
    verbose_name = "User Management"

    def ready(self):
        """Import signals when app is ready."""
        pass
