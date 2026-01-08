"""
OpenAI Realtime API compatible Pydantic schemas.

These schemas implement the exact data structures required by the
OpenAI Realtime API specification for 100% compatibility.

All schemas use Django Ninja's Schema class (Pydantic v2).
"""

from datetime import datetime
from typing import Any, Literal, Optional, Union

from ninja import Field, Schema

# =============================================================================
# CONFIGURATION SCHEMAS
# =============================================================================


class InputAudioTranscription(Schema):
    """Input audio transcription configuration."""

    model: str = "whisper-1"


class TurnDetection(Schema):
    """Turn detection (VAD) configuration."""

    type: Literal["server_vad", "semantic_vad"] = "server_vad"
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    prefix_padding_ms: int = Field(default=300, ge=0)
    silence_duration_ms: int = Field(default=200, ge=0)
    create_response: bool = True
    interrupt_response: bool = True


class NoiseReduction(Schema):
    """Input audio noise reduction configuration."""

    type: Literal["near_field", "far_field"] = "near_field"


class ToolParameters(Schema):
    """JSON Schema for tool parameters."""

    type: str = "object"
    properties: dict[str, Any] = {}
    required: list[str] = []


class Tool(Schema):
    """Function tool definition."""

    type: Literal["function"] = "function"
    name: str
    description: Optional[str] = None
    parameters: dict[str, Any] = {}


class SessionConfig(Schema):
    """Session configuration matching OpenAI spec."""

    modalities: list[Literal["text", "audio"]] = ["text", "audio"]
    instructions: Optional[str] = None
    voice: Literal[
        "alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"
    ] = "alloy"
    input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = "pcm16"
    output_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = "pcm16"
    input_audio_transcription: Optional[InputAudioTranscription] = None
    turn_detection: Optional[TurnDetection] = None
    tools: list[Tool] = []
    tool_choice: Union[Literal["auto", "none", "required"], str] = "auto"
    temperature: float = Field(default=0.8, ge=0.6, le=1.2)
    max_response_output_tokens: Union[int, Literal["inf"]] = "inf"
    input_audio_noise_reduction: Optional[NoiseReduction] = None


class ResponseConfig(Schema):
    """Response configuration for response.create."""

    modalities: Optional[list[Literal["text", "audio"]]] = None
    instructions: Optional[str] = None
    voice: Optional[
        Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"]
    ] = None
    output_audio_format: Optional[Literal["pcm16", "g711_ulaw", "g711_alaw"]] = None
    tools: Optional[list[Tool]] = None
    tool_choice: Optional[Union[Literal["auto", "none", "required"], str]] = None
    temperature: Optional[float] = Field(default=None, ge=0.6, le=1.2)
    max_output_tokens: Optional[Union[int, Literal["inf"]]] = None
    conversation: Literal["auto", "none"] = "auto"
    input: Optional[list[dict[str, Any]]] = None
    metadata: Optional[dict[str, Any]] = None


# =============================================================================
# CONTENT PART SCHEMAS
# =============================================================================


class InputTextContent(Schema):
    """Input text content part."""

    type: Literal["input_text"] = "input_text"
    text: str


class InputAudioContent(Schema):
    """Input audio content part."""

    type: Literal["input_audio"] = "input_audio"
    audio: Optional[str] = None  # Base64 encoded
    transcript: Optional[str] = None


class TextContent(Schema):
    """Text content part (assistant output)."""

    type: Literal["text"] = "text"
    text: str


class AudioContent(Schema):
    """Audio content part (assistant output)."""

    type: Literal["audio"] = "audio"
    audio: Optional[str] = None  # Base64 encoded
    transcript: Optional[str] = None


ContentPart = Union[InputTextContent, InputAudioContent, TextContent, AudioContent]


# =============================================================================
# CONVERSATION ITEM SCHEMAS
# =============================================================================


class MessageItemInput(Schema):
    """Message item for conversation.item.create."""

    type: Literal["message"] = "message"
    role: Literal["system", "user", "assistant"]
    content: list[dict[str, Any]]


class FunctionCallItemInput(Schema):
    """Function call item for conversation.item.create."""

    type: Literal["function_call"] = "function_call"
    name: str
    call_id: str
    arguments: str


class FunctionCallOutputItemInput(Schema):
    """Function call output item for conversation.item.create."""

    type: Literal["function_call_output"] = "function_call_output"
    call_id: str
    output: str


ConversationItemInput = Union[
    MessageItemInput, FunctionCallItemInput, FunctionCallOutputItemInput
]


