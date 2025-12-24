"""
Pydantic schemas for API Key endpoints.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from ninja import Schema


class APIKeyCreate(Schema):
    """Schema for creating an API key."""
    name: str
    description: str = ""
    project_id: Optional[UUID] = None
    scopes: List[str] = ["realtime"]
    rate_limit_tier: str = "standard"
    expires_in_days: Optional[int] = None


class APIKeyUpdate(Schema):
    """Schema for updating an API key."""
    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[List[str]] = None
    rate_limit_tier: Optional[str] = None


class APIKeyResponse(Schema):
    """Schema for API key response (without full key)."""
    id: UUID
    tenant_id: UUID
    name: str
    description: str
    key_prefix: str
    project_id: Optional[UUID] = None
    scopes: List[str]
    rate_limit_tier: str
    is_active: bool
    is_expired: bool
    is_revoked: bool
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int
    created_by_id: Optional[UUID] = None
    created_at: datetime

    @staticmethod
    def from_orm(key) -> "APIKeyResponse":
        return APIKeyResponse(
            id=key.id,
            tenant_id=key.tenant_id,
            name=key.name,
            description=key.description,
            key_prefix=key.key_prefix,
            project_id=key.project_id,
            scopes=key.scopes,
            rate_limit_tier=key.rate_limit_tier,
            is_active=key.is_active,
            is_expired=key.is_expired,
            is_revoked=key.is_revoked,
            expires_at=key.expires_at,
            revoked_at=key.revoked_at,
            last_used_at=key.last_used_at,
            usage_count=key.usage_count,
            created_by_id=key.created_by_id,
            created_at=key.created_at,
        )


class APIKeyCreateResponse(Schema):
    """Schema for API key creation response (includes full key)."""
    id: UUID
    tenant_id: UUID
    name: str
    description: str
    key: str  # Full key - only returned once!
    key_prefix: str
    project_id: Optional[UUID] = None
    scopes: List[str]
    rate_limit_tier: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    @staticmethod
    def from_orm(key, full_key: str) -> "APIKeyCreateResponse":
        return APIKeyCreateResponse(
            id=key.id,
            tenant_id=key.tenant_id,
            name=key.name,
            description=key.description,
            key=full_key,
            key_prefix=key.key_prefix,
            project_id=key.project_id,
            scopes=key.scopes,
            rate_limit_tier=key.rate_limit_tier,
            expires_at=key.expires_at,
            created_at=key.created_at,
        )


class APIKeyListResponse(Schema):
    """Schema for paginated API key list."""
    items: List[APIKeyResponse]
    total: int
    page: int
    page_size: int
    pages: int


class APIKeyRotateRequest(Schema):
    """Schema for rotating an API key."""
    grace_period_hours: int = 0


class APIKeyRotateResponse(Schema):
    """Schema for API key rotation response."""
    new_key: APIKeyCreateResponse
    old_key_expires_at: Optional[datetime] = None


class APIKeyRevokeRequest(Schema):
    """Schema for revoking an API key."""
    reason: str = ""


class APIKeyValidateResponse(Schema):
    """Schema for API key validation response."""
    valid: bool
    key_id: Optional[UUID] = None
    tenant_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    scopes: List[str] = []
    rate_limit_tier: Optional[str] = None
    error: Optional[str] = None
