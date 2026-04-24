"""
Voice session WebSocket consumer.

Handles real-time voice communication for sessions.
"""

import logging
import uuid
from typing import Any, Optional

from django.conf import settings
from apps.realtime.ovos_bus import OVOSIntelligenceBridge

from .base import BaseConsumer

logger = logging.getLogger(__name__)

# Shared OVOS Bridge instance
ovos_bridge = OVOSIntelligenceBridge()


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

            # Connect to OVOS Bridge
            await ovos_bridge.connect()
            ovos_bridge.register_session(self.session_id, self.handle_ovos_speak)

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

            # Unregister from OVOS Bridge
            ovos_bridge.unregister_session(self.session_id)

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
    async def handle_input_audio_buffer_append(self, content: dict[str, Any]):
        """
        Handle input_audio_buffer.append event.
        
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

        # Forward to STT processing via Redis Stream (simplified for now to match current worker)
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
            await self.send_error("server_error", "Could not process audio buffer")

    async def handle_input_audio_buffer_commit(self, content: dict[str, Any]):
        """Handle input_audio_buffer.commit event."""
        await self.send_event("input_audio_buffer.committed", {
            "session_id": self.session_id,
            "item_id": f"item_{uuid.uuid4().hex[:12]}"
        })

    async def handle_input_audio_buffer_clear(self, content: dict[str, Any]):
        """Handle input_audio_buffer.clear event."""
        await self.send_event("input_audio_buffer.cleared", {})

    async def handle_response_create(self, content: dict[str, Any]):
        """Handle response.create event."""
        # Trigger LLM response generation
        await self.send_event(
            "response.created",
            {
                "response": {
                    "id": f"resp_{uuid.uuid4().hex[:12]}",
                    "object": "realtime.response",
                    "status": "in_progress",
                    "output": []
                }
            },
        )

    async def handle_response_cancel(self, content: dict[str, Any]):
        """Handle response.cancel event."""
        await self.send_event(
            "response.cancelled",
            {
                "response_id": content.get("response_id", "unknown"),
            },
        )

    async def handle_session_update(self, content: dict[str, Any]):
        """
        Handle session.update event.
        
        **Implements: WEBSOCKET-002**
        """
        config = content.get("session", {})

        if self.session:
            try:
                # Merge config
                current_config = self.session.config or {}
                current_config.update(config)
                self.session.config = current_config
                await self.session.asave(update_fields=["config", "updated_at"])
            except Exception as e:
                logger.error(f"Failed to update session config: {e}")
                await self.send_error(
                    "server_error",
                    "Could not update session configuration"
                )
                return

        await self.send_event(
            "session.updated",
            {
                "session": {
                    "id": self.session_id,
                    "object": "realtime.session",
                    "model": self.session.config.get("model", "gpt-4o-realtime-preview"),
                    "modalities": self.session.config.get("modalities", ["text", "audio"]),
                    "instructions": self.session.config.get("instructions", ""),
                    "voice": self.session.config.get("voice", "alloy"),
                    "input_audio_format": self.session.config.get("input_audio_format", "pcm16"),
                    "output_audio_format": self.session.config.get("output_audio_format", "pcm16"),
                    "turn_detection": self.session.config.get("turn_detection"),
                    "tools": self.session.config.get("tools", []),
                    "tool_choice": self.session.config.get("tool_choice", "auto"),
                    "temperature": self.session.config.get("temperature", 0.8),
                    "max_response_output_tokens": self.session.config.get("max_response_output_tokens", "inf"),
                }
            },
        )

    # Group message handlers (Server-originated events via channel layer)
    async def transcription_result(self, event: dict[str, Any]):
        """Handle transcription result from STT worker."""
        data = event["data"]
        transcript = data.get("text", "")

        # 1. Send to client
        await self.send_event("conversation.item.input_audio_transcription.completed", {
            "item_id": data.get("correlation_id", "unknown"),
            "content_index": 0,
            "transcript": transcript
        })

        # 2. Forward to OVOS Skill Bus
        if transcript:
            await ovos_bridge.send_utterance(
                session_id=self.session_id,
                text=transcript,
                context={"correlation_id": data.get("correlation_id")}
            )

    async def session_event(self, event: dict[str, Any]):
        """Handle lifecycle events from STT/TTS workers (e.g. speech_started)."""
        data = event["data"]
        await self.send_event(data["type"], {
            "session_id": data["session_id"]
        })

    async def handle_ovos_speak(self, utterance: str, context: dict[str, Any]):
        """
        Callback handler for OVOS 'speak' messages.
        Forwards the response to the client and triggers TTS.
        """
        response_id = f"resp_{uuid.uuid4().hex[:12]}"
        correlation_id = context.get("correlation_id", "unknown")

        # 1. Send transcript delta to client (OpenAI spec)
        await self.send_event("response.audio_transcript.delta", {
            "response_id": response_id,
            "delta": utterance
        })

        # 2. Trigger TTS Worker via Redis Stream
        try:
            from apps.workflows.redis_client import RedisClient
            redis = RedisClient()
            await redis.connect()

            await redis.client.xadd(
                settings.TTS_WORKER["STREAM_REQUESTS"],
                {
                    "session_id": self.session_id,
                    "text": utterance,
                    "response_id": response_id,
                    "correlation_id": correlation_id,
                    "voice": self.session.config.get("voice", settings.TTS_WORKER["DEFAULT_VOICE"]),
                    "speed": str(self.session.config.get("speed", settings.TTS_WORKER["DEFAULT_SPEED"])),
                }
            )
            await redis.disconnect()
        except Exception as e:
            logger.error(f"Failed to trigger TTS for session {self.session_id}: {e}")
            await self.send_error("server_error", "Could not synthesize speech")

    async def response_chunk(self, event: dict[str, Any]):
        """Handle response chunk from LLM worker."""
        # Align with OpenAI response.audio_transcript.delta or response.audio.delta
        data = event["data"]
        if "text" in data:
            await self.send_event("response.text.delta", {
                "response_id": data.get("response_id"),
                "item_id": data.get("item_id"),
                "output_index": 0,
                "content_index": 0,
                "delta": data["text"]
            })
        elif "audio" in data:
            await self.send_event("response.audio.delta", {
                "response_id": data.get("response_id"),
                "item_id": data.get("item_id"),
                "output_index": 0,
                "content_index": 0,
                "delta": data["audio"]
            })

    async def response_completed(self, event: dict[str, Any]):
        """Handle response completion."""
        data = event["data"]
        await self.send_event("response.done", {
            "response": {
                "id": data.get("response_id"),
                "object": "realtime.response",
                "status": "completed",
                "output": [],
                "usage": data.get("usage", {})
            }
        })

    async def audio_output(self, event: dict[str, Any]):
        """Handle audio output from TTS worker."""
        # Handled by response_chunk in OpenAI spec as response.audio.delta
        pass