class ConversationItemObject(Schema):
    """Conversation item object in server events."""

    id: str
    object: Literal["realtime.item"] = "realtime.item"
    type: Literal["message", "function_call", "function_call_output"]
    status: Literal["completed", "incomplete", "in_progress"] = "completed"
    role: Optional[Literal["system", "user", "assistant"]] = None
    content: Optional[list[dict[str, Any]]] = None
    name: Optional[str] = None
    call_id: Optional[str] = None
    arguments: Optional[str] = None
    output: Optional[str] = None


# =============================================================================
# SESSION OBJECT SCHEMAS
# =============================================================================


class SessionObject(Schema):
    """Session object in server events."""

    id: str
    object: Literal["realtime.session"] = "realtime.session"
    model: str = "gpt-4o-realtime-preview"
    modalities: list[str] = ["text", "audio"]
    instructions: str = ""
    voice: str = "alloy"
    input_audio_format: str = "pcm16"
    output_audio_format: str = "pcm16"
    input_audio_transcription: Optional[dict[str, Any]] = None
    turn_detection: Optional[dict[str, Any]] = None
    tools: list[dict[str, Any]] = []
    tool_choice: str = "auto"
    temperature: float = 0.8
    max_response_output_tokens: Union[int, str] = "inf"
    input_audio_noise_reduction: Optional[dict[str, Any]] = None


class ConversationObject(Schema):
    """Conversation object in server events."""

    id: str
    object: Literal["realtime.conversation"] = "realtime.conversation"


# =============================================================================
# RESPONSE OBJECT SCHEMAS
# =============================================================================


class UsageDetails(Schema):
    """Token usage details."""

    cached_tokens: int = 0
    text_tokens: int = 0
    audio_tokens: int = 0


class Usage(Schema):
    """Token usage statistics."""

    total_tokens: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    input_token_details: Optional[UsageDetails] = None
    output_token_details: Optional[UsageDetails] = None


class ResponseObject(Schema):
    """Response object in server events."""

    id: str
    object: Literal["realtime.response"] = "realtime.response"
    status: Literal["in_progress", "completed", "cancelled", "incomplete", "failed"]
    status_details: Optional[dict[str, Any]] = None
    output: list[ConversationItemObject] = []
    usage: Optional[Usage] = None
    metadata: Optional[dict[str, Any]] = None


# =============================================================================
# ERROR SCHEMAS
# =============================================================================


class ErrorObject(Schema):
    """Error details."""

    type: Literal["invalid_request_error", "server_error", "authentication_error"]
    code: Optional[str] = None
    message: str
    param: Optional[str] = None
    event_id: Optional[str] = None


# =============================================================================
# RATE LIMIT SCHEMAS
# =============================================================================


class RateLimitInfo(Schema):
    """Rate limit information."""

    name: str
    limit: int
    remaining: int
    reset_seconds: float


# =============================================================================
# CLIENT EVENT SCHEMAS
# =============================================================================


class ClientEvent(Schema):
    """Base client event."""

    event_id: Optional[str] = None
    type: str


class SessionUpdateEvent(ClientEvent):
    """session.update event."""

    type: Literal["session.update"] = "session.update"
    session: SessionConfig


class InputAudioBufferAppendEvent(ClientEvent):
    """input_audio_buffer.append event."""

    type: Literal["input_audio_buffer.append"] = "input_audio_buffer.append"
    audio: str  # Base64 encoded


class InputAudioBufferCommitEvent(ClientEvent):
    """input_audio_buffer.commit event."""

    type: Literal["input_audio_buffer.commit"] = "input_audio_buffer.commit"


class InputAudioBufferClearEvent(ClientEvent):
    """input_audio_buffer.clear event."""

    type: Literal["input_audio_buffer.clear"] = "input_audio_buffer.clear"


class ConversationItemCreateEvent(ClientEvent):
    """conversation.item.create event."""

    type: Literal["conversation.item.create"] = "conversation.item.create"
    previous_item_id: Optional[str] = None
    item: dict[str, Any]  # ConversationItemInput


class ConversationItemDeleteEvent(ClientEvent):
    """conversation.item.delete event."""

    type: Literal["conversation.item.delete"] = "conversation.item.delete"
    item_id: str


class ConversationItemTruncateEvent(ClientEvent):
    """conversation.item.truncate event."""

    type: Literal["conversation.item.truncate"] = "conversation.item.truncate"
    item_id: str
    content_index: int
    audio_end_ms: int


class ConversationItemRetrieveEvent(ClientEvent):
    """conversation.item.retrieve event."""

    type: Literal["conversation.item.retrieve"] = "conversation.item.retrieve"
    item_id: str


class ResponseCreateEvent(ClientEvent):
    """response.create event."""

    type: Literal["response.create"] = "response.create"
    response: Optional[ResponseConfig] = None


class ResponseCancelEvent(ClientEvent):
    """response.cancel event."""

    type: Literal["response.cancel"] = "response.cancel"


