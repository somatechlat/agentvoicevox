"""
Django testing settings for AgentVoiceBox Platform.

These settings are optimized for running tests.
Uses in-memory databases and caches for speed.
"""

import os
from pathlib import Path

# Set TESTING flag before importing anything
os.environ["TESTING"] = "true"

# Import settings config for env vars (must be after TESTING flag is set)
from . import settings_config as env  # noqa: E402

# ==========================================================================
# PATH CONFIGURATION
# ==========================================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ==========================================================================
# CORE DJANGO SETTINGS (minimal for testing)
# ==========================================================================
SECRET_KEY = env.django_secret_key
DEBUG = False
ALLOWED_HOSTS = ["*"]

# Minimal apps for testing
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Local apps
    "apps.core",
    "apps.tenants",
    "apps.users",
    "apps.projects",
    "apps.api_keys",
    "apps.sessions",
    "apps.billing",
    "apps.voice",
    "apps.themes",
    "apps.audit",
    "apps.notifications",
    "apps.workflows",
    "apps.realtime",
]

# Minimal middleware for testing
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Custom user model
AUTH_USER_MODEL = "users.User"

# Default primary key
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = "static/"

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
# TEST DATABASE - Use real PostgreSQL on shared services port
# Optimized for parallel test execution with pytest-xdist
# ==========================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "agentvoicebox",  # Database name from init script
        "USER": "shared_admin",  # Shared services user
        "PASSWORD": "shared_secure_2024",  # Shared services password
        "HOST": "localhost",
        "PORT": 65004,  # Shared services PostgreSQL port
        "CONN_MAX_AGE": 60,  # Keep connections alive for 60s (parallel workers)
        "CONN_HEALTH_CHECKS": True,  # Check connection health before use
        "OPTIONS": {
            "connect_timeout": 5,
            # Connection pooling for parallel tests
            "options": "-c statement_timeout=30000",  # 30s statement timeout
        },
        # pytest-xdist creates separate test databases per worker
        "TEST": {
            "NAME": "test_agentvoicebox",
            "SERIALIZE": False,  # Don't serialize test database creation
        },
    }
}

# ==========================================================================
# DISABLE EXTERNAL SERVICES FOR TESTS
# ==========================================================================
# Vault - disable fail-fast and connection
VAULT = {
    "ADDR": "",
    "FAIL_FAST": False,
}

# Keycloak - disable for tests
KEYCLOAK = {
    "URL": "",
    "REALM": "test",
    "CLIENT_ID": "test",
    "CLIENT_SECRET": "test",
    "ALGORITHMS": ["RS256"],
    "AUDIENCE": "test",
}

# Temporal - disable for tests
TEMPORAL = {
    "HOST": "",
    "NAMESPACE": "test",
    "TASK_QUEUE": "test",
}

# OPA - disable for tests
OPA = {
    "URL": "",
    "ENABLED": False,
}

# Kafka - disable for tests
KAFKA = {
    "ENABLED": False,
}

# Lago - disable for tests
LAGO = {
    "API_URL": "",
    "API_KEY": "",
}

# Rate limits for tests (different values to test tier logic)
RATE_LIMITS = {
    "DEFAULT": 100,
    "API_KEY": 500,
    "ADMIN": 1000,
}
