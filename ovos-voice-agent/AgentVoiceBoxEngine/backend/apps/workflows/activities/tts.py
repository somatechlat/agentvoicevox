"""
TTS workflow activities.

Real synthesis via Kokoro ONNX (same engine as run_tts_worker).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass

from django.conf import settings
from temporalio import activity


@dataclass
class SynthesisRequest:
    """Text-to-speech request."""

    tenant_id: str
    session_id: str
    text: str
    voice_id: str = "af_heart"
    language: str = "en-us"
    speed: float = 1.0
    output_format: str = "wav"


@dataclass
class SynthesisResult:
    """Text-to-speech result."""

    audio_data: bytes
    audio_format: str
    duration_seconds: float


class TTSActivities:
    """Activities for speech synthesis."""

    @activity.defn
    async def synthesize_speech(self, request: SynthesisRequest) -> SynthesisResult:
        if not request.text.strip():
            raise ValueError("Text is required for speech synthesis")

        import io
        import wave

        import numpy as np

        from apps.workflows.management.commands.run_tts_worker import KokoroTTS

        engine = KokoroTTS()
        engine.load(
            settings.TTS_WORKER["MODEL_DIR"],
            settings.TTS_WORKER["MODEL_FILE"],
            settings.TTS_WORKER["VOICES_FILE"],
        )
        samples, sample_rate = await asyncio.to_thread(
            engine.synthesize,
            request.text.strip(),
            request.voice_id or settings.TTS_WORKER.get("DEFAULT_VOICE", "af_heart"),
            float(request.speed or 1.0),
            request.language or "en-us",
        )
        if samples.size == 0:
            raise RuntimeError("TTS produced empty audio")

        pcm = (np.clip(samples.astype(np.float32), -1.0, 1.0) * 32767.0).astype("<i2")
        output_format = (request.output_format or "wav").lower()
        if output_format != "wav":
            raise ValueError(f"Unsupported TTS output_format: {request.output_format}")

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(int(sample_rate))
            wav.writeframes(pcm.tobytes())
        return SynthesisResult(
            audio_data=buf.getvalue(),
            audio_format="wav",
            duration_seconds=float(pcm.size) / float(sample_rate),
        )
