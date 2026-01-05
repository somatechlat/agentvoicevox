"""
Voice session WebSocket consumer.

Handles real-time voice communication for sessions.
"""

import logging
from typing import Any, Optional

from .base import BaseConsumer

logger = logging.getLogger(__name__)


class SessionConsumer(BaseConsumer):
    """
    Voice session consumer.

    Handles:
    - Audio streaming (input/output)
    - Transcription results
    - LLM responses
    - Session events
    """

    def __init__(self, *args, **kwargs):
        """Initializes the SessionConsumer."""
        super().__init__(*args, **kwargs)
        self.session_id: Optional[str] = None
        self.session = None

    async def connect(self):
        """Handle connection and validate session."""
        # Get session ID from URL
        self.session_id = self.scope["url_route"]["kwargs"].get("session_id")

        if not self.session_id:
            await self.close(code=4004)
            return

        await super().connect()

        if self.authenticated:
            # Validate session belongs to tenant
            if not await self._validate_session():
                await self.close(code=4004)
                return

            # Join session group
            await self.channel_layer.group_add(
                f"session_{self.session_id}",
                self.channel_name,
            )

            # Mark session as active
            await self._activate_session()

            # Send session info
            await self.send_event(
                "session.connected",
                {
                    "session_id": self.session_id,
                    "config": self.session.config if self.session else {},
                },
            )

    async def disconnect(self, close_code):
        """Handle disconnection."""
        if self.session_id:
            await self.channel_layer.group_discard(
                f"session_{self.session_id}",
                self.channel_name,
            )

            # Complete session if normal close
            if close_code == self.CLOSE_NORMAL:
                await self._complete_session()

        await super().disconnect(close_code)

    async def _validate_session(self) -> bool:
        """Validate session exists and belongs to tenant."""
        from apps.sessions.models import Session

        try:
            self.session = await Session.objects.filter(
                id=self.session_id,
                tenant_id=self.tenant_id,
            ).afirst()

            return self.session is not None

        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return False

    async def _activate_session(self):
        """Mark session as active."""
        if self.session:
            from django.utils import timezone

            self.session.status = "active"
            self.session.started_at = timezone.now()
            await self.session.asave(update_fields=["status", "started_at", "updated_at"])

    async def _complete_session(self):
        """Mark session as completed."""
        if self.session:
            from django.utils import timezone

            self.session.status = "completed"
            self.session.terminated_at = timezone.now()
            if self.session.started_at:
                self.session.duration_seconds = (
                    self.session.terminated_at - self.session.started_at
                ).total_seconds()
            await self.session.asave(
                update_fields=["status", "terminated_at", "duration_seconds", "updated_at"]
            )

    # Message handlers
    async def handle_audio_input(self, content: dict[str, Any]):
        """Handle incoming audio chunk."""
        audio_data = content.get("audio")
        if not audio_data:
            return

        # Forward to STT processing via Temporal workflow
        # This would trigger the STT workflow
        await self.channel_layer.group_send(
            f"stt_worker_{self.tenant_id}",
            {
                "type": "process_audio",
                "session_id": self.session_id,
                "audio": audio_data,
            },
        )

    async def handle_response_create(self, content: dict[str, Any]):
        """Handle request to generate response."""
        # Trigger LLM response generation
        await self.send_event(
            "response.started",
            {
                "session_id": self.session_id,
            },
        )

    async def handle_response_cancel(self, content: dict[str, Any]):
        """Handle response cancellation."""
        await self.send_event(
            "response.cancelled",
            {
                "session_id": self.session_id,
            },
        )

    async def handle_session_update(self, content: dict[str, Any]):
        """Handle session configuration update."""
        config = content.get("config", {})

        if self.session:
            self.session.config.update(config)
            await self.session.asave(update_fields=["config", "updated_at"])

        await self.send_event(
            "session.updated",
            {
                "session_id": self.session_id,
                "config": self.session.config if self.session else {},
            },
        )

    # Group message handlers
    async def transcription_result(self, event: dict[str, Any]):
        """Handle transcription result from STT worker."""
        await self.send_event("transcription.completed", event["data"])

    async def response_chunk(self, event: dict[str, Any]):
        """Handle response chunk from LLM worker."""
        await self.send_event("response.chunk", event["data"])

    async def response_completed(self, event: dict[str, Any]):
        """Handle response completion."""
        await self.send_event("response.completed", event["data"])

    async def audio_output(self, event: dict[str, Any]):
        """Handle audio output from TTS worker."""
        await self.send_event("audio.output", event["data"])
