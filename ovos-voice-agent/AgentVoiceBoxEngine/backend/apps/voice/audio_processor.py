"""
Audio Processing Utility for AgentVoiceBox.
Handles transcoding between various audio formats (PCM16, G.711 u-law/a-law)
and prepares audio for STT/TTS workers.
"""

import base64
import io

import numpy as np
import soundfile as sf
from pydub import AudioSegment


class AudioProcessor:
    """Utility class for audio transcoding and normalization."""

    @staticmethod
    def to_pcm16(audio_data: bytes, source_format: str, sample_rate: int = 16000) -> bytes:
        """
        Converts incoming audio data to raw PCM16 bytes at the target sample rate.
        
        Args:
            audio_data: Raw audio bytes or base64 encoded string.
            source_format: 'pcm16', 'g711_ulaw', or 'g711_alaw'.
            sample_rate: Target sample rate (default 16kHz for STT).
            
        Returns:
            Raw PCM16 bytes.
        """
        # Handle base64 if needed
        try:
            if isinstance(audio_data, str):
                audio_data = base64.b64decode(audio_data)
        except Exception:
            pass

        if source_format == "pcm16":
            # Already PCM16, but we might need to resample or ensure headerless
            audio = AudioSegment.from_raw(
                io.BytesIO(audio_data),
                sample_width=2,
                frame_rate=sample_rate,
                channels=1
            )
        elif source_format == "g711_ulaw":
            audio = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format="mulaw",
                frame_rate=8000,  # G.711 is usually 8kHz
                channels=1
            )
            # Resample to target rate
            audio = audio.set_frame_rate(sample_rate)
        elif source_format == "g711_alaw":
            audio = AudioSegment.from_file(
                io.BytesIO(audio_data),
                format="alaw",
                frame_rate=8000,
                channels=1
            )
            # Resample to target rate
            audio = audio.set_frame_rate(sample_rate)
        else:
            raise ValueError(f"Unsupported audio format: {source_format}")

        return audio.raw_data

    @staticmethod
    def from_pcm16(pcm_data: bytes, target_format: str, sample_rate: int = 16000) -> bytes:
        """
        Converts raw PCM16 bytes to the target format.
        
        Args:
            pcm_data: Raw PCM16 bytes.
            target_format: 'pcm16', 'g711_ulaw', or 'g711_alaw'.
            sample_rate: Source sample rate.
            
        Returns:
            Encoded audio bytes.
        """
        audio = AudioSegment.from_raw(
            io.BytesIO(pcm_data),
            sample_width=2,
            frame_rate=sample_rate,
            channels=1
        )

        output = io.BytesIO()
        if target_format == "pcm16":
            return audio.raw_data
        elif target_format == "g711_ulaw":
            audio.export(output, format="mulaw")
        elif target_format == "g711_alaw":
            audio.export(output, format="alaw")
        else:
            raise ValueError(f"Unsupported target format: {target_format}")

        return output.getvalue()

    @staticmethod
    def extract_features(audio_data: bytes, sample_rate: int = 16000) -> dict:
        """Extracts basic features like RMS power (utility for visualizers/VAD)."""
        audio_io = io.BytesIO(audio_data)
        data, _ = sf.read(audio_io)

        if len(data) == 0:
            return {"rms": 0.0, "peak": 0.0}

        rms = np.sqrt(np.mean(data**2))
        peak = np.max(np.abs(data))

        return {
            "rms": float(rms),
            "peak": float(peak)
        }
