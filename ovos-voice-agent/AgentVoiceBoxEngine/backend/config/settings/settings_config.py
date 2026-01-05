"""
Environment configuration using pydantic-settings.

All environment variables are validated at startup.
Missing required variables cause immediate failure with clear error messages.
"""

import sys
from typing import Optional

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Required variables will cause startup failure if missing.
    Optional variables have sensible defaults.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================================
    # DJANGO CORE
    # ==========================================================================
    django_secret_key: str = Field(
        ...,
        min_length=50,
        description="Django secret key (minimum 50 characters)",
    )
    django_debug: bool = Field(default=False, description="Debug mode")
    django_allowed_hosts: str = Field(
        ...,
        description="Comma-separated list of allowed hosts",
    )
    django_settings_module: str = Field(
        ...,
        description="Django settings module path",
    )

    # ==========================================================================
    # VOICE AGENT BASE URLS
    # ==========================================================================
    voice_agent_base_url: str = Field(
        ...,
        description="Public HTTP base URL for voice agent",
    )
    voice_agent_ws_base_url: str = Field(
        ...,
        description="Public WS base URL for voice agent",
    )

    # ==========================================================================
    # DATABASE (PostgreSQL)
    # ==========================================================================
    db_host: str = Field(..., description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(..., description="Database name")
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")
    db_conn_max_age: int = Field(default=60, description="Database connection max age")

    # ==========================================================================
    # REDIS
    # ==========================================================================
    redis_url: str = Field(
        ...,
        description="Redis connection URL",
    )
    redis_cache_db: int = Field(default=1, description="Redis database for cache")
    redis_session_db: int = Field(default=2, description="Redis database for sessions")
    redis_channel_db: int = Field(default=3, description="Redis database for channels")

    # ==========================================================================
    # KEYCLOAK
    # ==========================================================================
    keycloak_url: str = Field(
        ...,
        description="Keycloak server URL",
    )
    keycloak_realm: str = Field(
        ...,
        description="Keycloak realm name",
    )
    keycloak_client_id: str = Field(
        ...,
        description="Keycloak client ID",
    )
    keycloak_client_secret: Optional[str] = Field(
        default=None,
        description="Keycloak client secret",
    )

    # ==========================================================================
    # TEMPORAL
    # ==========================================================================
    temporal_host: str = Field(
        ...,
        description="Temporal server host:port",
    )
    temporal_namespace: str = Field(
        ...,
        description="Temporal namespace",
    )
    temporal_task_queue: str = Field(
        ...,
        description="Default Temporal task queue",
    )

    # ==========================================================================
    # HASHICORP VAULT
    # ==========================================================================
    vault_addr: str = Field(
        ...,
        description="Vault server address",
    )
    vault_token: Optional[str] = Field(
        default=None,
        description="Vault token (dev mode)",
    )
    vault_role_id: Optional[str] = Field(
        default=None,
        description="Vault AppRole role ID",
    )
    vault_secret_id: Optional[str] = Field(
        default=None,
        description="Vault AppRole secret ID",
    )
    vault_mount_point: str = Field(
        default="secret",
        description="Vault KV mount point",
    )
    vault_fail_fast: bool = Field(
        default=True,
        description="Fail startup if Vault is unavailable",
    )

    # ==========================================================================
    # OPA (Open Policy Agent)
    # ==========================================================================
    opa_url: str = Field(
        ...,
        description="OPA server URL",
    )
    opa_decision_path: str = Field(
        ...,
        description="OPA decision path for policy evaluation",
    )
    opa_timeout_seconds: int = Field(
        default=3,
        description="OPA request timeout in seconds",
    )
    opa_enabled: bool = Field(
        default=True,
        description="Enable OPA policy enforcement",
    )

    # ==========================================================================
    # KAFKA
    # ==========================================================================
    kafka_bootstrap_servers: str = Field(
        ...,
        description="Kafka bootstrap servers (comma-separated)",
    )
    kafka_consumer_group: str = Field(
        ...,
        description="Kafka consumer group ID",
    )
    kafka_enabled: bool = Field(
        default=False,
        description="Enable Kafka event streaming",
    )
    kafka_security_protocol: str = Field(
        default="PLAINTEXT",
        description="Kafka security protocol (PLAINTEXT, SSL, SASL_PLAINTEXT, SASL_SSL)",
    )

    # ==========================================================================
    # LAGO BILLING
    # ==========================================================================
    lago_api_url: str = Field(
        ...,
        description="Lago API URL",
    )
    lago_api_key: Optional[str] = Field(
        default=None,
        description="Lago API key",
    )
    lago_webhook_secret: Optional[str] = Field(
        default=None,
        description="Lago webhook secret",
    )

    # ==========================================================================
    # OBSERVABILITY
    # ==========================================================================
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(
        default="json",
        description="Log format: json or console",
    )
    sentry_dsn: Optional[str] = Field(default=None, description="Sentry DSN")
    prometheus_enabled: bool = Field(
        default=True,
        description="Enable Prometheus metrics",
    )

    # ==========================================================================
    # LLM PROVIDERS
    # ==========================================================================
    groq_api_key: str = Field(default="", description="Groq API key")
    openai_api_key: str = Field(default="", description="OpenAI API key")
    groq_api_base: str = Field(
        ...,
        description="Groq API base URL",
    )
    openai_api_base: str = Field(
        ...,
        description="OpenAI API base URL",
    )
    ollama_base_url: str = Field(
        ...,
        description="Ollama base URL",
    )
    llm_default_provider: str = Field(
        ...,
        description="Default LLM provider",
    )
    llm_default_model: str = Field(
        ...,
        description="Default LLM model",
    )
    llm_max_tokens: int = Field(
        ...,
        description="Default LLM max tokens",
    )
    llm_temperature: float = Field(
        ...,
        description="Default LLM temperature",
    )
    llm_circuit_breaker_threshold: int = Field(
        ...,
        description="LLM circuit breaker failure threshold",
    )
    llm_circuit_breaker_timeout: float = Field(
        ...,
        description="LLM circuit breaker timeout seconds",
    )
    llm_max_history_items: int = Field(
        ...,
        description="Max conversation items to include in LLM context",
    )
    llm_provider_priority: str = Field(
        ...,
        description="Comma-separated LLM provider priority list",
    )

    # ==========================================================================
    # STT
    # ==========================================================================
    stt_model: str = Field(
        ...,
        description="Whisper model size",
    )
    stt_device: str = Field(
        ...,
        description="STT device (cpu, cuda, auto)",
    )
    stt_compute_type: str = Field(
        ...,
        description="STT compute type",
    )
    stt_batch_size: int = Field(
        ...,
        description="Max concurrent STT transcriptions",
    )
    stt_sample_rate: int = Field(
        ...,
        description="Target sample rate for STT processing",
    )

    # ==========================================================================
    # TTS
    # ==========================================================================
    tts_model_dir: str = Field(
        ...,
        description="Kokoro model directory",
    )
    tts_model_file: str = Field(
        ...,
        description="Kokoro model filename",
    )
    tts_voices_file: str = Field(
        ...,
        description="Kokoro voices filename",
    )
    tts_default_voice: str = Field(
        ...,
        description="Default TTS voice",
    )
    tts_default_speed: float = Field(
        ...,
        description="Default TTS speed",
    )
    tts_chunk_size: int = Field(
        ...,
        description="TTS chunk size (samples)",
    )

    # ==========================================================================
    # WORKER STREAMS
    # ==========================================================================
    llm_stream_requests: str = Field(
        ...,
        description="Redis stream for LLM requests",
    )
    llm_group_workers: str = Field(
        ...,
        description="Redis consumer group for LLM workers",
    )
    llm_response_channel: str = Field(
        ...,
        description="Redis channel prefix for LLM responses",
    )
    stt_stream_audio: str = Field(
        ...,
        description="Redis stream for STT audio",
    )
    stt_group_workers: str = Field(
        ...,
        description="Redis consumer group for STT workers",
    )
    stt_channel_transcription: str = Field(
        ...,
        description="Redis channel prefix for STT results",
    )
    tts_stream_requests: str = Field(
        ...,
        description="Redis stream for TTS requests",
    )
    tts_group_workers: str = Field(
        ...,
        description="Redis consumer group for TTS workers",
    )
    tts_channel_tts: str = Field(
        ...,
        description="Redis channel prefix for TTS control",
    )
    tts_channel_audio_out: str = Field(
        ...,
        description="Redis stream prefix for TTS audio output",
    )

    # ==========================================================================
    # REDIS WORKER CONNECTIONS
    # ==========================================================================
    redis_max_connections: int = Field(
        ...,
        description="Redis max connections for workers",
    )
    redis_socket_timeout: float = Field(
        ...,
        description="Redis socket timeout seconds",
    )
    redis_socket_connect_timeout: float = Field(
        ...,
        description="Redis socket connect timeout seconds",
    )
    redis_retry_on_timeout: bool = Field(
        ...,
        description="Redis retry on timeout",
    )
    redis_health_check_interval: int = Field(
        ...,
        description="Redis health check interval seconds",
    )

    # ==========================================================================
    # CORS
    # ==========================================================================
    cors_allowed_origins: str = Field(
        ...,
        description="Comma-separated CORS allowed origins",
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS",
    )

    # ==========================================================================
    # RATE LIMITING
    # ==========================================================================
    rate_limit_default: int = Field(
        default=60,
        description="Default rate limit per minute",
    )
    rate_limit_api_key: int = Field(
        default=120,
        description="API key rate limit per minute",
    )
    rate_limit_admin: int = Field(
        default=300,
        description="Admin rate limit per minute",
    )
    realtime_requests_per_minute: int = Field(
        ...,
        description="Realtime session requests per minute",
    )
    realtime_tokens_per_minute: int = Field(
        ...,
        description="Realtime session tokens per minute",
    )
    realtime_rate_limit_window_seconds: int = Field(
        ...,
        description="Realtime rate limit window in seconds",
    )

    # ==========================================================================
    # COMPUTED PROPERTIES
    # ==========================================================================
    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse allowed hosts into list."""
        return [h.strip() for h in self.django_allowed_hosts.split(",") if h.strip()]

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into list."""
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v.upper()


# ==========================================================================
# INSTANTIATE AND VALIDATE SETTINGS AT MODULE LOAD
# ==========================================================================
try:
    # Create singleton instance - validates all required env vars
    _settings = Settings()
except ValidationError as e:
    print("=" * 60, file=sys.stderr)
    print("CONFIGURATION ERROR: Missing or invalid environment variables", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    for error in e.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        print(f"  - {field}: {error['msg']}", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    sys.exit(1)


# ==========================================================================
# EXPORT ALL SETTINGS AS MODULE-LEVEL ATTRIBUTES
# This allows: from . import settings_config as env; env.db_host
# ==========================================================================

# Django Core
django_secret_key = _settings.django_secret_key
django_debug = _settings.django_debug
django_allowed_hosts = _settings.django_allowed_hosts
django_settings_module = _settings.django_settings_module
allowed_hosts_list = _settings.allowed_hosts_list
voice_agent_base_url = _settings.voice_agent_base_url
voice_agent_ws_base_url = _settings.voice_agent_ws_base_url

# Database
db_host = _settings.db_host
db_port = _settings.db_port
db_name = _settings.db_name
db_user = _settings.db_user
db_password = _settings.db_password
db_conn_max_age = _settings.db_conn_max_age

# Redis
redis_url = _settings.redis_url
redis_cache_db = _settings.redis_cache_db
redis_session_db = _settings.redis_session_db
redis_channel_db = _settings.redis_channel_db

# Keycloak
keycloak_url = _settings.keycloak_url
keycloak_realm = _settings.keycloak_realm
keycloak_client_id = _settings.keycloak_client_id
keycloak_client_secret = _settings.keycloak_client_secret

# Temporal
temporal_host = _settings.temporal_host
temporal_namespace = _settings.temporal_namespace
temporal_task_queue = _settings.temporal_task_queue

# Vault
vault_addr = _settings.vault_addr
vault_token = _settings.vault_token
vault_role_id = _settings.vault_role_id
vault_secret_id = _settings.vault_secret_id
vault_mount_point = _settings.vault_mount_point
vault_fail_fast = _settings.vault_fail_fast

# OPA
opa_url = _settings.opa_url
opa_decision_path = _settings.opa_decision_path
opa_timeout_seconds = _settings.opa_timeout_seconds
opa_enabled = _settings.opa_enabled

# Kafka
kafka_bootstrap_servers = _settings.kafka_bootstrap_servers
kafka_consumer_group = _settings.kafka_consumer_group
kafka_enabled = _settings.kafka_enabled
kafka_security_protocol = _settings.kafka_security_protocol

# Lago
lago_api_url = _settings.lago_api_url
lago_api_key = _settings.lago_api_key
lago_webhook_secret = _settings.lago_webhook_secret

# Observability
log_level = _settings.log_level
log_format = _settings.log_format
sentry_dsn = _settings.sentry_dsn
prometheus_enabled = _settings.prometheus_enabled

# LLM Providers
groq_api_key = _settings.groq_api_key
openai_api_key = _settings.openai_api_key
groq_api_base = _settings.groq_api_base
openai_api_base = _settings.openai_api_base
ollama_base_url = _settings.ollama_base_url
llm_default_provider = _settings.llm_default_provider
llm_default_model = _settings.llm_default_model
llm_max_tokens = _settings.llm_max_tokens
llm_temperature = _settings.llm_temperature
llm_circuit_breaker_threshold = _settings.llm_circuit_breaker_threshold
llm_circuit_breaker_timeout = _settings.llm_circuit_breaker_timeout
llm_max_history_items = _settings.llm_max_history_items
llm_provider_priority = _settings.llm_provider_priority

# STT
stt_model = _settings.stt_model
stt_device = _settings.stt_device
stt_compute_type = _settings.stt_compute_type
stt_batch_size = _settings.stt_batch_size
stt_sample_rate = _settings.stt_sample_rate

# TTS
tts_model_dir = _settings.tts_model_dir
tts_model_file = _settings.tts_model_file
tts_voices_file = _settings.tts_voices_file
tts_default_voice = _settings.tts_default_voice
tts_default_speed = _settings.tts_default_speed
tts_chunk_size = _settings.tts_chunk_size

# Worker Streams
llm_stream_requests = _settings.llm_stream_requests
llm_group_workers = _settings.llm_group_workers
llm_response_channel = _settings.llm_response_channel
stt_stream_audio = _settings.stt_stream_audio
stt_group_workers = _settings.stt_group_workers
stt_channel_transcription = _settings.stt_channel_transcription
tts_stream_requests = _settings.tts_stream_requests
tts_group_workers = _settings.tts_group_workers
tts_channel_tts = _settings.tts_channel_tts
tts_channel_audio_out = _settings.tts_channel_audio_out

# Redis worker connection settings
redis_max_connections = _settings.redis_max_connections
redis_socket_timeout = _settings.redis_socket_timeout
redis_socket_connect_timeout = _settings.redis_socket_connect_timeout
redis_retry_on_timeout = _settings.redis_retry_on_timeout
redis_health_check_interval = _settings.redis_health_check_interval

# CORS
cors_allowed_origins = _settings.cors_allowed_origins
cors_allow_credentials = _settings.cors_allow_credentials
cors_origins_list = _settings.cors_origins_list

# Rate Limiting
rate_limit_default = _settings.rate_limit_default
rate_limit_api_key = _settings.rate_limit_api_key
rate_limit_admin = _settings.rate_limit_admin
realtime_requests_per_minute = _settings.realtime_requests_per_minute
realtime_tokens_per_minute = _settings.realtime_tokens_per_minute
realtime_rate_limit_window_seconds = _settings.realtime_rate_limit_window_seconds
