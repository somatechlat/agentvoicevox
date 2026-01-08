"""
Django base settings for AgentVoiceBox Platform.

This module contains settings common to all environments.
Environment-specific settings override these in their respective modules.
"""

from pathlib import Path

from . import settings_config as env

# ==========================================================================
# PATH CONFIGURATION
# ==========================================================================
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent  # AgentVoiceBoxEngine directory

# ==========================================================================
# CORE DJANGO SETTINGS
# ==========================================================================
SECRET_KEY = env.django_secret_key
DEBUG = env.django_debug
ALLOWED_HOSTS = env.allowed_hosts_list

VOICE_AGENT = {
    "BASE_URL": env.voice_agent_base_url,
    "WS_BASE_URL": env.voice_agent_ws_base_url,
}

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # PostgreSQL-specific features
]

THIRD_PARTY_APPS = [
    "ninja",  # Django Ninja REST API
    "channels",  # Django Channels WebSocket
    "corsheaders",  # CORS handling
    "django_prometheus",  # Prometheus metrics
    "django_structlog",  # Structured logging
]

LOCAL_APPS = [
    "apps.core",  # Core shared functionality
    "apps.tenants",  # Multi-tenancy
    "apps.users",  # User management
    "apps.projects",  # Project management
    "apps.api_keys",  # API key management
    "apps.sessions",  # Voice sessions
    "apps.billing",  # Billing integration (Lago)
    "apps.voice",  # Voice configuration
    "apps.themes",  # Theme management
    "apps.audit",  # Audit logging
    "apps.notifications",  # Notifications
    "apps.workflows",  # Temporal workflows
    "apps.realtime",  # OpenAI Realtime API
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ==========================================================================
# MIDDLEWARE
# ==========================================================================
MIDDLEWARE = [
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Custom middleware
    "apps.core.middleware.request_logging.RequestLoggingMiddleware",
    "apps.core.middleware.tenant.TenantMiddleware",
    "apps.core.middleware.authentication.KeycloakAuthenticationMiddleware",
    "apps.core.middleware.rate_limit.RateLimitMiddleware",
    "apps.core.middleware.audit.AuditMiddleware",
    "apps.core.middleware.exception_handler.ExceptionMiddleware",
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

ROOT_URLCONF = "config.urls"

# ==========================================================================
# TEMPLATES
# ==========================================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
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

# ==========================================================================
# ASGI APPLICATION
# ==========================================================================
ASGI_APPLICATION = "config.asgi.application"
WSGI_APPLICATION = "config.wsgi.application"

# ==========================================================================
# DATABASE (PostgreSQL with Django ORM)
# ==========================================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env.db_name,
        "USER": env.db_user,
        "PASSWORD": env.db_password,
        "HOST": env.db_host,
        "PORT": env.db_port,
        "CONN_MAX_AGE": env.db_conn_max_age,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30 second query timeout
        },
    }
}

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ==========================================================================
# CUSTOM USER MODEL
# ==========================================================================
AUTH_USER_MODEL = "users.User"

# ==========================================================================
# PASSWORD VALIDATION
# ==========================================================================
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ==========================================================================
# INTERNATIONALIZATION
# ==========================================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ==========================================================================
# STATIC FILES
# ==========================================================================
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# STATICFILES_DIRS only needed if you have additional static files outside apps
# STATICFILES_DIRS = [BASE_DIR / "static"]

# ==========================================================================
# MEDIA FILES
# ==========================================================================
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ==========================================================================
# REDIS CACHE
# ==========================================================================
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.redis_url.replace("/0", f"/{env.redis_cache_db}"),
        "KEY_PREFIX": "avb",
    }
}

# ==========================================================================
# SESSION (Redis-backed)
# ==========================================================================
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_AGE = 86400  # 24 hours

# ==========================================================================
# DJANGO CHANNELS (WebSocket)
# ==========================================================================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [env.redis_url.replace("/0", f"/{env.redis_channel_db}")],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# ==========================================================================
# CORS CONFIGURATION
# ==========================================================================
CORS_ALLOWED_ORIGINS = env.cors_origins_list
CORS_ALLOW_CREDENTIALS = env.cors_allow_credentials
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-tenant-id",
    "x-api-key",
    "x-request-id",
]

# ==========================================================================
# KEYCLOAK CONFIGURATION
# ==========================================================================
KEYCLOAK = {
    "URL": env.keycloak_url,
    "REALM": env.keycloak_realm,
    "CLIENT_ID": env.keycloak_client_id,
    "CLIENT_SECRET": env.keycloak_client_secret,
    "ALGORITHMS": ["RS256"],
    "AUDIENCE": env.keycloak_client_id,
}

# ==========================================================================
# TEMPORAL CONFIGURATION
# ==========================================================================
TEMPORAL = {
    "HOST": env.temporal_host,
    "NAMESPACE": env.temporal_namespace,
    "TASK_QUEUE": env.temporal_task_queue,
}

