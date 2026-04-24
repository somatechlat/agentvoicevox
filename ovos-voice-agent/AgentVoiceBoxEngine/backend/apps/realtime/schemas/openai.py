"""
OpenAI Realtime Protocol Schemas
================================

These Pydantic schemas define the structures for messages exchanged over the
`/ws/v1/realtime` WebSocket. They map directly to the official OpenAI Realtime API
specification, allowing AVB to act as a drop-in replacement.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel


class OpenAIBaseEvent(BaseModel):
    """Base event structure for all OpenAI realtime messages."""
    type: str

class SessionUpdateEvent(OpenAIBaseEvent):
    """Client event to update session configuration (e.g. voice, instructions)."""
    type: str = "session.update"
    session: Dict[str, Any]

class InputAudioBufferAppendEvent(OpenAIBaseEvent):
    """Client event to send raw base64 PCM audio chunks."""
    type: str = "input_audio_buffer.append"
    audio: str  # Base64 encoded PCM16 audio

class InputAudioBufferCommitEvent(OpenAIBaseEvent):
    """Client event indicating end of audio input (if VAD is disabled)."""
    type: str = "input_audio_buffer.commit"

class ResponseCreateEvent(OpenAIBaseEvent):
    """Client event to manually trigger a response."""
    type: str = "response.create"
    response: Optional[Dict[str, Any]] = None

# --- Server Events ---

class ServerSessionCreatedEvent(OpenAIBaseEvent):
    type: str = "session.created"
    session: Dict[str, Any]

class ServerResponseAudioDeltaEvent(OpenAIBaseEvent):
    """Server event streaming synthesized audio back to the client."""
    type: str = "response.audio.delta"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    delta: str  # Base64 encoded PCM16 audio

class ServerResponseAudioDoneEvent(OpenAIBaseEvent):
    type: str = "response.audio.done"
    response_id: str
    item_id: str
    output_index: int
    content_index: int

class ServerErrorEvent(OpenAIBaseEvent):
    type: str = "error"
    error: Dict[str, Any]
