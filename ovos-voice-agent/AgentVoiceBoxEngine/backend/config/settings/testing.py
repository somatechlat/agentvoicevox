"""
Django testing settings for AgentVoiceBox Platform.

These settings are optimized for running tests.
Uses in-memory databases and caches for speed.
"""
from .base import *  # noqa: F401, F403

# ==========================================================================
# DEBUG MODE
# ==========================================================================
DEBUG = False

# ==========================================================================
# FASTER PASSWORD HASHING FOR TESTS
# ==========================================================================
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# ==========================================================================
# IN-MEMORY CACHE FOR TESTS
# ==========================================================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# ==========================================================================
# IN-MEMORY CHANNEL LAYER FOR TESTS
# ==========================================================================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    }
}

# ==========================================================================
# EMAIL (In-memory for tests)
# ==========================================================================
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# ==========================================================================
# LOGGING (Minimal for tests)
# ==========================================================================
LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "null": {
            "class": "logging.NullHandler",
        },
    },
    "root": {
        "handlers": ["null"],
        "level": "CRITICAL",
    },
}

# ==========================================================================
# SECURITY (Disabled for tests)
# ==========================================================================
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# ==========================================================================
# MIDDLEWARE (Remove rate limiting for tests)
# ==========================================================================
MIDDLEWARE = [m for m in MIDDLEWARE if "RateLimit" not in m]  # noqa: F405

# ==========================================================================
# TEST DATABASE
# ==========================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test_agentvoicebox",
        "USER": env.db_user,  # noqa: F405
        "PASSWORD": env.db_password,  # noqa: F405
        "HOST": env.db_host,  # noqa: F405
        "PORT": env.db_port,  # noqa: F405
        "TEST": {
            "NAME": "test_agentvoicebox",
        },
    }
}
