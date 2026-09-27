"""
STT (Speech-to-Text) streaming WebSocket consumer.
"""

import logging
from typing import Any

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
            await self.send_event(
                "stt.ready",
                {
                    "models": ["tiny", "base", "small"],
                    "languages": [
                        "en",
                        "es",
                        "fr",
                        "de",
                        "it",
                        "pt",
                        "nl",
                        "pl",
                        "ru",
                        "zh",
                        "ja",
                        "ko",
                    ],
                },
            )

    async def handle_audio_chunk(self, content: dict[str, Any]):
        """Enqueue audio for the STT worker (faster-whisper)."""
        audio_data = content.get("audio")
        is_final = bool(content.get("is_final", False))

        if not audio_data:
            return

        import time
        import uuid

        from django.conf import settings

        from apps.workflows.redis_client import RedisClient

        try:
            redis = RedisClient()
            await redis.connect()
            await redis.client.xadd(
                settings.STT_WORKER["STREAM_AUDIO"],
                {
                    "session_id": str(content.get("session_id") or self.scope.get("session_id") or ""),
                    "tenant_id": str(getattr(self, "tenant_id", "") or ""),
                    "correlation_id": str(content.get("correlation_id") or uuid.uuid4().hex),
                    "audio": str(audio_data),
                    "audio_format": str(content.get("audio_format") or "pcm16"),
                    "language": str(content.get("language") or ""),
                    "is_final": "1" if is_final else "0",
                    "timestamp": str(time.time()),
                },
            )
            await redis.disconnect()
            await self.send_event(
                "transcription.queued",
                {"is_final": is_final},
            )
        except Exception as exc:
            logger.error("Failed to enqueue STT audio: %s", exc)
            await self.send_event(
                "error",
                {"code": "stt_enqueue_failed", "message": "Could not queue audio"},
            )

    async def handle_config(self, content: dict[str, Any]):
        """Handle STT configuration update."""
        model = content.get("model", "tiny")
        language = content.get("language", "en")

        await self.send_event(
            "stt.configured",
            {
                "model": model,
                "language": language,
            },
        )

    # Group message handlers
    async def transcription_partial(self, event: dict[str, Any]):
        """Handle partial transcription result."""
        await self.send_event("transcription.partial", event["data"])

    async def transcription_final(self, event: dict[str, Any]):
        """Handle final transcription result."""
        await self.send_event("transcription.final", event["data"])
