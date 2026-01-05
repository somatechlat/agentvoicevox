"""Schemas for voice cloning endpoints."""

from datetime import datetime
from uuid import UUID

from ninja import Schema


class CustomVoiceOut(Schema):
    """Schema for representing a custom voice."""

    id: UUID
    name: str
    language: str
    quality: str
    status: str
    created_at: datetime
    sample_duration_seconds: float
    is_default: bool
    error_message: str | None = None


class CustomVoiceCreateOut(Schema):
    """Schema for the output of a custom voice creation request."""

    id: UUID
    name: str
    language: str
    quality: str
    status: str
    created_at: datetime
    sample_duration_seconds: float
    is_default: bool
