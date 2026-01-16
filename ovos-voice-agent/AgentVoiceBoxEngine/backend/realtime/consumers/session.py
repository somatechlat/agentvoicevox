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

    **Implements: WEBSOCKET-001, WEBSOCKET-002**
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
            await self.close(code=self.CLOSE_SESSION_INVALID)
            return

        await super().connect()

        if self.authenticated:
            # Validate session belongs to tenant
            if not await self._validate_session():
                await self.close(code=self.CLOSE_SESSION_INVALID)
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
        """
        Mark session as active.
        
        **Implements: WEBSOCKET-002**
        """
        if not self.session:
            return
        
        try:
            from django.utils import timezone

            self.session.status = "active"
            self.session.started_at = timezone.now()
            await self.session.asave(
                update_fields=["status", "started_at", "updated_at"]
            )
        except Exception as e:
            logger.error(f"Failed to activate session {self.session_id}: {e}")
            await self.send_error(
                "session_activation_failed",
                "Could not activate session",
                {"session_id": self.session_id}
            )

    async def _complete_session(self):
        """
        Mark session as completed.
        
        **Implements: WEBSOCKET-002**
        """
        if not self.session:
            return
        
        try:
            from django.utils import timezone

            self.session.status = "completed"
            self.session.terminated_at = timezone.now()
            if self.session.started_at:
                self.session.duration_seconds = (
                    self.session.terminated_at - self.session.started_at
                ).total_seconds()
            await self.session.asave(
                update_fields=[
                    "status",
                    "terminated_at",
                    "duration_seconds",
                    "updated_at",
                ]
            )
        except Exception as e:
            logger.error(f"Failed to complete session {self.session_id}: {e}")
            # Still send completion event to client
            await self.send_event(
                "session.completed",
                {
                    "session_id": self.session_id,
                    "status": "completed_with_errors",
                },
            )

    # Message handlers
    async def handle_audio_input(self, content: dict[str, Any]):
        """
        Handle incoming audio chunk with validation.
        
        **Implements: WEBSOCKET-001**
        """
        # Validate session state
        if not self.session or self.session.status != "active":
            await self.send_error("invalid_session", "Session is not active")
            return
        
        # Validate audio data exists
        audio_data = content.get("audio")
        if not audio_data:
            await self.send_error("missing_audio", "No audio data provided")
            return
        
        # Validate audio size (prevent DoS)
        if len(audio_data) > self.MAX_AUDIO_CHUNK_SIZE:
            await self.send_error(
                "audio_too_large", 
                f"Audio chunk exceeds {self.MAX_AUDIO_CHUNK_SIZE} bytes"
            )
            return
        
        # Apply rate limiting
        if not await self._check_rate_limit():
            await self.send_error(
                "rate_limited", 
                "Too many audio chunks - please slow down"
            )
            return
        
        # Forward to STT processing
        try:
            await self.channel_layer.group_send(
                f"stt_worker_{self.tenant_id}",
                {
                    "type": "process_audio",
                    "session_id": self.session_id,
                    "audio": audio_data,
                },
            )
        except Exception as e:
            logger.error(f"Failed to forward audio to STT worker: {e}")
            await self.send_error("processing_failed", "Could not process audio")

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
        """
        Handle session configuration update.
        
        **Implements: WEBSOCKET-002**
        """
        config = content.get("config", {})

        if self.session:
            try:
                self.session.config.update(config)
                await self.session.asave(update_fields=["config", "updated_at"])
            except Exception as e:
                logger.error(f"Failed to update session config: {e}")
                await self.send_error(
                    "update_failed",
                    "Could not update session configuration"
                )
                return

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
