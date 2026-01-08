"""
Pydantic Schemas for the Tenant API
=====================================

This module defines the Pydantic schemas used for data validation, serialization,
and deserialization in the Tenant API endpoints. These schemas form the public
data contract for interacting with tenant and tenant settings resources.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from ninja import Schema
from pydantic import Field, field_validator


class TenantCreateSchema(Schema):
    """
    Defines the request payload for creating a new tenant.
    Used in the admin endpoint for tenant creation.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="The legal or display name of the organization.",
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="A unique, URL-friendly identifier for the tenant.",
    )
    tier: str = Field(
        default="free", description="The initial subscription tier for the tenant."
    )
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="A flexible JSON field for miscellaneous settings.",
    )

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        """Ensures the provided tier is one of the valid choices."""
        from .models import Tenant

        if v not in Tenant.Tier.values:
            raise ValueError(f"Invalid tier. Must be one of: {Tenant.Tier.values}")
        return v


class TenantUpdateSchema(Schema):
    """
    Defines the request payload for updating a tenant's details.
    Used in the admin endpoint. All fields are optional for partial updates.
    """

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="The new name for the organization.",
    )
    settings: Optional[dict[str, Any]] = Field(
        None, description="A dictionary of settings to update in the JSON field."
    )


class TenantResponseSchema(Schema):
    """
    Defines the response structure for a single tenant object.
    This is the standard representation of a tenant returned by the API.
    """

    id: UUID  # The unique identifier for the tenant.
    name: str  # The name of the organization.
    slug: str  # The URL-friendly identifier.
    tier: str  # The current subscription tier (e.g., 'free', 'pro').
    status: str  # The current lifecycle status (e.g., 'active', 'suspended').
    billing_id: str  # The customer ID from the external billing system.
    settings: dict[str, Any]  # Miscellaneous tenant-specific settings.
    max_users: int  # The maximum number of users this tenant can have.
    max_projects: int  # The maximum number of projects this tenant can create.
    max_api_keys: int  # The maximum number of active API keys.
    max_sessions_per_month: int  # The monthly session usage limit.
    created_at: datetime  # Timestamp of when the tenant was created.
    updated_at: datetime  # Timestamp of the last update.
    activated_at: Optional[datetime] = None  # Timestamp of first activation.
    suspended_at: Optional[datetime] = None  # Timestamp of last suspension.


class TenantListResponseSchema(Schema):
    """
    Defines the response structure for a paginated list of tenants.
    Used in the admin endpoint for listing all tenants.
    """

    items: list[TenantResponseSchema]  # The list of tenants on the current page.
    total: int  # The total number of tenants matching the query.
    page: int  # The current page number.
    page_size: int  # The number of items per page.
    pages: int  # The total number of pages.


class TenantSettingsSchema(Schema):
    """
    Defines the comprehensive structure for a tenant's extended settings.
    This schema represents the full set of customizable settings for a tenant.
    """

    # Branding settings
    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#6366f1"
    secondary_color: str = "#8b5cf6"

    # Voice feature defaults
    default_voice_id: str = "af_heart"
    default_stt_model: str = "tiny"
    default_stt_language: str = "en"
    stt_vad_enabled: bool = True
    stt_beam_size: int = 5
    default_tts_model: str = "kokoro"
    default_llm_provider: str = "groq"
    default_llm_model: str = "llama-3.3-70b-versatile"
    default_llm_temperature: float = 0.7
    default_llm_max_tokens: int = 1024

    # Notification settings
    webhook_url: str = ""
    email_notifications: bool = True
    slack_webhook_url: str = ""

    # Security policies
    require_mfa: bool = False
    session_timeout_minutes: int = 1440  # Default: 24 hours
    allowed_ip_ranges: list[str] = Field(default_factory=list)
    api_key_expiry_days: int = 365  # Default: 1 year


class TenantSettingsUpdateSchema(Schema):
    """
    Defines the request payload for updating tenant settings.
    All fields are optional to allow for partial updates.
    """

    # Branding
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None

    # Voice Defaults
    default_voice_id: Optional[str] = None
    default_stt_model: Optional[str] = None
    default_stt_language: Optional[str] = None
    stt_vad_enabled: Optional[bool] = None
    stt_beam_size: Optional[int] = None
    default_tts_model: Optional[str] = None
    default_llm_provider: Optional[str] = None
    default_llm_model: Optional[str] = None
    default_llm_temperature: Optional[float] = None
    default_llm_max_tokens: Optional[int] = None

    # Notifications
    webhook_url: Optional[str] = None
    email_notifications: Optional[bool] = None
    slack_webhook_url: Optional[str] = None

    # Security
    require_mfa: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    allowed_ip_ranges: Optional[list[str]] = None
    api_key_expiry_days: Optional[int] = None

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        """Ensures that color fields are valid hex color codes."""
        if v is not None and not v.startswith("#"):
            raise ValueError("Color must be a hex value starting with #")
        return v


class TenantUpgradeTierSchema(Schema):
    """
    Defines the request payload for upgrading or downgrading a tenant's tier.
    """

    tier: str  # The target tier to move the tenant to.

    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        """Ensures the provided tier is one of the valid choices."""
        from .models import Tenant

        if v not in Tenant.Tier.values:
            raise ValueError(f"Invalid tier. Must be one of: {Tenant.Tier.values}")
        return v


class TenantSuspendSchema(Schema):
    """
    Defines the request payload for suspending a tenant.
    """

    reason: str = Field(
        default="", max_length=500, description="An optional reason for the suspension."
    )
