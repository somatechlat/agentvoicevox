"""Django app configuration for voice sessions."""

from django.apps import AppConfig


class SessionsConfig(AppConfig):
    """Sessions app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.sessions"
    label = "voice_sessions"  # Avoid conflict with django.contrib.sessions
    verbose_name = "Voice Sessions"

    def ready(self):
        """Import signals when app is ready."""
        pass
