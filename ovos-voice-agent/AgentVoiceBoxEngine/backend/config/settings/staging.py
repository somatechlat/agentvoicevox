"""
Django staging settings for AgentVoiceBox Platform.

These settings are similar to production but with some relaxations
for testing and debugging in a staging environment.
"""
from .production import *  # noqa: F401, F403

# ==========================================================================
# DEBUG (Can be enabled for staging debugging)
# ==========================================================================
DEBUG = env.django_debug  # noqa: F405

# ==========================================================================
# LOGGING (More verbose than production)
# ==========================================================================
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405

# ==========================================================================
# DATABASE (Staging may use different SSL settings)
# ==========================================================================
DATABASES["default"]["OPTIONS"]["sslmode"] = "prefer"  # noqa: F405
