"""
Text-to-Speech (TTS) Workflow Activities
========================================

This module defines a set of Temporal Workflow Activities specifically designed
for Text-to-Speech (TTS) processing within voice processing pipelines. These
activities handle the conversion of text into spoken audio, primarily using
the `kokoro` TTS engine, and include utilities for managing available voices
and validating input text.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from temporalio import activity

logger = logging.getLogger(__name__)


@dataclass
class SynthesisRequest:
    """
    Defines the parameters for requesting text-to-speech synthesis.

    Attributes:
        tenant_id (str): The ID of the tenant initiating the request.
        session_id (str): A unique identifier for the current session or interaction.
        text (str): The text content to be synthesized into speech.
        voice_id (str): The identifier of the TTS voice to use (e.g., 'af_heart').
        language (str): The language code for synthesis (e.g., 'en-us').
        speed (float): The speech speed multiplier (1.0 is normal).
        output_format (str): The desired audio output format (e.g., 'wav').
    """

    tenant_id: str
    session_id: str
    text: str
    voice_id: str = "af_heart"
    language: str = "en-us"
    speed: float = 1.0
    output_format: str = "wav"


@dataclass
class SynthesisResult:
    """
    Represents the structured result of text-to-speech synthesis.

    Attributes:
        audio_data (bytes): The raw audio data of the synthesized speech.
        audio_format (str): The format of the returned audio data.
        duration_seconds (float): The duration of the synthesized audio in seconds.
        sample_rate (int): The sample rate of the audio.
        processing_time_ms (float): The time taken for synthesis in milliseconds.
        character_count (int): The number of characters in the original text.
    """

    audio_data: bytes
    audio_format: str
    duration_seconds: float
    sample_rate: int
    processing_time_ms: float
    character_count: int


@dataclass
class VoiceInfo:
    """
    Provides descriptive information about an available TTS voice.

    Attributes:
        voice_id (str): The unique identifier for the voice.
        name (str): A human-readable name for the voice.
        language (str): The language code of the voice.
        gender (str): The perceived gender of the voice.
        description (str): A brief description of the voice's characteristics.
    """

    voice_id: str
    name: str
    language: str
    gender: str
    description: str


class TTSActivities:
    """
    A collection of Temporal Workflow Activities for Text-to-Speech (TTS) operations.

    These activities are designed to be executed within a Temporal workflow,
    providing robust and fault-tolerant audio generation capabilities.
    """

    @activity.defn(name="tts_synthesize_speech")
    async def synthesize_speech(
        self,
        request: SynthesisRequest,
    ) -> SynthesisResult:
        """
        Synthesizes speech from text using the Kokoro TTS engine.

        This activity converts input text into audio bytes, handling the
        interaction with the Kokoro engine and necessary audio processing
        (e.g., combining segments, converting to WAV format).

        Args:
            request: A `SynthesisRequest` object containing text and synthesis parameters.

        Returns:
            A `SynthesisResult` object with the synthesized audio data and metadata.

        Raises:
            Exception: If the speech synthesis process fails.
        """
        import io
        import time
        import wave  # Python's built-in WAV file writer.

        import numpy as np  # Used for efficient audio array manipulation.

        start_time = time.time()  # Record start time for latency calculation.

        try:
            # Local import of Kokoro TTS to avoid module-level dependency.
            from kokoro import KPipeline

            # Initialize Kokoro pipeline for the specified language.
            lang_code = request.language.split("-")[
                0
            ]  # Extract base language from locale (e.g., "en" from "en-us").
            pipeline = KPipeline(lang_code=lang_code)

            audio_segments = []
            # Iterate through generated audio segments from Kokoro.
            for _, _, audio_np_array in pipeline(
                request.text,
                voice=request.voice_id,
                speed=request.speed,
            ):
                audio_segments.append(audio_np_array)

            # Combine all audio segments into a single NumPy array.
            if audio_segments:
                combined_audio_float = np.concatenate(audio_segments)
            else:
                combined_audio_float = np.array([], dtype=np.float32)

            # Convert the float audio data to 16-bit WAV bytes.
            sample_rate = 24000  # Kokoro's default sample rate.
            audio_bytes_buffer = io.BytesIO()

            with wave.open(audio_bytes_buffer, "wb") as wav_file:
                wav_file.setnchannels(1)  # Mono audio.
                wav_file.setsampwidth(2)  # 16-bit audio.
                wav_file.setframerate(sample_rate)

                # Scale float32 audio to int16 range (-32768 to 32767).
                audio_int16 = (combined_audio_float * 32767).astype(np.int16)
                wav_file.writeframes(audio_int16.tobytes())

            audio_data = audio_bytes_buffer.getvalue()
            duration = len(combined_audio_float) / sample_rate
            processing_time = (
                time.time() - start_time
            ) * 1000  # Convert to milliseconds.

            logger.info(
                f"Synthesized speech for session {request.session_id}: "
                f"{len(request.text)} chars, {duration:.2f}s audio, {processing_time:.0f}ms"
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
            logger.warning(
                "Kokoro TTS library not available, returning empty audio for session %s.",
                request.session_id,
            )
            return SynthesisResult(
                audio_data=b"",
                audio_format=request.output_format,
                duration_seconds=0.0,
                sample_rate=24000,
                processing_time_ms=0.0,
                character_count=len(request.text),
            )

        except Exception as e:
            logger.error(f"TTS synthesis failed for session {request.session_id}: {e}")
            raise

    @activity.defn(name="tts_list_voices")
    async def list_voices(
        self,
        language: Optional[str] = None,
    ) -> list[VoiceInfo]:
        """
        Retrieves a list of available TTS voices.

        Currently, this activity provides a hardcoded list of sample voices
        from the Kokoro TTS engine. It supports optional filtering by language.

        Args:
            language: (Optional) A language code (e.g., 'en-us') to filter available voices.

        Returns:
            A list of `VoiceInfo` objects, describing each available voice.
        """
        # Hardcoded list of sample Kokoro voices. In a production system, this
        # would typically be fetched dynamically from the TTS provider's API.
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
            # Filter by the base language code (e.g., 'en' from 'en-us').
            lang_prefix = language.lower().split("-")[0]
            voices = [v for v in voices if v.language.lower().startswith(lang_prefix)]

        return voices

    @activity.defn(name="tts_validate_text")
    async def validate_text(
        self,
        text: str,
        max_length: int = 5000,
    ) -> dict[str, Any]:
        """
        Validates input text for suitability for TTS synthesis.

        Checks for empty text, excessive length, and presence of unsupported
        control characters. Provides an estimated duration for the synthesized speech.

        Args:
            text: The text string to validate.
            max_length: The maximum allowed character length for the text.

        Returns:
            A dictionary indicating `valid` status, any `error` message,
            and estimated metrics (`character_count`, `word_count`, `estimated_duration_seconds`).
        """
        if not text or not text.strip():
            return {
                "valid": False,
                "error": "Text is empty or contains only whitespace.",
            }

        if len(text) > max_length:
            return {
                "valid": False,
                "error": f"Text too long: {len(text)} chars (max {max_length}).",
            }

        # Check for unsupported control characters that might interfere with TTS engines.
        import unicodedata  # Local import.

        control_chars = [
            c for c in text if unicodedata.category(c) == "Cc" and c not in "\n\r\t"
        ]
        if control_chars:
            return {
                "valid": False,
                "error": f"Text contains {len(control_chars)} unsupported control characters.",
            }

        # Provide a very rough estimate for speech duration.
        # This is a heuristic; actual duration depends on voice, speed, and content.
        return {
            "valid": True,
            "character_count": len(text),
            "word_count": len(text.split()),
            "estimated_duration_seconds": len(text)
            / 15,  # Heuristic: approx. 15 chars per second.
        }
