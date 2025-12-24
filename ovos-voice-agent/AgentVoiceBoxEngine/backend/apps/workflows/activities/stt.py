"""
Speech-to-Text (STT) activities for Temporal workflows.

Handles audio transcription via Faster-Whisper or external STT services.
"""
import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionRequest:
    """Request for audio transcription."""

    tenant_id: str
    session_id: str
    audio_data: bytes
    audio_format: str = "wav"
    language: Optional[str] = None
    model: str = "tiny"


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""

    text: str
    language: str
    confidence: float
    segments: List[Dict[str, Any]]
    duration_seconds: float
    processing_time_ms: float


@dataclass
class TranscriptionSegment:
    """A segment of transcribed audio."""

    start: float
    end: float
    text: str
    confidence: float


class STTActivities:
    """
    Speech-to-Text activities for voice processing workflows.

    Activities:
    - transcribe_audio: Transcribe audio chunk to text
    - detect_language: Detect language from audio
    - validate_audio: Validate audio format and quality
    """

    @activity.defn(name="stt_transcribe_audio")
    async def transcribe_audio(
        self,
        request: TranscriptionRequest,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text using Faster-Whisper.

        Args:
            request: TranscriptionRequest with audio data and config

        Returns:
            TranscriptionResult with transcribed text and metadata

        Raises:
            Exception: If transcription fails
        """
        import time

        start_time = time.time()

        try:
            # Import here to avoid loading model at module level
            from faster_whisper import WhisperModel

            # Get model based on request (cached in production)
            model = WhisperModel(
                request.model,
                device="cpu",
                compute_type="int8",
            )

            # Save audio to temp file for processing
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                suffix=f".{request.audio_format}",
                delete=False,
            ) as f:
                f.write(request.audio_data)
                temp_path = f.name

            try:
                # Transcribe
                segments, info = model.transcribe(
                    temp_path,
                    language=request.language,
                    beam_size=5,
                    vad_filter=True,
                )

                # Collect segments
                result_segments = []
                full_text = []

                for segment in segments:
                    result_segments.append({
                        "start": segment.start,
                        "end": segment.end,
                        "text": segment.text.strip(),
                        "confidence": segment.avg_logprob,
                    })
                    full_text.append(segment.text.strip())

                processing_time = (time.time() - start_time) * 1000

                logger.info(
                    f"Transcribed audio for session {request.session_id}: "
                    f"{len(result_segments)} segments, {info.duration:.2f}s audio"
                )

                return TranscriptionResult(
                    text=" ".join(full_text),
                    language=info.language,
                    confidence=info.language_probability,
                    segments=result_segments,
                    duration_seconds=info.duration,
                    processing_time_ms=processing_time,
                )

            finally:
                # Clean up temp file
                os.unlink(temp_path)

        except Exception as e:
            logger.error(
                f"STT transcription failed for session {request.session_id}: {e}"
            )
            raise

    @activity.defn(name="stt_detect_language")
    async def detect_language(
        self,
        tenant_id: str,
        audio_data: bytes,
        audio_format: str = "wav",
    ) -> Dict[str, Any]:
        """
        Detect language from audio sample.

        Args:
            tenant_id: Tenant identifier
            audio_data: Audio bytes
            audio_format: Audio format (wav, mp3, etc.)

        Returns:
            Dict with detected language and confidence
        """
        try:
            from faster_whisper import WhisperModel

            model = WhisperModel("tiny", device="cpu", compute_type="int8")

            import tempfile
            import os

            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}",
                delete=False,
            ) as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                # Detect language only (first 30 seconds)
                _, info = model.transcribe(
                    temp_path,
                    language=None,  # Auto-detect
                    beam_size=1,
                )

                return {
                    "language": info.language,
                    "confidence": info.language_probability,
                }

            finally:
                os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            raise

    @activity.defn(name="stt_validate_audio")
    async def validate_audio(
        self,
        audio_data: bytes,
        audio_format: str,
        min_duration_seconds: float = 0.1,
        max_duration_seconds: float = 300.0,
    ) -> Dict[str, Any]:
        """
        Validate audio format and quality.

        Args:
            audio_data: Audio bytes
            audio_format: Expected audio format
            min_duration_seconds: Minimum audio duration
            max_duration_seconds: Maximum audio duration

        Returns:
            Dict with validation result and audio info
        """
        try:
            import io
            import wave

            if audio_format.lower() == "wav":
                with io.BytesIO(audio_data) as audio_io:
                    with wave.open(audio_io, "rb") as wav:
                        channels = wav.getnchannels()
                        sample_width = wav.getsampwidth()
                        framerate = wav.getframerate()
                        frames = wav.getnframes()
                        duration = frames / framerate

                        if duration < min_duration_seconds:
                            return {
                                "valid": False,
                                "error": f"Audio too short: {duration:.2f}s",
                            }

                        if duration > max_duration_seconds:
                            return {
                                "valid": False,
                                "error": f"Audio too long: {duration:.2f}s",
                            }

                        return {
                            "valid": True,
                            "channels": channels,
                            "sample_width": sample_width,
                            "framerate": framerate,
                            "duration_seconds": duration,
                        }
            else:
                # For other formats, just check size
                size_mb = len(audio_data) / (1024 * 1024)
                if size_mb > 50:
                    return {
                        "valid": False,
                        "error": f"Audio file too large: {size_mb:.2f}MB",
                    }

                return {
                    "valid": True,
                    "size_bytes": len(audio_data),
                    "format": audio_format,
                }

        except Exception as e:
            logger.error(f"Audio validation failed: {e}")
            return {
                "valid": False,
                "error": str(e),
            }
