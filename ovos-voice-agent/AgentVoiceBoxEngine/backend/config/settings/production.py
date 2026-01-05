"""
Django production settings for AgentVoiceBox Platform.

These settings are optimized for production deployment.
Security headers and HTTPS are enforced.
"""

from .base import *  # noqa: F401, F403

# ==========================================================================
# DEBUG MODE (NEVER True in production)
# ==========================================================================
DEBUG = False

# ==========================================================================
# SECURITY SETTINGS
# ==========================================================================
# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS (HTTP Strict Transport Security)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Content Security
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# Referrer Policy
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# ==========================================================================
# COOKIE SECURITY
# ==========================================================================
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# ==========================================================================
# CORS (Strict in production)
# ==========================================================================
CORS_ALLOW_ALL_ORIGINS = False
# CORS_ALLOWED_ORIGINS is set from environment in base.py

# ==========================================================================
# LOGGING (JSON format for production)
# ==========================================================================
LOGGING["handlers"]["console"]["formatter"] = "json"  # noqa: F405

# ==========================================================================
# CACHE (Production Redis settings)
# ==========================================================================
# Django's built-in Redis cache doesn't support socket_timeout options
# These are handled at the connection level by redis-py

# ==========================================================================
# DATABASE (Production optimizations)
# ==========================================================================
DATABASES["default"]["CONN_MAX_AGE"] = 600  # 10 minutes  # noqa: F405
DATABASES["default"]["OPTIONS"]["sslmode"] = "require"  # noqa: F405

# ==========================================================================
# STATIC FILES (WhiteNoise for production)
# ==========================================================================
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # noqa: F405
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
