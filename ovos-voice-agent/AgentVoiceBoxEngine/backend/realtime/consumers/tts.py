"""
TTS (Text-to-Speech) streaming WebSocket consumer.
"""

import logging
from typing import Any

from .base import BaseConsumer

logger = logging.getLogger(__name__)


class TTSConsumer(BaseConsumer):
    """
    TTS streaming consumer.

    Handles real-time text-to-speech synthesis.
    """

    async def connect(self):
        """Handle connection."""
        await super().connect()

        if self.authenticated:
            # Send available voices
            await self.send_event(
                "tts.ready",
                {
                    "voices": [
                        {"id": "af_heart", "name": "Heart", "language": "en"},
                        {"id": "af_bella", "name": "Bella", "language": "en"},
                        {"id": "af_nicole", "name": "Nicole", "language": "en"},
                        {"id": "am_adam", "name": "Adam", "language": "en"},
                        {"id": "am_michael", "name": "Michael", "language": "en"},
                    ],
                    "formats": ["pcm16", "mp3", "opus"],
                },
            )

    async def handle_synthesize(self, content: dict[str, Any]):
        """Enqueue text synthesis for the Kokoro TTS worker."""
        import time
        import uuid

        from django.conf import settings

        from apps.workflows.redis_client import RedisClient

        text = content.get("text", "")
        voice_id = content.get("voice_id", "af_heart")
        speed = content.get("speed", 1.0)
        session_id = str(content.get("session_id") or getattr(self, "session_id", "") or "")
        response_id = str(content.get("response_id") or f"resp_{uuid.uuid4().hex[:12]}")

        if not text:
            await self.send_error("invalid_request", "Text is required")
            return

        await self.send_event(
            "tts.started",
            {"text": text, "voice_id": voice_id, "response_id": response_id},
        )

        try:
            redis = RedisClient()
            await redis.connect()
            await redis.client.xadd(
                settings.TTS_WORKER["STREAM_REQUESTS"],
                {
                    "session_id": session_id,
                    "text": str(text),
                    "voice": str(voice_id),
                    "speed": str(speed),
                    "response_id": response_id,
                    "correlation_id": str(content.get("correlation_id") or uuid.uuid4().hex),
                    "language": str(content.get("language") or content.get("lang") or "en-us"),
                    "timestamp": str(time.time()),
                },
            )
            await redis.disconnect()
        except Exception as exc:
            logger.error("Failed to enqueue TTS request: %s", exc)
            await self.send_error("server_error", "Could not queue synthesis")

    async def handle_cancel(self, content: dict[str, Any]):
        """Handle synthesis cancellation."""
        await self.send_event("tts.cancelled", {})

    async def handle_config(self, content: dict[str, Any]):
        """Handle TTS configuration update."""
        voice_id = content.get("voice_id", "af_heart")
        speed = content.get("speed", 1.0)
        format = content.get("format", "pcm16")

        await self.send_event(
            "tts.configured",
            {
                "voice_id": voice_id,
                "speed": speed,
                "format": format,
            },
        )

    # Group message handlers
    async def audio_chunk(self, event: dict[str, Any]):
        """Handle audio chunk from TTS worker."""
        await self.send_event("tts.audio", event["data"])

    async def synthesis_completed(self, event: dict[str, Any]):
        """Handle synthesis completion."""
        await self.send_event("tts.completed", event["data"])
