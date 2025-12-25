"""
Django app configuration for OpenAI Realtime API.
"""
from django.apps import AppConfig


class RealtimeConfig(AppConfig):
    """Configuration for the realtime app."""
    
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.realtime"
    verbose_name = "OpenAI Realtime API"
    
    def ready(self):
        """Initialize app when Django starts."""
        pass
