"""
Django development settings for AgentVoiceBox Platform.

These settings are optimized for local development with Docker.
"""

import os
from .base import *  # noqa: F401, F403

# ==========================================================================
# DEBUG MODE
# ==========================================================================
# Default to True for dev, but allow override for "Local Production" testing
DEBUG = os.getenv("DEBUG", "True").lower() == "true"

# ==========================================================================
# ALLOWED HOSTS (Development)
# ==========================================================================
if os.getenv("DJANGO_ALLOWED_HOSTS"):
    ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS").split(",")
else:
    ALLOWED_HOSTS = ["*"]  # Allow all hosts in development default

# ==========================================================================
# CORS (Allow all in development)
# ==========================================================================
if os.getenv("CORS_ALLOW_ALL_ORIGINS"):
     CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS").lower() == "true"
else:
    CORS_ALLOW_ALL_ORIGINS = True

# ==========================================================================
# EMAIL (Console backend for development)
# ==========================================================================
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ==========================================================================
# DJANGO DEBUG TOOLBAR (Optional)
# ==========================================================================
try:
    import debug_toolbar  # noqa: F401

    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    INTERNAL_IPS = ["127.0.0.1", "localhost"]
except ImportError:
    pass

# ==========================================================================
# SECURITY (Relaxed for development)
# ==========================================================================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ==========================================================================
# LOGGING (More verbose in development)
# ==========================================================================
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
LOGGING["loggers"]["apps"]["level"] = "DEBUG"  # noqa: F405
LOGGING["handlers"]["console"]["formatter"] = "console"  # noqa: F405

# ==========================================================================
# CACHE (Use local memory in development if Redis unavailable)
# ==========================================================================
# Uncomment to use local memory cache instead of Redis
# CACHES = {
#     "default": {
#         "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
#     }
# }