# ==========================================================================
# VAULT CONFIGURATION
# ==========================================================================
VAULT = {
    "ADDR": env.vault_addr,
    "TOKEN": env.vault_token,
    "ROLE_ID": env.vault_role_id,
    "SECRET_ID": env.vault_secret_id,
    "MOUNT_POINT": env.vault_mount_point,
    "FAIL_FAST": env.vault_fail_fast,
}

# ==========================================================================
# OPA CONFIGURATION
# ==========================================================================
OPA = {
    "URL": env.opa_url,
    "DECISION_PATH": env.opa_decision_path,
    "TIMEOUT_SECONDS": env.opa_timeout_seconds,
    "ENABLED": env.opa_enabled,
}

# ==========================================================================
# KAFKA CONFIGURATION
# ==========================================================================
KAFKA = {
    "BOOTSTRAP_SERVERS": env.kafka_bootstrap_servers,
    "CONSUMER_GROUP": env.kafka_consumer_group,
    "ENABLED": env.kafka_enabled,
    "SECURITY_PROTOCOL": env.kafka_security_protocol,
}

# ==========================================================================
# LAGO BILLING CONFIGURATION
# ==========================================================================
LAGO = {
    "API_URL": env.lago_api_url,
    "API_KEY": env.lago_api_key,
    "WEBHOOK_SECRET": env.lago_webhook_secret,
}

# ==========================================================================
# LLM PROVIDER CONFIGURATION
# ==========================================================================
LLM_PROVIDERS = {
    "groq": {
        "api_key": env.groq_api_key,
        "base_url": env.groq_api_base,
    },
    "openai": {
        "api_key": env.openai_api_key,
        "base_url": env.openai_api_base,
    },
    "ollama": {
        "base_url": env.ollama_base_url,
    },
}

# ==========================================================================
# RATE LIMITING
# ==========================================================================
RATE_LIMITS = {
    "DEFAULT": env.rate_limit_default,
    "API_KEY": env.rate_limit_api_key,
    "ADMIN": env.rate_limit_admin,
}

# ==========================================================================
# REALTIME RATE LIMITING
# ==========================================================================
REALTIME_RATE_LIMITS = {
    "REQUESTS_PER_MINUTE": env.realtime_requests_per_minute,
    "TOKENS_PER_MINUTE": env.realtime_tokens_per_minute,
    "WINDOW_SECONDS": env.realtime_rate_limit_window_seconds,
}

# ==========================================================================
# WORKER CONFIGURATION
# ==========================================================================
REDIS_WORKER = {
    "URL": env.redis_url,
    "MAX_CONNECTIONS": env.redis_max_connections,
    "SOCKET_TIMEOUT": env.redis_socket_timeout,
    "SOCKET_CONNECT_TIMEOUT": env.redis_socket_connect_timeout,
    "RETRY_ON_TIMEOUT": env.redis_retry_on_timeout,
    "HEALTH_CHECK_INTERVAL": env.redis_health_check_interval,
}

LLM_WORKER = {
    "DEFAULT_PROVIDER": env.llm_default_provider,
    "DEFAULT_MODEL": env.llm_default_model,
    "MAX_TOKENS": env.llm_max_tokens,
    "TEMPERATURE": env.llm_temperature,
    "CIRCUIT_BREAKER_THRESHOLD": env.llm_circuit_breaker_threshold,
    "CIRCUIT_BREAKER_TIMEOUT": env.llm_circuit_breaker_timeout,
    "MAX_HISTORY_ITEMS": env.llm_max_history_items,
    "PROVIDER_PRIORITY": [
        provider.strip()
        for provider in env.llm_provider_priority.split(",")
        if provider.strip()
    ],
    "STREAM_REQUESTS": env.llm_stream_requests,
    "GROUP_WORKERS": env.llm_group_workers,
    "RESPONSE_CHANNEL": env.llm_response_channel,
}

STT_WORKER = {
    "MODEL": env.stt_model,
    "DEVICE": env.stt_device,
    "COMPUTE_TYPE": env.stt_compute_type,
    "BATCH_SIZE": env.stt_batch_size,
    "SAMPLE_RATE": env.stt_sample_rate,
    "STREAM_AUDIO": env.stt_stream_audio,
    "GROUP_WORKERS": env.stt_group_workers,
    "CHANNEL_TRANSCRIPTION": env.stt_channel_transcription,
}

TTS_WORKER = {
    "MODEL_DIR": env.tts_model_dir,
    "MODEL_FILE": env.tts_model_file,
    "VOICES_FILE": env.tts_voices_file,
    "DEFAULT_VOICE": env.tts_default_voice,
    "DEFAULT_SPEED": env.tts_default_speed,
    "CHUNK_SIZE": env.tts_chunk_size,
    "STREAM_REQUESTS": env.tts_stream_requests,
    "GROUP_WORKERS": env.tts_group_workers,
    "CHANNEL_TTS": env.tts_channel_tts,
    "CHANNEL_AUDIO_OUT": env.tts_channel_audio_out,
}

# ==========================================================================
# LOGGING (Standard Python logging)
# ==========================================================================

# Standard Python logging configuration
# Using simple formatters without external dependencies
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
        "console": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env.log_level,
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": env.log_level,
            "propagate": False,
        },
    },
}
