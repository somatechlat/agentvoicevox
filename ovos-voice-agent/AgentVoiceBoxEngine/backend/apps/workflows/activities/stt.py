"""
STT workflow activities.

Real transcription via faster-whisper when the STT worker model is available
in-process, or by validating and enqueueing work for the STT worker stream.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

from django.conf import settings
from temporalio import activity


@dataclass
class TranscriptionRequest:
    """Speech-to-text request."""

    tenant_id: str
    session_id: str
    audio_data: bytes
    audio_format: str = "pcm16"
    language: Optional[str] = None
    model: str = "tiny"


@dataclass
class TranscriptionResult:
    """Speech-to-text result."""

    text: str
    language: str
    duration_seconds: float
    confidence: float = 0.0


class STTActivities:
    """Activities for speech-to-text work."""

    @activity.defn
    async def transcribe_audio(self, request: TranscriptionRequest) -> TranscriptionResult:
        if not request.audio_data:
            raise ValueError("Audio data is required for transcription")

        import numpy as np

        from apps.workflows.management.commands.run_stt_worker import (
            FasterWhisperTranscriber,
            pcm16_bytes_to_float32,
        )

        fmt = (request.audio_format or "pcm16").lower()
        if fmt not in {"pcm16", "raw", "s16le"}:
            raise ValueError(
                f"Unsupported audio_format for direct STT activity: {request.audio_format}"
            )

        waveform = pcm16_bytes_to_float32(request.audio_data)
        sample_rate = int(settings.STT_WORKER.get("SAMPLE_RATE", 16000))
        model_name = request.model or settings.STT_WORKER.get("MODEL", "tiny")

        transcriber = FasterWhisperTranscriber()
        transcriber.load(
            model_name,
            settings.STT_WORKER.get("DEVICE", "auto"),
            settings.STT_WORKER.get("COMPUTE_TYPE", "int8"),
        )
        text, language, duration = await asyncio.to_thread(
            transcriber.transcribe,
            np.asarray(waveform, dtype=np.float32),
            sample_rate,
            request.language,
        )
        return TranscriptionResult(
            text=text,
            language=language,
            duration_seconds=duration,
        )