class OutputAudioBufferClearEvent(ClientEvent):
    """output_audio_buffer.clear event."""

    type: Literal["output_audio_buffer.clear"] = "output_audio_buffer.clear"


# =============================================================================
# SERVER EVENT SCHEMAS
# =============================================================================


class ServerEvent(Schema):
    """Base server event."""

    event_id: str
    type: str


# Session Events
class SessionCreatedEvent(ServerEvent):
    """session.created event."""

    type: Literal["session.created"] = "session.created"
    session: SessionObject


class SessionUpdatedEvent(ServerEvent):
    """session.updated event."""

    type: Literal["session.updated"] = "session.updated"
    session: SessionObject


# Conversation Events
class ConversationCreatedEvent(ServerEvent):
    """conversation.created event."""

    type: Literal["conversation.created"] = "conversation.created"
    conversation: ConversationObject


class ConversationItemCreatedEvent(ServerEvent):
    """conversation.item.created event."""

    type: Literal["conversation.item.created"] = "conversation.item.created"
    previous_item_id: Optional[str] = None
    item: ConversationItemObject


class ConversationItemDeletedEvent(ServerEvent):
    """conversation.item.deleted event."""

    type: Literal["conversation.item.deleted"] = "conversation.item.deleted"
    item_id: str


class ConversationItemTruncatedEvent(ServerEvent):
    """conversation.item.truncated event."""

    type: Literal["conversation.item.truncated"] = "conversation.item.truncated"
    item_id: str
    content_index: int
    audio_end_ms: int


class ConversationItemRetrievedEvent(ServerEvent):
    """conversation.item.retrieved event."""

    type: Literal["conversation.item.retrieved"] = "conversation.item.retrieved"
    item: ConversationItemObject


# Input Audio Buffer Events
class InputAudioBufferCommittedEvent(ServerEvent):
    """input_audio_buffer.committed event."""

    type: Literal["input_audio_buffer.committed"] = "input_audio_buffer.committed"
    previous_item_id: Optional[str] = None
    item_id: str


class InputAudioBufferClearedEvent(ServerEvent):
    """input_audio_buffer.cleared event."""

    type: Literal["input_audio_buffer.cleared"] = "input_audio_buffer.cleared"


class InputAudioBufferSpeechStartedEvent(ServerEvent):
    """input_audio_buffer.speech_started event."""

    type: Literal["input_audio_buffer.speech_started"] = (
        "input_audio_buffer.speech_started"
    )
    audio_start_ms: int
    item_id: str


class InputAudioBufferSpeechStoppedEvent(ServerEvent):
    """input_audio_buffer.speech_stopped event."""

    type: Literal["input_audio_buffer.speech_stopped"] = (
        "input_audio_buffer.speech_stopped"
    )
    audio_end_ms: int
    item_id: str


# Transcription Events
class InputAudioTranscriptionCompletedEvent(ServerEvent):
    """conversation.item.input_audio_transcription.completed event."""

    type: Literal["conversation.item.input_audio_transcription.completed"] = (
        "conversation.item.input_audio_transcription.completed"
    )
    item_id: str
    content_index: int
    transcript: str


class InputAudioTranscriptionFailedEvent(ServerEvent):
    """conversation.item.input_audio_transcription.failed event."""

    type: Literal["conversation.item.input_audio_transcription.failed"] = (
        "conversation.item.input_audio_transcription.failed"
    )
    item_id: str
    content_index: int
    error: ErrorObject


# Response Events
class ResponseCreatedEvent(ServerEvent):
    """response.created event."""

    type: Literal["response.created"] = "response.created"
    response: ResponseObject


class ResponseDoneEvent(ServerEvent):
    """response.done event."""

    type: Literal["response.done"] = "response.done"
    response: ResponseObject


class ResponseCancelledEvent(ServerEvent):
    """response.cancelled event (note: OpenAI uses British spelling)."""

    type: Literal["response.cancelled"] = "response.cancelled"
    response_id: str


class ResponseOutputItemAddedEvent(ServerEvent):
    """response.output_item.added event."""

    type: Literal["response.output_item.added"] = "response.output_item.added"
    response_id: str
    output_index: int
    item: ConversationItemObject


class ResponseOutputItemDoneEvent(ServerEvent):
    """response.output_item.done event."""

    type: Literal["response.output_item.done"] = "response.output_item.done"
    response_id: str
    output_index: int
    item: ConversationItemObject


class ResponseContentPartAddedEvent(ServerEvent):
    """response.content_part.added event."""

    type: Literal["response.content_part.added"] = "response.content_part.added"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    part: dict[str, Any]


class ResponseContentPartDoneEvent(ServerEvent):
    """response.content_part.done event."""

    type: Literal["response.content_part.done"] = "response.content_part.done"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    part: dict[str, Any]


