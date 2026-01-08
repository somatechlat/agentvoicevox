"""
Wake Word API Endpoints
=======================

This module provides the REST API endpoints for managing and monitoring wake words.
All operations are tenant-scoped, allowing users to manage their own set of
wake words and view their performance analytics.
"""

from uuid import UUID

from django.db.models import Sum
from ninja import Router
from ninja.files import UploadedFile

from apps.core.exceptions import (
    FeatureNotImplementedError,
    NotFoundError,
    ValidationError,
)

from .models import WakeWord
from .wake_words_schemas import (
    WakeWordAnalyticsOut,
    WakeWordCreate,
    WakeWordOut,
    WakeWordUpdate,
)

# Router for wake word endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Wake Words"])


def _wake_word_out(wake_word: WakeWord) -> WakeWordOut:
    """
    Serializes a WakeWord Django model instance into a WakeWordOut schema.

    Args:
        wake_word: The WakeWord model instance.

    Returns:
        A WakeWordOut object populated with the wake word's data.
    """
    return WakeWordOut(
        id=wake_word.id,
        phrase=wake_word.phrase,
        sensitivity=wake_word.sensitivity,
        is_enabled=wake_word.is_enabled,
        detection_count=wake_word.detection_count,
        false_positive_count=wake_word.false_positive_count,
        missed_activation_count=wake_word.missed_activation_count,
        created_at=wake_word.created_at,
        last_detected_at=wake_word.last_detected_at,
    )


@router.get("", response=list[WakeWordOut], summary="List Wake Words")
def list_wake_words(request):
    """
    Lists all wake word configurations for the current tenant.

    This operation is tenant-scoped.

    Returns:
        A list of wake word objects, ordered by creation date.
    """
    wake_words = WakeWord.objects.filter(tenant=request.tenant).order_by("-created_at")
    return [_wake_word_out(w) for w in wake_words]


@router.post("", response=WakeWordOut, summary="Create a Wake Word")
def create_wake_word(request, payload: WakeWordCreate):
    """
    Creates a new wake word configuration for the current tenant.

    This operation is tenant-scoped.

    Args:
        payload: A WakeWordCreate object with the wake word's phrase and sensitivity.

    Returns:
        The newly created wake word object.

    Raises:
        ValidationError: If the wake word phrase is empty.
    """
    if not payload.phrase.strip():
        raise ValidationError("Wake word phrase is required")

    wake_word = WakeWord.objects.create(
        tenant=request.tenant,
        phrase=payload.phrase.strip(),
        sensitivity=payload.sensitivity,
    )
    return _wake_word_out(wake_word)


@router.patch("/{wake_word_id}", response=WakeWordOut, summary="Update a Wake Word")
def update_wake_word(request, wake_word_id: UUID, payload: WakeWordUpdate):
    """
    Updates an existing wake word configuration.

    This operation is tenant-scoped and allows for partial updates.

    Args:
        wake_word_id: The UUID of the wake word to update.
        payload: A WakeWordUpdate object with the fields to modify.

    Returns:
        The updated wake word object.

    Raises:
        NotFoundError: If the wake word is not found or does not belong to the tenant.
    """
    try:
        wake_word = WakeWord.objects.get(id=wake_word_id, tenant=request.tenant)
    except (WakeWord.DoesNotExist, ValueError):
        raise NotFoundError("Wake word not found")

    updates = payload.dict(exclude_unset=True)
    for key, value in updates.items():
        setattr(wake_word, key, value)
    wake_word.save()
    return _wake_word_out(wake_word)


@router.delete("/{wake_word_id}", response={204: None}, summary="Delete a Wake Word")
def delete_wake_word(request, wake_word_id: UUID):
    """
    Deletes a wake word configuration.

    This operation is tenant-scoped and permanent.

    Args:
        wake_word_id: The UUID of the wake word to delete.

    Returns:
        A 204 No Content response on successful deletion.
    """
    try:
        wake_word = WakeWord.objects.get(id=wake_word_id, tenant=request.tenant)
    except (WakeWord.DoesNotExist, ValueError):
        raise NotFoundError("Wake word not found")

    wake_word.delete()
    return 204, None


@router.post("/{wake_word_id}/test", summary="Test a Wake Word (Not Implemented)")
def test_wake_word(request, wake_word_id: UUID, audio: UploadedFile):
    """
    Tests a wake word against a provided audio file.

    NOTE: This feature is not yet implemented. This endpoint serves as a
    placeholder for future functionality.

    Args:
        wake_word_id: The UUID of the wake word to test.
        audio: The uploaded audio file to test against.

    Raises:
        ValidationError: If the audio file is missing.
        FeatureNotImplementedError: Always, as this feature is not available.
    """
    if audio is None:
        raise ValidationError("Audio file is required")
    raise FeatureNotImplementedError("Wake word detection pipeline not configured")


@router.get(
    "/analytics", response=WakeWordAnalyticsOut, summary="Get Wake Word Analytics"
)
def wake_word_analytics(request):
    """
    Retrieves aggregated analytics for all wake words for the current tenant.

    This operation is tenant-scoped.

    Returns:
        An analytics object containing total detections and performance rates.
    """
    qs = WakeWord.objects.filter(tenant=request.tenant)

    # Aggregate statistics from all wake words for the tenant.
    total_detections = int(qs.aggregate(total=Sum("detection_count")).get("total") or 0)
    total_false = int(qs.aggregate(total=Sum("false_positive_count")).get("total") or 0)
    total_missed = int(
        qs.aggregate(total=Sum("missed_activation_count")).get("total") or 0
    )

    # Calculate rates, avoiding division by zero.
    false_rate = (total_false / total_detections) if total_detections else 0.0
    missed_rate = (total_missed / total_detections) if total_detections else 0.0

    return WakeWordAnalyticsOut(
        total_detections=total_detections,
        false_positive_rate=false_rate,
        missed_activation_rate=missed_rate,
        avg_confidence=0.0,  # NOTE: Confidence metric is not yet implemented.
    )
