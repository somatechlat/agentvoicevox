"""
Pydantic schemas for Tenant API.

Used by Django Ninja for request/response validation.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from ninja import Schema
from pydantic import Field, field_validator


class TenantCreateSchema(Schema):
    """Schema for creating a new tenant."""
    
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    tier: str = Field(default="free")
    settings: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        valid_tiers = {"free", "starter", "pro", "enterprise"}
        if v not in valid_tiers:
            raise ValueError(f"Invalid tier. Must be one of: {valid_tiers}")
        return v


class TenantUpdateSchema(Schema):
    """Schema for updating a tenant."""
    
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    settings: Optional[Dict[str, Any]] = None


class TenantResponseSchema(Schema):
    """Schema for tenant response."""
    
    id: UUID
    name: str
    slug: str
    tier: str
    status: str
    billing_id: str
    settings: Dict[str, Any]
    max_users: int
    max_projects: int
    max_api_keys: int
    max_sessions_per_month: int
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime] = None
    suspended_at: Optional[datetime] = None


class TenantListResponseSchema(Schema):
    """Schema for tenant list response."""
    
    items: List[TenantResponseSchema]
    total: int
    page: int
    page_size: int
    pages: int


class TenantSettingsSchema(Schema):
    """Schema for tenant settings."""
    
    logo_url: str = ""
    favicon_url: str = ""
    primary_color: str = "#6366f1"
    secondary_color: str = "#8b5cf6"
    default_voice_id: str = "af_heart"
    default_stt_model: str = "tiny"
    default_tts_model: str = "kokoro"
    default_llm_provider: str = "groq"
    default_llm_model: str = "llama-3.3-70b-versatile"
    webhook_url: str = ""
    email_notifications: bool = True
    slack_webhook_url: str = ""
    require_mfa: bool = False
    session_timeout_minutes: int = 1440
    allowed_ip_ranges: List[str] = Field(default_factory=list)
    api_key_expiry_days: int = 365


class TenantSettingsUpdateSchema(Schema):
    """Schema for updating tenant settings."""
    
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    default_voice_id: Optional[str] = None
    default_stt_model: Optional[str] = None
    default_tts_model: Optional[str] = None
    default_llm_provider: Optional[str] = None
    default_llm_model: Optional[str] = None
    webhook_url: Optional[str] = None
    email_notifications: Optional[bool] = None
    slack_webhook_url: Optional[str] = None
    require_mfa: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    allowed_ip_ranges: Optional[List[str]] = None
    api_key_expiry_days: Optional[int] = None
    
    @field_validator("primary_color", "secondary_color")
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.startswith("#"):
            raise ValueError("Color must be a hex value starting with #")
        return v


class TenantUpgradeTierSchema(Schema):
    """Schema for upgrading tenant tier."""
    
    tier: str
    
    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        valid_tiers = {"free", "starter", "pro", "enterprise"}
        if v not in valid_tiers:
            raise ValueError(f"Invalid tier. Must be one of: {valid_tiers}")
        return v


class TenantSuspendSchema(Schema):
    """Schema for suspending a tenant."""
    
    reason: str = Field(default="", max_length=500)
