"""Django app configuration for voice."""

from django.apps import AppConfig


class VoiceConfig(AppConfig):
    """Voice app configuration."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.voice"
    verbose_name = "Voice Configuration"

    def ready(self):
        """Import signals when app is ready."""
        pass