# Audio Streaming Events
class ResponseAudioDeltaEvent(ServerEvent):
    """response.audio.delta event."""

    type: Literal["response.audio.delta"] = "response.audio.delta"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    delta: str  # Base64 encoded audio


class ResponseAudioDoneEvent(ServerEvent):
    """response.audio.done event."""

    type: Literal["response.audio.done"] = "response.audio.done"
    response_id: str
    item_id: str
    output_index: int
    content_index: int


class ResponseAudioTranscriptDeltaEvent(ServerEvent):
    """response.audio_transcript.delta event."""

    type: Literal["response.audio_transcript.delta"] = "response.audio_transcript.delta"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    delta: str


class ResponseAudioTranscriptDoneEvent(ServerEvent):
    """response.audio_transcript.done event."""

    type: Literal["response.audio_transcript.done"] = "response.audio_transcript.done"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    transcript: str


# Text Streaming Events
class ResponseTextDeltaEvent(ServerEvent):
    """response.text.delta event."""

    type: Literal["response.text.delta"] = "response.text.delta"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    delta: str


class ResponseTextDoneEvent(ServerEvent):
    """response.text.done event."""

    type: Literal["response.text.done"] = "response.text.done"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    text: str


# Function Call Events
class ResponseFunctionCallArgumentsDeltaEvent(ServerEvent):
    """response.function_call_arguments.delta event."""

    type: Literal["response.function_call_arguments.delta"] = (
        "response.function_call_arguments.delta"
    )
    response_id: str
    item_id: str
    output_index: int
    call_id: str
    delta: str


class ResponseFunctionCallArgumentsDoneEvent(ServerEvent):
    """response.function_call_arguments.done event."""

    type: Literal["response.function_call_arguments.done"] = (
        "response.function_call_arguments.done"
    )
    response_id: str
    item_id: str
    output_index: int
    call_id: str
    arguments: str


# Output Audio Buffer Events
class OutputAudioBufferClearedEvent(ServerEvent):
    """output_audio_buffer.cleared event."""

    type: Literal["output_audio_buffer.cleared"] = "output_audio_buffer.cleared"


class OutputAudioBufferStartedEvent(ServerEvent):
    """output_audio_buffer.started event."""

    type: Literal["output_audio_buffer.started"] = "output_audio_buffer.started"
    response_id: str


class OutputAudioBufferStoppedEvent(ServerEvent):
    """output_audio_buffer.stopped event."""

    type: Literal["output_audio_buffer.stopped"] = "output_audio_buffer.stopped"
    response_id: str


# Rate Limit Events
class RateLimitsUpdatedEvent(ServerEvent):
    """rate_limits.updated event."""

    type: Literal["rate_limits.updated"] = "rate_limits.updated"
    rate_limits: list[RateLimitInfo]


# Error Event
class ErrorEvent(ServerEvent):
    """error event."""

    type: Literal["error"] = "error"
    error: ErrorObject


# =============================================================================
# REST API SCHEMAS
# =============================================================================


class SessionCreateRequest(Schema):
    """Request body for POST /v1/realtime/sessions."""

    model: str = "gpt-4o-realtime-preview"
    session: Optional[SessionConfig] = None


class ClientSecretObject(Schema):
    """Client secret object in session create response."""

    value: str
    expires_at: int  # Unix timestamp


class SessionCreateResponse(Schema):
    """Response for POST /v1/realtime/sessions."""

    id: str
    object: Literal["realtime.session"] = "realtime.session"
    model: str
    modalities: list[str]
    instructions: str
    voice: str
    input_audio_format: str
    output_audio_format: str
    input_audio_transcription: Optional[dict[str, Any]] = None
    turn_detection: Optional[dict[str, Any]] = None
    tools: list[dict[str, Any]]
    tool_choice: str
    temperature: float
    max_response_output_tokens: Union[int, str]
    client_secret: ClientSecretObject


class SessionListResponse(Schema):
    """Response for GET /v1/realtime/sessions."""

    object: Literal["list"] = "list"
    data: list[SessionObject]


class SessionDetailResponse(Schema):
    """Response for GET /v1/realtime/sessions/{id}."""

    id: str
    object: Literal["realtime.session"] = "realtime.session"
    model: str
    status: str
    modalities: list[str]
    instructions: str
    voice: str
    input_audio_format: str
    output_audio_format: str
    input_audio_transcription: Optional[dict[str, Any]] = None
    turn_detection: Optional[dict[str, Any]] = None
    tools: list[dict[str, Any]]
    tool_choice: str
    temperature: float
    max_response_output_tokens: Union[int, str]
    created_at: datetime
    expires_at: Optional[datetime] = None
