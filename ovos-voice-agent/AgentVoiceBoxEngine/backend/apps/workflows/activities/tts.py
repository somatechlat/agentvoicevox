"""
Text-to-Speech (TTS) activities for Temporal workflows.

Handles audio synthesis via Kokoro or external TTS services.
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class SynthesisRequest:
    """Request for text-to-speech synthesis."""

    tenant_id: str
    session_id: str
    text: str
    voice_id: str = "af_heart"
    language: str = "en-us"
    speed: float = 1.0
    output_format: str = "wav"


@dataclass
class SynthesisResult:
    """Result of text-to-speech synthesis."""

    audio_data: bytes
    audio_format: str
    duration_seconds: float
    sample_rate: int
    processing_time_ms: float
    character_count: int


@dataclass
class VoiceInfo:
    """Information about an available voice."""

    voice_id: str
    name: str
    language: str
    gender: str
    description: str


class TTSActivities:
    """
    Text-to-Speech activities for voice processing workflows.

    Activities:
    - synthesize_speech: Convert text to audio
    - list_voices: Get available voices
    - validate_text: Validate text for synthesis
    """

    @activity.defn(name="tts_synthesize_speech")
    async def synthesize_speech(
        self,
        request: SynthesisRequest,
    ) -> SynthesisResult:
        """
        Synthesize speech from text using Kokoro TTS.

        Args:
            request: SynthesisRequest with text and voice config

        Returns:
            SynthesisResult with audio data and metadata

        Raises:
            Exception: If synthesis fails
        """
        import time

        start_time = time.time()

        try:
            # Import Kokoro TTS
            from kokoro import KPipeline

            # Initialize pipeline for the language
            lang_code = request.language.split("-")[0]  # e.g., "en" from "en-us"
            pipeline = KPipeline(lang_code=lang_code)

            # Generate audio
            audio_segments = []
            total_duration = 0.0

            for _, _, audio in pipeline(
                request.text,
                voice=request.voice_id,
                speed=request.speed,
            ):
                audio_segments.append(audio)

            # Combine audio segments
            import numpy as np

            if audio_segments:
                combined_audio = np.concatenate(audio_segments)
            else:
                combined_audio = np.array([], dtype=np.float32)

            # Convert to WAV bytes
            import io
            import wave

            sample_rate = 24000  # Kokoro default
            audio_bytes = io.BytesIO()

            with wave.open(audio_bytes, "wb") as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(sample_rate)

                # Convert float32 to int16
                audio_int16 = (combined_audio * 32767).astype(np.int16)
                wav.writeframes(audio_int16.tobytes())

            audio_data = audio_bytes.getvalue()
            duration = len(combined_audio) / sample_rate
            processing_time = (time.time() - start_time) * 1000

            logger.info(
                f"Synthesized speech for session {request.session_id}: "
                f"{len(request.text)} chars, {duration:.2f}s audio"
            )

            return SynthesisResult(
                audio_data=audio_data,
                audio_format=request.output_format,
                duration_seconds=duration,
                sample_rate=sample_rate,
                processing_time_ms=processing_time,
                character_count=len(request.text),
            )

        except ImportError:
            # Fallback if Kokoro not available - return empty audio
            logger.warning("Kokoro TTS not available, returning empty audio")
            return SynthesisResult(
                audio_data=b"",
                audio_format=request.output_format,
                duration_seconds=0.0,
                sample_rate=24000,
                processing_time_ms=0.0,
                character_count=len(request.text),
            )

        except Exception as e:
            logger.error(
                f"TTS synthesis failed for session {request.session_id}: {e}"
            )
            raise

    @activity.defn(name="tts_list_voices")
    async def list_voices(
        self,
        language: Optional[str] = None,
    ) -> List[VoiceInfo]:
        """
        List available TTS voices.

        Args:
            language: Optional language filter

        Returns:
            List of available VoiceInfo
        """
        # Kokoro available voices
        voices = [
            VoiceInfo(
                voice_id="af_heart",
                name="Heart",
                language="en-us",
                gender="female",
                description="Warm, friendly American female voice",
            ),
            VoiceInfo(
                voice_id="af_bella",
                name="Bella",
                language="en-us",
                gender="female",
                description="Clear, professional American female voice",
            ),
            VoiceInfo(
                voice_id="af_nicole",
                name="Nicole",
                language="en-us",
                gender="female",
                description="Soft, calm American female voice",
            ),
            VoiceInfo(
                voice_id="af_sarah",
                name="Sarah",
                language="en-us",
                gender="female",
                description="Energetic American female voice",
            ),
            VoiceInfo(
                voice_id="am_adam",
                name="Adam",
                language="en-us",
                gender="male",
                description="Deep, authoritative American male voice",
            ),
            VoiceInfo(
                voice_id="am_michael",
                name="Michael",
                language="en-us",
                gender="male",
                description="Friendly American male voice",
            ),
            VoiceInfo(
                voice_id="bf_emma",
                name="Emma",
                language="en-gb",
                gender="female",
                description="Clear British female voice",
            ),
            VoiceInfo(
                voice_id="bm_george",
                name="George",
                language="en-gb",
                gender="male",
                description="Professional British male voice",
            ),
        ]

        if language:
            lang_prefix = language.lower().replace("-", "")[:2]
            voices = [v for v in voices if v.language.startswith(lang_prefix)]

        return voices

    @activity.defn(name="tts_validate_text")
    async def validate_text(
        self,
        text: str,
        max_length: int = 5000,
    ) -> Dict[str, Any]:
        """
        Validate text for TTS synthesis.

        Args:
            text: Text to validate
            max_length: Maximum allowed text length

        Returns:
            Dict with validation result
        """
        if not text or not text.strip():
            return {
                "valid": False,
                "error": "Text is empty",
            }

        if len(text) > max_length:
            return {
                "valid": False,
                "error": f"Text too long: {len(text)} chars (max {max_length})",
            }

        # Check for unsupported characters
        # Most TTS systems handle Unicode well, but check for control chars
        import unicodedata

        control_chars = [c for c in text if unicodedata.category(c) == "Cc" and c not in "\n\r\t"]
        if control_chars:
            return {
                "valid": False,
                "error": f"Text contains {len(control_chars)} control characters",
            }

        return {
            "valid": True,
            "character_count": len(text),
            "word_count": len(text.split()),
            "estimated_duration_seconds": len(text) / 15,  # ~15 chars/second
        }
