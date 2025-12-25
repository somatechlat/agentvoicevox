"""
Environment configuration using pydantic-settings.

All environment variables are validated at startup.
Missing required variables cause immediate failure with clear error messages.
"""
import sys
from typing import List, Optional

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
        default="localhost,127.0.0.1",
        description="Comma-separated list of allowed hosts",
    )
    django_settings_module: str = Field(
        default="config.settings.development",
        description="Django settings module path",
    )

    # ==========================================================================
    # DATABASE (PostgreSQL)
    # ==========================================================================
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="agentvoicebox", description="Database name")
    db_user: str = Field(default="agentvoicebox", description="Database user")
    db_password: str = Field(..., description="Database password")
    db_conn_max_age: int = Field(default=60, description="Database connection max age")

    # ==========================================================================
    # REDIS
    # ==========================================================================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL",
    )
    redis_cache_db: int = Field(default=1, description="Redis database for cache")
    redis_session_db: int = Field(default=2, description="Redis database for sessions")
    redis_channel_db: int = Field(default=3, description="Redis database for channels")

    # ==========================================================================
    # KEYCLOAK
    # ==========================================================================
    keycloak_url: str = Field(
        default="http://localhost:8080",
        description="Keycloak server URL",
    )
    keycloak_realm: str = Field(
        default="agentvoicebox",
        description="Keycloak realm name",
    )
    keycloak_client_id: str = Field(
        default="agentvoicebox-backend",
        description="Keycloak client ID",
    )
    keycloak_client_secret: Optional[str] = Field(
        default=None,
        description="Keycloak client secret",
    )

    # ==========================================================================
    # SPICEDB
    # ==========================================================================
    spicedb_endpoint: str = Field(
        default="localhost:50051",
        description="SpiceDB gRPC endpoint",
    )
    spicedb_token: str = Field(..., description="SpiceDB preshared key")
    spicedb_insecure: bool = Field(
        default=True,
        description="Use insecure connection (dev only)",
    )

    # ==========================================================================
    # TEMPORAL
    # ==========================================================================
    temporal_host: str = Field(
        default="localhost:7233",
        description="Temporal server host:port",
    )
    temporal_namespace: str = Field(
        default="agentvoicebox",
        description="Temporal namespace",
    )
    temporal_task_queue: str = Field(
        default="default",
        description="Default Temporal task queue",
    )

    # ==========================================================================
    # HASHICORP VAULT
    # ==========================================================================
    vault_addr: str = Field(
        default="http://localhost:8200",
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
        default="http://localhost:8181",
        description="OPA server URL",
    )
    opa_decision_path: str = Field(
        default="/v1/data/agentvoicebox/allow",
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
        default="localhost:9092",
        description="Kafka bootstrap servers (comma-separated)",
    )
    kafka_consumer_group: str = Field(
        default="agentvoicebox-backend",
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
        default="http://localhost:3000",
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
    # CORS
    # ==========================================================================
    cors_allowed_origins: str = Field(
        default="http://localhost:3000",
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

    # ==========================================================================
    # COMPUTED PROPERTIES
    # ==========================================================================
    @property
    def allowed_hosts_list(self) -> List[str]:
        """Parse allowed hosts into list."""
        return [h.strip() for h in self.django_allowed_hosts.split(",") if h.strip()]

    @property
    def cors_origins_list(self) -> List[str]:
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

# SpiceDB
spicedb_endpoint = _settings.spicedb_endpoint
spicedb_token = _settings.spicedb_token
spicedb_insecure = _settings.spicedb_insecure

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

# CORS
cors_allowed_origins = _settings.cors_allowed_origins
cors_allow_credentials = _settings.cors_allow_credentials
cors_origins_list = _settings.cors_origins_list

# Rate Limiting
rate_limit_default = _settings.rate_limit_default
rate_limit_api_key = _settings.rate_limit_api_key
rate_limit_admin = _settings.rate_limit_admin
