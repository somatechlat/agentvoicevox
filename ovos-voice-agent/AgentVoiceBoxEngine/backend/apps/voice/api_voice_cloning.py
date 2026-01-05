"""
Voice Cloning API Endpoints
=============================

This module provides the REST API endpoints for managing custom-cloned voices.
All operations are tenant-scoped to ensure that users can only access and
manage their own custom voices.
"""

from django.db import transaction
from ninja import Router
from ninja.files import UploadedFile

from apps.core.exceptions import FeatureNotImplementedError, NotFoundError, ValidationError

from .models import CustomVoice
from .voice_cloning_schemas import CustomVoiceCreateOut, CustomVoiceOut

# Router for voice cloning endpoints, tagged for OpenAPI documentation.
router = Router(tags=["Voice Cloning"])


def _custom_voice_out(voice: CustomVoice) -> CustomVoiceOut:
    """
    Serializes a CustomVoice Django model instance into a CustomVoiceOut schema.

    Args:
        voice: The CustomVoice model instance.

    Returns:
        A CustomVoiceOut object populated with the custom voice's data.
    """
    return CustomVoiceOut(
        id=voice.id,
        name=voice.name,
        language=voice.language,
        quality=voice.quality,
        status=voice.status,
        created_at=voice.created_at,
        sample_duration_seconds=voice.sample_duration_seconds,
        is_default=voice.is_default,
        error_message=voice.error_message or None,
    )


@router.get("/voices", response=list[CustomVoiceOut], summary="List Custom Voices")
def list_custom_voices(request):
    """
    Lists all custom voices created by the current tenant.

    This operation is tenant-scoped.

    Returns:
        A list of custom voice objects.
    """
    voices = CustomVoice.objects.filter(tenant=request.tenant).order_by("-created_at")
    return [_custom_voice_out(v) for v in voices]


@router.post("/voices", response=CustomVoiceCreateOut, summary="Create a Custom Voice")
def create_custom_voice(
    request,
    audio: UploadedFile,
    name: str,
    language: str = "en",
    quality: str = "balanced",
):
    """
    Creates a new custom voice by uploading an audio sample.

    This endpoint initiates the voice cloning process. The actual cloning happens
    asynchronously. The initial status of the voice will be 'processing'.
    This operation is tenant-scoped.

    Args:
        audio: The uploaded audio file (e.g., .wav, .mp3) for voice cloning.
        name: A human-readable name for the new voice.
        language: The language code of the audio sample.
        quality: The requested training quality.

    Returns:
        A 201 status and an object representing the newly created custom voice job.

    Raises:
        ValidationError: If the audio file or voice name is missing.
    """
    if audio is None:
        raise ValidationError("Audio file is required")
    if not name.strip():
        raise ValidationError("Voice name is required")

    # The creation of the model instance triggers the async cloning process.
    voice = CustomVoice.objects.create(
        tenant=request.tenant,
        name=name.strip(),
        language=language,
        quality=quality,
        status=CustomVoice.Status.PROCESSING,
        sample_audio=audio,
        sample_duration_seconds=0,  # This would be updated by the async worker.
    )

    return CustomVoiceCreateOut(
        id=voice.id,
        name=voice.name,
        language=voice.language,
        quality=voice.quality,
        status=voice.status,
        created_at=voice.created_at,
        sample_duration_seconds=voice.sample_duration_seconds,
        is_default=voice.is_default,
    )


@router.get("/voices/{voice_id}", response=CustomVoiceOut, summary="Get a Custom Voice")
def get_custom_voice(request, voice_id: str):
    """
    Retrieves a specific custom voice by its ID.

    This operation is tenant-scoped.

    Args:
        voice_id: The UUID of the custom voice to retrieve.

    Returns:
        The requested custom voice object.

    Raises:
        NotFoundError: If the voice does not exist or does not belong to the tenant.
    """
    try:
        voice = CustomVoice.objects.get(id=voice_id, tenant=request.tenant)
    except (CustomVoice.DoesNotExist, ValueError):
        raise NotFoundError("Custom voice not found")
    return _custom_voice_out(voice)


@router.delete("/voices/{voice_id}", response={204: None}, summary="Delete a Custom Voice")
def delete_custom_voice(request, voice_id: str):
    """
    Deletes a custom voice.

    This operation is tenant-scoped and permanently removes the custom voice
    and its associated audio file.

    Args:
        voice_id: The UUID of the custom voice to delete.

    Returns:
        A 204 No Content response on successful deletion.
    """
    try:
        voice = CustomVoice.objects.get(id=voice_id, tenant=request.tenant)
    except (CustomVoice.DoesNotExist, ValueError):
        raise NotFoundError("Custom voice not found")
    voice.delete()
    return 204, None


@router.post("/voices/{voice_id}/default", response=CustomVoiceOut, summary="Set Custom Voice as Default")
@transaction.atomic
def set_default_custom_voice(request, voice_id: str):
    """
    Sets a specific custom voice as the default for the current tenant.

    This operation is tenant-scoped and transactional. It ensures that only one
    custom voice can be the default at any given time for a tenant.

    Args:
        voice_id: The UUID of the custom voice to set as default.

    Returns:
        The updated custom voice object, with `is_default` set to True.
    """
    try:
        voice = CustomVoice.objects.get(id=voice_id, tenant=request.tenant)
    except (CustomVoice.DoesNotExist, ValueError):
        raise NotFoundError("Custom voice not found")

    # Atomically unset other defaults and set the new one.
    CustomVoice.objects.filter(tenant=request.tenant, is_default=True).update(is_default=False)
    voice.is_default = True
    voice.save(update_fields=["is_default", "updated_at"])
    return _custom_voice_out(voice)


@router.get("/voices/{voice_id}/preview", summary="Preview a Custom Voice (Not Implemented)")
def preview_custom_voice(request, voice_id: str, text: str = ""):
    """
    Generates a preview of a custom voice with the given text.

    NOTE: This feature is not yet implemented. This endpoint serves as a
    placeholder for future functionality.

    Args:
        voice_id: The UUID of the custom voice.
        text: The text to be synthesized into speech.

    Raises:
        FeatureNotImplementedError: Always, as this feature is not available.
    """
    raise FeatureNotImplementedError("Voice cloning preview not configured")
