"""
Speech-to-Text (STT) Configuration and Testing API Endpoints
============================================================

This module provides API endpoints for managing Speech-to-Text (STT) configurations
and for testing STT provider integrations. These endpoints allow tenants to set up
their preferred STT models and languages, and to get insights into STT usage metrics.
"""


from django.db.models import Sum
from django.utils import timezone
from ninja import Router
from ninja.files import UploadedFile

from apps.billing.models import UsageEvent
from apps.core.exceptions import ValidationError
from apps.tenants.services import TenantSettingsService
from apps.workflows.activities.stt import STTActivities, TranscriptionRequest

from .schemas import STTConfigOut, STTConfigUpdate, STTMetricsOut, STTTestOut

# Router for STT configuration and testing endpoints.
router = Router(tags=["STT Integrations"])


@router.get("/config", response=STTConfigOut, summary="Get STT Configuration")
def get_stt_config(request):
    """
    Retrieves the current Speech-to-Text (STT) configuration for the authenticated tenant.

    This includes settings like the STT model, language, VAD (Voice Activity Detection)
    status, and beam size.

    **Permissions:** Assumed to require ADMIN or DEVELOPER role (explicit check missing).
    """
    # TODO: Implement explicit permission check (e.g., if not request.user.is_admin: raise PermissionDeniedError)
    settings = TenantSettingsService.get_settings(request.tenant.id)
    return STTConfigOut(
        model=settings.default_stt_model,
        language=settings.default_stt_language,
        vad_enabled=settings.stt_vad_enabled,
        beam_size=settings.stt_beam_size,
    )


@router.patch("/config", response=STTConfigOut, summary="Update STT Configuration")
def update_stt_config(request, payload: STTConfigUpdate):
    """
    Updates the Speech-to-Text (STT) configuration for the authenticated tenant.

    This endpoint handles updates to various STT settings stored in `TenantSettings`.

    **Permissions:** Assumed to require ADMIN or DEVELOPER role (explicit check missing).
    """
    # TODO: Implement explicit permission check (e.g., if not request.user.is_admin: raise PermissionDeniedError)
    settings = TenantSettingsService.update_voice_defaults(
        tenant_id=request.tenant.id,
        default_stt_model=payload.model,
        default_stt_language=payload.language,
        stt_vad_enabled=payload.vad_enabled,
        stt_beam_size=payload.beam_size,
    )

    return STTConfigOut(
        model=settings.default_stt_model,
        language=settings.default_stt_language,
        vad_enabled=settings.stt_vad_enabled,
        beam_size=settings.stt_beam_size,
    )


@router.get("/metrics", response=STTMetricsOut, summary="Get STT Usage Metrics")
def get_stt_metrics(request):
    """
    Retrieves aggregated Speech-to-Text (STT) usage metrics for the current tenant.

    Currently, this endpoint calculates the total STT minutes for the current day
    from `UsageEvent`s. Latency and accuracy are placeholders.

    **Permissions:** Assumed to require OPERATOR role or higher (explicit check missing).
    """
    # TODO: Implement explicit permission check (e.g., if not request.user.is_operator: raise PermissionDeniedError)
    start_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    total_minutes = (
        UsageEvent.all_objects.filter(
            tenant=request.tenant,
            event_type=UsageEvent.EventType.STT_MINUTES,
            created_at__gte=start_day,
        ).aggregate(total=Sum("quantity"))["total"]
        or 0
    )

    return STTMetricsOut(
        avg_latency_ms=0.0,  # Placeholder for average latency.
        total_minutes=float(total_minutes),
        accuracy_estimate=0.0,  # Placeholder for accuracy estimate (e.g., Word Error Rate).
    )


@router.post("/test", response=STTTestOut, summary="Test STT Transcription")
async def test_stt(request, audio: UploadedFile):
    """
    Tests the current STT configuration for the authenticated tenant by transcribing
    an uploaded audio file.

    **Permissions:** Assumed to require DEVELOPER role or higher (explicit check missing).
    """
    # TODO: Implement explicit permission check (e.g., if not request.user.is_developer: raise PermissionDeniedError)
    if audio is None:
        raise ValidationError("Audio file is required.")

    audio_bytes = audio.read()
    if not audio_bytes:
        raise ValidationError("Audio file is empty.")

    settings = TenantSettingsService.get_settings(request.tenant.id)

    # Determine audio format from file extension.
    ext = "wav"  # Default to WAV.
    if audio.name and "." in audio.name:
        ext = audio.name.rsplit(".", 1)[1].lower()

    # Construct the TranscriptionRequest payload for the workflow activity.
    result = await STTActivities().transcribe_audio(
        TranscriptionRequest(
            tenant_id=str(request.tenant.id),
            session_id="stt-test",  # A special session ID for testing purposes.
            audio_data=audio_bytes,
            audio_format=ext,
            # Use tenant's default language, or None if set to 'auto' for model to detect.
            language=(
                settings.default_stt_language
                if settings.default_stt_language != "auto"
                else None
            ),
            model=settings.default_stt_model,
        )
    )

    return STTTestOut(transcription=result.text)
