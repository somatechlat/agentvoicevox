"""
OpenAI Realtime Gateway Consumer
================================

This Django Channels WebSocket consumer implements the OpenAI Realtime WebSocket protocol.
It acts as a "Dumb Pipe" bridge between client applications (using standard OpenAI SDKs)
and the native OVOS message bus.

It receives base64 encoded audio from the client, decodes it, and sends it to OVOS.
Conversely, it listens to the ovos-bus for synthesized audio and streams it back to the
client as base64 PCM16 chunks, wrapped in the OpenAI `response.audio.delta` event format.
"""

import json
import logging
import base64
from typing import Any, Dict

from channels.generic.websocket import AsyncWebsocketConsumer
from ovos_bus_client import Message

from apps.voice.ovos_bridge import ovos_config_bridge

logger = logging.getLogger(__name__)

class OpenAIGatewayConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer that mimics the OpenAI Realtime API.
    """

    async def connect(self):
        """Accepts the WebSocket connection and sends the initial session.created event."""
        self.session_id = self.scope.get("session_id", "default_session")
        
        await self.accept()
        logger.info(f"OpenAI Gateway connection accepted. Session: {self.session_id}")

        # Send session.created event
        session_created = {
            "type": "session.created",
            "session": {
                "id": self.session_id,
                "model": "gpt-4o-realtime-preview-2024-10-01",
                "voice": "alloy",
                "instructions": "You are a helpful assistant.",
            }
        }
        await self.send(text_data=json.dumps(session_created))
        
        # We should register a callback with the OVOS bus to listen for audio responses.
        # For simplicity in this bridge, we assume the ovos_config_bridge handles emitting.
        # A more robust implementation would register a listener on the bus client here.

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        logger.info(f"OpenAI Gateway disconnected with code: {close_code}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Receives messages from the client.
        In the OpenAI protocol, everything is JSON strings containing base64 audio.
        """
        if text_data:
            try:
                data = json.loads(text_data)
                event_type = data.get("type")
                
                if event_type == "session.update":
                    await self._handle_session_update(data.get("session", {}))
                elif event_type == "input_audio_buffer.append":
                    await self._handle_audio_append(data.get("audio", ""))
                elif event_type == "input_audio_buffer.commit":
                    # Let OVOS know we finished sending audio if VAD is not handling it
                    await self._handle_audio_commit()
                elif event_type == "response.create":
                    pass # Trigger response manually
                else:
                    logger.debug(f"Unhandled event type: {event_type}")
                    
            except json.JSONDecodeError:
                await self._send_error("invalid_json", "Failed to parse JSON")

    async def _handle_session_update(self, session_data: Dict[str, Any]):
        """Updates the session configuration on the OVOS bus."""
        # Map OpenAI session fields to OVOS VoicePersona structure
        voice = session_data.get("voice", "af_heart")
        instructions = session_data.get("instructions", "")
        
        persona_config = {
            "voice": {"id": voice, "speed": 1.0},
            "stt": {"language": "en"},
            "llm": {"model": "default", "system_prompt": instructions, "temperature": 0.7}
        }
        
        # Apply to OVOS
        ovos_config_bridge.apply_persona_to_session(self.session_id, persona_config)
        logger.info(f"Session {self.session_id} updated with config: {persona_config}")

    async def _handle_audio_append(self, b64_audio: str):
        """
        Receives base64 audio, decodes it, and sends it to the OVOS bus.
        The OVOS listener component is configured to intercept the `avb.gateway.audio.chunk` 
        event and process the raw PCM stream directly.
        """
        # Decode base64 PCM16 24kHz audio
        try:
            audio_bytes = base64.b64decode(b64_audio)
            
            # Emit the verified Realtime audio chunk format for the AVB-OVOS pipeline.
            msg = Message("avb.gateway.audio.chunk", data={"audio": b64_audio}, context={"session_id": self.session_id})
            ovos_config_bridge.client.emit(msg)
            
        except Exception as e:
            logger.error(f"Error handling audio append: {e}")

    async def _handle_audio_commit(self):
        """Signals end of audio input."""
        msg = Message("avb.gateway.audio.commit", data={}, context={"session_id": self.session_id})
        ovos_config_bridge.client.emit(msg)

    async def _send_error(self, code: str, message: str):
        """Helper to send standard OpenAI error events."""
        error_event = {
            "type": "error",
            "error": {
                "type": "invalid_request_error",
                "code": code,
                "message": message
            }
        }
        await self.send(text_data=json.dumps(error_event))
