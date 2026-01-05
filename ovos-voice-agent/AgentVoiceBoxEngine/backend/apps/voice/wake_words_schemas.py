"""Schemas for wake word endpoints."""

from datetime import datetime
from uuid import UUID

from ninja import Schema


class WakeWordOut(Schema):
    """Schema for representing a wake word."""

    id: UUID
    phrase: str
    sensitivity: float
    is_enabled: bool
    detection_count: int
    false_positive_count: int
    missed_activation_count: int
    created_at: datetime
    last_detected_at: datetime | None = None


class WakeWordCreate(Schema):
    """Schema for creating a new wake word."""

    phrase: str
    sensitivity: float = 0.5


class WakeWordUpdate(Schema):
    """Schema for updating an existing wake word."""

    phrase: str | None = None
    sensitivity: float | None = None
    is_enabled: bool | None = None


class WakeWordAnalyticsOut(Schema):
    """Schema for wake word analytics."""

    total_detections: int
    false_positive_rate: float
    missed_activation_rate: float
    avg_confidence: float
