"""
STT (Speech-to-Text) streaming WebSocket consumer.
"""
import logging
from typing import Any, Dict

from .base import BaseConsumer

logger = logging.getLogger(__name__)


class STTConsumer(BaseConsumer):
    """
    STT streaming consumer.

    Handles real-time speech-to-text transcription.
    """

    async def connect(self):
        """Handle connection."""
        await super().connect()

        if self.authenticated:
            await self.send_event("stt.ready", {
                "models": ["tiny", "base", "small"],
                "languages": ["en", "es", "fr", "de", "it", "pt", "nl", "pl", "ru", "zh", "ja", "ko"],
            })

    async def handle_audio_chunk(self, content: Dict[str, Any]):
        """Handle incoming audio chunk for transcription."""
        audio_data = content.get("audio")
        is_final = content.get("is_final", False)

        if not audio_data:
            return

        # Process audio chunk
        # In production, this would forward to Temporal STT workflow
        await self.send_event("transcription.partial", {
            "text": "",
            "is_final": is_final,
        })

    async def handle_config(self, content: Dict[str, Any]):
        """Handle STT configuration update."""
        model = content.get("model", "tiny")
        language = content.get("language", "en")

        await self.send_event("stt.configured", {
            "model": model,
            "language": language,
        })

    # Group message handlers
    async def transcription_partial(self, event: Dict[str, Any]):
        """Handle partial transcription result."""
        await self.send_event("transcription.partial", event["data"])

    async def transcription_final(self, event: Dict[str, Any]):
        """Handle final transcription result."""
        await self.send_event("transcription.final", event["data"])
