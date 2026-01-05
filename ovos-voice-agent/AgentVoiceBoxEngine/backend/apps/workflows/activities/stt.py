"""
Speech-to-Text (STT) Workflow Activities
========================================

This module defines a set of Temporal Workflow Activities specifically designed
for Speech-to-Text (STT) processing within voice processing pipelines. These
activities leverage the `faster_whisper` library for efficient audio
transcription and language detection, and include utilities for audio validation.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionRequest:
    """
    Defines the parameters for requesting an audio transcription.

    Attributes:
        tenant_id (str): The ID of the tenant initiating the request.
        session_id (str): A unique identifier for the current session or interaction.
        audio_data (bytes): The raw audio data to be transcribed.
        audio_format (str): The format of the audio data (e.g., 'wav', 'mp3').
        language (Optional[str]): The language of the audio (e.g., 'en', 'es'). If None, language is auto-detected.
        model (str): The `faster_whisper` model size to use for transcription (e.g., 'tiny', 'base', 'small').
    """

    tenant_id: str
    session_id: str
    audio_data: bytes
    audio_format: str = "wav"
    language: Optional[str] = None
    model: str = "tiny"


@dataclass
class TranscriptionResult:
    """
    Represents the structured result of an audio transcription.

    Attributes:
        text (str): The full transcribed text.
        language (str): The detected or specified language of the audio.
        confidence (float): A confidence score for the transcription (e.g., language probability).
        segments (list[dict[str, Any]]): A list of dictionaries, each representing a transcribed segment.
        duration_seconds (float): The duration of the transcribed audio in seconds.
        processing_time_ms (float): The time taken for transcription in milliseconds.
    """

    text: str
    language: str
    confidence: float
    segments: list[dict[str, Any]]
    duration_seconds: float
    processing_time_ms: float


@dataclass
class TranscriptionSegment:
    """
    Represents a single segment of transcribed audio with timing and confidence.

    Attributes:
        start (float): Start time of the segment in seconds.
        end (float): End time of the segment in seconds.
        text (str): The transcribed text for this segment.
        confidence (float): Confidence score for this segment's transcription.
    """

    start: float
    end: float
    text: str
    confidence: float


class STTActivities:
    """
    A collection of Temporal Workflow Activities for Speech-to-Text (STT) operations.

    These activities are designed to be executed within a Temporal workflow,
    providing robust and fault-tolerant audio processing capabilities.
    """

    @activity.defn(name="stt_transcribe_audio")
    async def transcribe_audio(
        self,
        request: TranscriptionRequest,
    ) -> TranscriptionResult:
        """
        Transcribes audio data into text using the `faster_whisper` library.

        This activity handles saving the audio data to a temporary file,
        performing the transcription, and cleaning up the temporary file.

        Args:
            request: A `TranscriptionRequest` object containing audio data and
                     transcription parameters.

        Returns:
            A `TranscriptionResult` object with the transcribed text, language,
            segments, and performance metrics.

        Raises:
            Exception: If the transcription process fails.
        """
        start_time = time.time()  # Record start time for latency calculation.

        # Local import to avoid loading the model at module level and for dynamic model loading.
        import os
        import tempfile
        import time
        from faster_whisper import WhisperModel

        try:
            # Initialize Whisper model.
            # `device="cpu"` uses the CPU, `compute_type="int8"` uses 8-bit integer quantization
            # for faster inference on CPUs. For GPU, `device="cuda"` would be used.
            model = WhisperModel(
                request.model,
                device="cpu",
                compute_type="int8",
            )

            # Save audio to a temporary file for `faster_whisper` processing.
            with tempfile.NamedTemporaryFile(
                suffix=f".{request.audio_format}",
                delete=False,  # Keep file until explicitly unlinked.
            ) as f:
                f.write(request.audio_data)
                temp_path = f.name

            try:
                # Perform the transcription.
                segments, info = model.transcribe(
                    temp_path,
                    language=request.language,
                    beam_size=5,  # Parameter for beam search decoding.
                    vad_filter=True,  # Enable Voice Activity Detection filtering.
                )

                # Collect and format transcription segments.
                result_segments = []
                full_text = []
                for segment in segments:
                    result_segments.append(
                        {
                            "start": segment.start,
                            "end": segment.end,
                            "text": segment.text.strip(),
                            "confidence": segment.avg_logprob,
                        }
                    )
                    full_text.append(segment.text.strip())

                processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds.

                logger.info(
                    f"Transcribed audio for session {request.session_id}: "
                    f"{len(result_segments)} segments, {info.duration:.2f}s audio, {processing_time:.0f}ms"
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
                # Ensure the temporary file is deleted.
                os.unlink(temp_path)

        except Exception as e:
            logger.error(f"STT transcription failed for session {request.session_id}: {e}")
            raise  # Re-raise the exception for Temporal to handle.

    @activity.defn(name="stt_detect_language")
    async def detect_language(
        self,
        tenant_id: str,
        audio_data: bytes,
        audio_format: str = "wav",
    ) -> dict[str, Any]:
        """
        Detects the dominant language in an audio sample using `faster_whisper`.

        This is typically used for multilingual applications where the audio
        language is not known beforehand. It transcribes a short segment of
        audio (first 30 seconds) to infer the language.

        Args:
            tenant_id: The ID of the tenant.
            audio_data: The raw audio data.
            audio_format: The format of the audio data.

        Returns:
            A dictionary containing the detected `language` code and a `confidence` score.

        Raises:
            Exception: If language detection fails.
        """
        import os
        import tempfile
        from faster_whisper import WhisperModel  # Local import.

        try:
            model = WhisperModel("tiny", device="cpu", compute_type="int8")

            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_format}",
                delete=False,
            ) as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                # Transcribe with language=None to enable auto-detection.
                # Only a short audio segment is needed for reliable language detection.
                segments, info = model.transcribe(
                    temp_path,
                    language=None,
                    beam_size=1,  # Lower beam size for faster detection.
                )

                return {
                    "language": info.language,
                    "confidence": info.language_probability,
                }

            finally:
                os.unlink(temp_path)

        except Exception as e:
            logger.error(f"STT language detection failed for tenant {tenant_id}: {e}")
            raise

    @activity.defn(name="stt_validate_audio")
    async def validate_audio(
        self,
        audio_data: bytes,
        audio_format: str,
        min_duration_seconds: float = 0.1,
        max_duration_seconds: float = 300.0,
    ) -> dict[str, Any]:
        """
        Validates the format and basic properties (like duration) of audio data.

        For WAV files, it performs more detailed checks. For other formats, it
        currently performs a size check.

        Args:
            audio_data: The raw audio data bytes.
            audio_format: The format of the audio (e.g., 'wav', 'mp3').
            min_duration_seconds: The minimum allowed duration for the audio.
            max_duration_seconds: The maximum allowed duration for the audio.

        Returns:
            A dictionary indicating `valid` status and any `error` message.
            For WAV files, it also returns `channels`, `sample_width`, `framerate`, `duration_seconds`.
            For other formats, `size_bytes` and `format`.

        Raises:
            Exception: If audio validation encounters an unexpected error.
        """
        try:
            import io
            import wave  # Python's built-in WAV file reader.

            if audio_format.lower() == "wav":
                with io.BytesIO(audio_data) as audio_io:
                    try:
                        with wave.open(audio_io, "rb") as wav:
                            channels = wav.getnchannels()
                            sample_width = wav.getsampwidth()
                            framerate = wav.getframerate()
                            frames = wav.getnframes()
                            duration = frames / framerate

                            if duration < min_duration_seconds:
                                return {
                                    "valid": False,
                                    "error": f"Audio too short: {duration:.2f}s (min {min_duration_seconds}s)",
                                }
                            if duration > max_duration_seconds:
                                return {
                                    "valid": False,
                                    "error": f"Audio too long: {duration:.2f}s (max {max_duration_seconds}s)",
                                }

                            return {
                                "valid": True,
                                "channels": channels,
                                "sample_width": sample_width,
                                "framerate": framerate,
                                "duration_seconds": duration,
                            }
                    except wave.Error as e:
                        # Handle specific WAV file errors.
                        return {"valid": False, "error": f"Invalid WAV file: {e}"}
            else:
                # For non-WAV formats, perform a basic size check as full parsing might be complex.
                size_mb = len(audio_data) / (1024 * 1024)
                # Hardcoded limit for general audio files, could be configurable.
                if size_mb > 50:
                    return {
                        "valid": False,
                        "error": f"Audio file too large: {size_mb:.2f}MB (max 50MB)",
                    }

                return {
                    "valid": True,
                    "size_bytes": len(audio_data),
                    "format": audio_format,
                }

        except Exception as e:
            logger.error(f"STT audio validation failed: {e}")
            return {
                "valid": False,
                "error": str(e),
            }
