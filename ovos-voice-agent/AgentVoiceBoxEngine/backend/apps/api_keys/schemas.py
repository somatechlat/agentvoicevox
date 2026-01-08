"""
Pydantic Schemas for API Key Management
========================================

This module defines the Pydantic schemas for data validation and serialization
in the API Key API endpoints. These schemas govern how API keys are created,
updated, listed, and validated, ensuring data consistency and clear communication
with API clients. Special attention is given to the secure handling of the full
API key, which is only exposed during creation.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from ninja import Schema


class APIKeyCreate(Schema):
    """
    Defines the request payload for creating a new API key.
    """

    name: str  # A human-readable name for the API key.
    description: str = ""  # An optional description of the API key's purpose.
    project_id: Optional[UUID] = (
        None  # (Optional) Associate the key with a specific project.
    )
    scopes: list[str] = [
        "realtime"
    ]  # A list of scopes for the API key (e.g., 'realtime', 'billing').
    rate_limit_tier: str = (
        "standard"  # The rate limit tier for the key (e.g., 'standard', 'elevated').
    )
    expires_in_days: Optional[int] = (
        None  # (Optional) Number of days until the key expires.
    )


class APIKeyUpdate(Schema):
    """
    Defines the request payload for updating an existing API key.
    All fields are optional to allow for partial updates (PATCH).
    """

    name: Optional[str] = None
    description: Optional[str] = None
    scopes: Optional[list[str]] = None
    rate_limit_tier: Optional[str] = None


class APIKeyResponse(Schema):
    """
    Defines the standard response structure for a single API key object.

    This schema explicitly **excludes the full plaintext key** for security reasons.
    It includes derived properties like `is_active`, `is_expired`, `is_revoked`.
    """

    id: UUID  # The unique identifier for the API key.
    tenant_id: UUID  # The ID of the tenant that owns this API key.
    name: str
    description: str
    key_prefix: str  # The first few characters of the full key for identification.
    project_id: Optional[UUID] = None  # The ID of the associated project, if any.
    scopes: list[str]  # The scopes granted to this API key.
    rate_limit_tier: str  # The rate limit tier applied to this key.
    is_active: bool  # True if the key is not revoked and not expired.
    is_expired: bool  # True if the key has passed its expiration date.
    is_revoked: bool  # True if the key has been explicitly revoked.
    expires_at: Optional[datetime] = (
        None  # The date and time after which the key becomes invalid.
    )
    revoked_at: Optional[datetime] = None  # The date and time this key was revoked.
    last_used_at: Optional[datetime] = (
        None  # Timestamp of the last successful API call.
    )
    usage_count: int  # Total number of API calls made using this key.
    created_by_id: Optional[UUID] = None  # The ID of the user who created the key.
    created_at: datetime  # Timestamp of when the key was created.

    @staticmethod
    def from_orm(key) -> "APIKeyResponse":
        """
        Creates an `APIKeyResponse` instance from a Django `APIKey` model instance.

        Args:
            key: The Django `APIKey` model instance.

        Returns:
            An instance of `APIKeyResponse`.
        """
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
    """
    Defines the response structure when an API key is successfully created.

    This is the **only time the full plaintext `key` is returned** to the client.
    Clients are responsible for securely storing this value.
    """

    id: UUID
    tenant_id: UUID
    name: str
    description: str
    key: str  # The full, plaintext API key string. **CRITICAL: Store securely.**
    key_prefix: str
    project_id: Optional[UUID] = None
    scopes: list[str]
    rate_limit_tier: str
    expires_at: Optional[datetime] = None
    created_at: datetime

    @staticmethod
    def from_orm(key, full_key: str) -> "APIKeyCreateResponse":
        """
        Creates an `APIKeyCreateResponse` instance from a Django `APIKey` model
        and the full plaintext key.

        Args:
            key: The Django `APIKey` model instance.
            full_key: The full plaintext API key string.

        Returns:
            An instance of `APIKeyCreateResponse`.
        """
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
    """
    Defines the response structure for a paginated list of API keys.
    """

    items: list[APIKeyResponse]  # The list of API keys on the current page.
    total: int  # The total number of API keys matching the query.
    page: int  # The current page number.
    page_size: int  # The number of items per page.
    pages: int  # The total number of pages.


class APIKeyRotateRequest(Schema):
    """
    Defines the request payload for rotating an API key.
    """

    grace_period_hours: int = (
        0  # Number of hours to keep the old key active (default: 0, immediate revocation).
    )


class APIKeyRotateResponse(Schema):
    """
    Defines the response structure for an API key rotation operation.
    """

    new_key: APIKeyCreateResponse  # Details of the newly generated API key.
    old_key_expires_at: Optional[datetime] = (
        None  # If a grace period was applied, the expiration of the old key.
    )


class APIKeyRevokeRequest(Schema):
    """
    Defines the request payload for revoking an API key.
    """

    reason: str = ""  # An optional reason for revoking the key.


class APIKeyValidateResponse(Schema):
    """
    Defines the response structure for the API key validation endpoint.
    """

    valid: bool  # True if the API key is valid, false otherwise.
    key_id: Optional[UUID] = None  # The ID of the validated API key.
    tenant_id: Optional[UUID] = None  # The ID of the tenant the key belongs to.
    project_id: Optional[UUID] = None  # The ID of the project the key is scoped to.
    scopes: list[str] = []  # The scopes granted to the key.
    rate_limit_tier: Optional[str] = None  # The rate limit tier of the key.
    error: Optional[str] = None  # A human-readable error message if validation fails.
