"""
Environment configuration using pydantic-settings.

All environment variables are validated at startup.
Missing required variables cause immediate failure with clear error messages.
"""
from typing import List, Optional

from pydantic import Field, field_validator
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
