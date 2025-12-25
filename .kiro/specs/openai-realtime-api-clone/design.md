# Design Document: OpenAI Realtime API Clone

## Overview

This design document specifies the architecture for implementing a **100% OpenAI Realtime API compatible** WebSocket and REST API layer in the AgentVoiceBox platform. The implementation is a complete drop-in replacement for OpenAI's Realtime API, supporting all endpoints, events, parameters, and behaviors exactly as documented by OpenAI.

The implementation uses:
- **Django 5.1+** - Web framework
- **Django Ninja** - REST API with OpenAPI documentation
- **Django Channels** - WebSocket support with ASGI
- **Django ORM** - Database access
- **Redis** - Channel layer, caching, ephemeral token storage

## Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Browser/SDK]
        Server[Server App]
    end

    subgraph "API Gateway (Nginx)"
        REST[REST /v1/realtime/*]
        WS[WebSocket /v1/realtime]
    end

    subgraph "Django Application"
        subgraph "REST API (Django Ninja)"
            SessionsAPI[POST /v1/realtime/sessions]
            SessionsListAPI[GET /v1/realtime/sessions]
            SessionDetailAPI[GET/DELETE /v1/realtime/sessions/{id}]
        end

        subgraph "WebSocket (Django Channels)"
            RealtimeConsumer[RealtimeConsumer]
            EventRouter[Event Router]
        end

        subgraph "Services"
            SessionService[Session Service]
            ConversationService[Conversation Service]
            AudioService[Audio Service]
            ResponseService[Response Service]
            TokenService[Ephemeral Token Service]
        end

        subgraph "Event Handlers"
            SessionHandler[Session Events]
            AudioBufferHandler[Audio Buffer Events]
            ConversationHandler[Conversation Events]
            ResponseHandler[Response Events]
        end
    end

    subgraph "Processing Workers"
        STTWorker[STT Worker]
        TTSWorker[TTS Worker]
        LLMWorker[LLM Worker]
        VADWorker[VAD Worker]
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL)]
        Redis[(Redis)]
    end

    Browser --> REST
    Browser --> WS
    Server --> REST
    Server --> WS

    REST --> SessionsAPI
    REST --> SessionsListAPI
    REST --> SessionDetailAPI
    WS --> RealtimeConsumer

    RealtimeConsumer --> EventRouter
    EventRouter --> SessionHandler
    EventRouter --> AudioBufferHandler
    EventRouter --> ConversationHandler
    EventRouter --> ResponseHandler

    SessionsAPI --> TokenService
    SessionsAPI --> SessionService
    RealtimeConsumer --> SessionService
    RealtimeConsumer --> ConversationService
    RealtimeConsumer --> AudioService
    RealtimeConsumer --> ResponseService

    SessionHandler --> SessionService
    AudioBufferHandler --> AudioService
    ConversationHandler --> ConversationService
    ResponseHandler --> ResponseService

    AudioService --> STTWorker
    AudioService --> VADWorker
    ResponseService --> LLMWorker
    ResponseService --> TTSWorker

    SessionService --> PostgreSQL
    ConversationService --> PostgreSQL
    TokenService --> Redis
    AudioService --> Redis
```

## Components and Interfaces

### 1. WebSocket Consumer: `RealtimeConsumer`

The main WebSocket consumer handling the `/v1/realtime` endpoint.

```python
# Location: backend/realtime/consumers/openai_realtime.py

class RealtimeConsumer(AsyncJsonWebsocketConsumer):
    """
    OpenAI Realtime API compatible WebSocket consumer.
    
    Handles all client events and emits server events according to
    the OpenAI Realtime API specification.
    """
    
    # Connection lifecycle
    async def connect(self) -> None: ...
    async def disconnect(self, close_code: int) -> None: ...
    
    # Message routing
    async def receive_json(self, content: dict) -> None: ...
    
    # Client event handlers
    async def handle_session_update(self, event: SessionUpdateEvent) -> None: ...
    async def handle_input_audio_buffer_append(self, event: AudioAppendEvent) -> None: ...
    async def handle_input_audio_buffer_commit(self, event: AudioCommitEvent) -> None: ...
    async def handle_input_audio_buffer_clear(self, event: AudioClearEvent) -> None: ...
    async def handle_conversation_item_create(self, event: ItemCreateEvent) -> None: ...
    async def handle_conversation_item_delete(self, event: ItemDeleteEvent) -> None: ...
    async def handle_conversation_item_truncate(self, event: ItemTruncateEvent) -> None: ...
    async def handle_response_create(self, event: ResponseCreateEvent) -> None: ...
    async def handle_response_cancel(self, event: ResponseCancelEvent) -> None: ...
    
    # Server event emitters
    async def emit_session_created(self, session: RealtimeSession) -> None: ...
    async def emit_session_updated(self, session: RealtimeSession) -> None: ...
    async def emit_conversation_created(self, conversation: Conversation) -> None: ...
    async def emit_conversation_item_created(self, item: ConversationItem) -> None: ...
    async def emit_error(self, error: RealtimeError) -> None: ...
    # ... all 28+ server events
```

### 2. REST API Router: `realtime_router`

Django Ninja router for REST endpoints.

```python
# Location: backend/apps/realtime/api.py

realtime_router = Router(tags=["Realtime API"])

@realtime_router.post("/sessions", response=SessionCreateResponse)
async def create_session(
    request: HttpRequest,
    payload: SessionCreateRequest,
) -> SessionCreateResponse:
    """Create a new realtime session with ephemeral token."""
    ...

@realtime_router.get("/sessions", response=List[SessionResponse])
async def list_sessions(request: HttpRequest) -> List[SessionResponse]:
    """List active realtime sessions (admin only)."""
    ...

@realtime_router.get("/sessions/{session_id}", response=SessionResponse)
async def get_session(
    request: HttpRequest,
    session_id: str,
) -> SessionResponse:
    """Get session details."""
    ...

@realtime_router.delete("/sessions/{session_id}")
async def delete_session(
    request: HttpRequest,
    session_id: str,
) -> None:
    """Terminate a session."""
    ...
```

### 3. Services

#### 3.1 Ephemeral Token Service

```python
# Location: backend/apps/realtime/services/token_service.py

class EphemeralTokenService:
    """
    Manages ephemeral tokens for WebSocket authentication.
    
    Tokens are stored in Redis with TTL for automatic expiration.
    """
    
    TOKEN_PREFIX = "realtime:token:"
    DEFAULT_TTL = 60  # seconds
    
    async def create_token(
        self,
        tenant_id: UUID,
        session_config: Optional[SessionConfig] = None,
        ttl: int = DEFAULT_TTL,
    ) -> EphemeralToken: ...
    
    async def validate_token(self, token: str) -> Optional[TokenClaims]: ...
    
    async def revoke_token(self, token: str) -> bool: ...
```

#### 3.2 Session Service

```python
# Location: backend/apps/realtime/services/session_service.py

class RealtimeSessionService:
    """
    Manages realtime session lifecycle and configuration.
    """
    
    async def create_session(
        self,
        tenant_id: UUID,
        config: SessionConfig,
    ) -> RealtimeSession: ...
    
    async def update_session(
        self,
        session_id: str,
        config: SessionConfig,
    ) -> RealtimeSession: ...
    
    async def get_session(self, session_id: str) -> Optional[RealtimeSession]: ...
    
    async def terminate_session(self, session_id: str) -> None: ...
```

#### 3.3 Conversation Service

```python
# Location: backend/apps/realtime/services/conversation_service.py

class ConversationService:
    """
    Manages conversation items within a session.
    """
    
    async def create_conversation(
        self,
        session_id: str,
    ) -> Conversation: ...
    
    async def add_item(
        self,
        conversation_id: str,
        item: ConversationItem,
        previous_item_id: Optional[str] = None,
    ) -> ConversationItem: ...
    
    async def delete_item(
        self,
        conversation_id: str,
        item_id: str,
    ) -> None: ...
    
    async def truncate_item(
        self,
        item_id: str,
        content_index: int,
        audio_end_ms: int,
    ) -> ConversationItem: ...
```

#### 3.4 Audio Service

```python
# Location: backend/apps/realtime/services/audio_service.py

class AudioService:
    """
    Manages audio buffers and audio format conversion.
    """
    
    async def append_audio(
        self,
        session_id: str,
        audio_base64: str,
    ) -> None: ...
    
    async def commit_buffer(
        self,
        session_id: str,
    ) -> str:  # Returns item_id
        ...
    
    async def clear_buffer(
        self,
        session_id: str,
    ) -> None: ...
    
    def convert_audio(
        self,
        audio_data: bytes,
        from_format: AudioFormat,
        to_format: AudioFormat,
    ) -> bytes: ...
```

#### 3.5 Response Service

```python
# Location: backend/apps/realtime/services/response_service.py

class ResponseService:
    """
    Manages response generation via LLM and TTS.
    """
    
    async def create_response(
        self,
        session_id: str,
        config: Optional[ResponseConfig] = None,
    ) -> Response: ...
    
    async def cancel_response(
        self,
        session_id: str,
        response_id: str,
    ) -> None: ...
    
    async def stream_response(
        self,
        response: Response,
        callback: Callable[[ServerEvent], Awaitable[None]],
    ) -> None: ...
```

## Data Models

### Django Models

```python
# Location: backend/apps/realtime/models.py

class RealtimeSession(TenantScopedModel):
    """
    OpenAI Realtime API session.
    
    Stores session configuration and state.
    """
    id = models.CharField(max_length=64, primary_key=True)  # sess_xxx format
    object = models.CharField(max_length=32, default="realtime.session")
    model = models.CharField(max_length=64, default="gpt-4o-realtime-preview")
    
    # Configuration
    modalities = ArrayField(models.CharField(max_length=16), default=list)
    instructions = models.TextField(blank=True)
    voice = models.CharField(max_length=32, default="alloy")
    input_audio_format = models.CharField(max_length=16, default="pcm16")
    output_audio_format = models.CharField(max_length=16, default="pcm16")
    input_audio_transcription = models.JSONField(null=True, blank=True)
    turn_detection = models.JSONField(null=True, blank=True)
    tools = models.JSONField(default=list)
    tool_choice = models.CharField(max_length=64, default="auto")
    temperature = models.FloatField(default=0.8)
    max_response_output_tokens = models.CharField(max_length=16, default="inf")
    
    # Noise reduction
    input_audio_noise_reduction = models.JSONField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=32, default="active")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)


class Conversation(models.Model):
    """
    Conversation within a realtime session.
    """
    id = models.CharField(max_length=64, primary_key=True)  # conv_xxx format
    object = models.CharField(max_length=32, default="realtime.conversation")
    session = models.ForeignKey(RealtimeSession, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class ConversationItem(models.Model):
    """
    Item within a conversation (message, function_call, function_call_output).
    """
    id = models.CharField(max_length=64, primary_key=True)  # item_xxx format
    object = models.CharField(max_length=32, default="realtime.item")
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    
    # Item type and role
    type = models.CharField(max_length=32)  # message, function_call, function_call_output
    role = models.CharField(max_length=16, null=True, blank=True)  # system, user, assistant
    status = models.CharField(max_length=16, default="completed")
    
    # Content
    content = models.JSONField(default=list)  # Array of content parts
    
    # Function call specific
    name = models.CharField(max_length=256, null=True, blank=True)
    call_id = models.CharField(max_length=64, null=True, blank=True)
    arguments = models.TextField(null=True, blank=True)
    output = models.TextField(null=True, blank=True)
    
    # Ordering
    position = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)


class Response(models.Model):
    """
    Response generated by the model.
    """
    id = models.CharField(max_length=64, primary_key=True)  # resp_xxx format
    object = models.CharField(max_length=32, default="realtime.response")
    session = models.ForeignKey(RealtimeSession, on_delete=models.CASCADE)
    
    # Status
    status = models.CharField(max_length=16, default="in_progress")
    status_details = models.JSONField(null=True, blank=True)
    
    # Output items
    output = models.JSONField(default=list)  # Array of item IDs
    
    # Usage
    usage = models.JSONField(null=True, blank=True)
    
    # Metadata
    metadata = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

### Pydantic Schemas (Django Ninja)

```python
# Location: backend/apps/realtime/schemas.py

# ============== Session Schemas ==============

class SessionConfig(Schema):
    """Session configuration matching OpenAI spec."""
    modalities: List[Literal["text", "audio"]] = ["text", "audio"]
    instructions: Optional[str] = None
    voice: Literal["alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse"] = "alloy"
    input_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = "pcm16"
    output_audio_format: Literal["pcm16", "g711_ulaw", "g711_alaw"] = "pcm16"
    input_audio_transcription: Optional[InputAudioTranscription] = None
    turn_detection: Optional[TurnDetection] = None
    tools: List[Tool] = []
    tool_choice: Union[Literal["auto", "none", "required"], str] = "auto"
    temperature: float = Field(default=0.8, ge=0.6, le=1.2)
    max_response_output_tokens: Union[int, Literal["inf"]] = "inf"
    input_audio_noise_reduction: Optional[NoiseReduction] = None


class TurnDetection(Schema):
    """Turn detection (VAD) configuration."""
    type: Literal["server_vad", "semantic_vad"] = "server_vad"
    threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    prefix_padding_ms: int = 300
    silence_duration_ms: int = 200
    create_response: bool = True
    interrupt_response: bool = True


class Tool(Schema):
    """Function tool definition."""
    type: Literal["function"] = "function"
    name: str
    description: Optional[str] = None
    parameters: dict  # JSON Schema


# ============== Client Event Schemas ==============

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
    item: ConversationItemInput


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


class ResponseCreateEvent(ClientEvent):
    """response.create event."""
    type: Literal["response.create"] = "response.create"
    response: Optional[ResponseConfig] = None


class ResponseCancelEvent(ClientEvent):
    """response.cancel event."""
    type: Literal["response.cancel"] = "response.cancel"


# ============== Server Event Schemas ==============

class ServerEvent(Schema):
    """Base server event."""
    event_id: str
    type: str


class SessionCreatedEvent(ServerEvent):
    """session.created event."""
    type: Literal["session.created"] = "session.created"
    session: SessionObject


class SessionUpdatedEvent(ServerEvent):
    """session.updated event."""
    type: Literal["session.updated"] = "session.updated"
    session: SessionObject


class ConversationCreatedEvent(ServerEvent):
    """conversation.created event."""
    type: Literal["conversation.created"] = "conversation.created"
    conversation: ConversationObject


class ConversationItemCreatedEvent(ServerEvent):
    """conversation.item.created event."""
    type: Literal["conversation.item.created"] = "conversation.item.created"
    previous_item_id: Optional[str] = None
    item: ConversationItemObject


class ResponseCreatedEvent(ServerEvent):
    """response.created event."""
    type: Literal["response.created"] = "response.created"
    response: ResponseObject


class ResponseAudioDeltaEvent(ServerEvent):
    """response.audio.delta event."""
    type: Literal["response.audio.delta"] = "response.audio.delta"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    delta: str  # Base64 encoded audio


class ResponseTextDeltaEvent(ServerEvent):
    """response.text.delta event."""
    type: Literal["response.text.delta"] = "response.text.delta"
    response_id: str
    item_id: str
    output_index: int
    content_index: int
    delta: str


class ErrorEvent(ServerEvent):
    """error event."""
    type: Literal["error"] = "error"
    error: ErrorObject


class ErrorObject(Schema):
    """Error details."""
    type: Literal["invalid_request_error", "server_error", "authentication_error"]
    code: Optional[str] = None
    message: str
    param: Optional[str] = None
    event_id: Optional[str] = None
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Authentication Validation

*For any* authentication attempt with a token (valid, invalid, or expired), the Realtime API SHALL correctly authenticate valid tokens, reject invalid tokens with appropriate error codes, and reject expired tokens with 401 status.

**Validates: Requirements 1.2, 1.3, 1.4, 2.4, 2.5**

### Property 2: Session Configuration Validation

*For any* valid session configuration (modalities, voice, audio formats, turn detection, tools, temperature), the Realtime API SHALL accept the configuration and store it correctly. *For any* invalid configuration (out-of-range temperature, invalid voice, invalid format), the Realtime API SHALL reject with an error event.

**Validates: Requirements 3.1-3.12**

### Property 3: Audio Buffer Consistency

*For any* sequence of `input_audio_buffer.append`, `input_audio_buffer.commit`, and `input_audio_buffer.clear` operations, the audio buffer state SHALL be consistent: appends accumulate data, commit creates an item and clears buffer, clear empties buffer without creating item.

**Validates: Requirements 6.1-6.6**

### Property 4: Conversation Item Consistency

*For any* sequence of `conversation.item.create`, `conversation.item.delete`, and `conversation.item.truncate` operations, the conversation state SHALL be consistent: items are ordered correctly, deletions remove items, truncations preserve partial content.

**Validates: Requirements 7.1-7.8**

### Property 5: Response Lifecycle Events

*For any* response generation, the Realtime API SHALL emit events in the correct order: `response.created` → (`response.output_item.added` → content deltas → `response.output_item.done`)* → `response.done`. Cancellation SHALL emit `response.cancelled` and stop further events.

**Validates: Requirements 8.1-8.7, 12.1-12.6**

### Property 6: Audio Format Round-Trip

*For any* audio data in a supported format (pcm16, g711_ulaw, g711_alaw), encoding to base64 then decoding SHALL produce equivalent audio data. Converting between formats SHALL preserve audio fidelity within acceptable tolerance.

**Validates: Requirements 18.1-18.4**

### Property 7: Event Structure Validation

*For any* server event emitted by the Realtime API, the event structure SHALL match the OpenAI specification exactly: all required fields present, correct types, correct field names.

**Validates: Requirements 9.1-9.4, 10.1-10.6, 11.1-11.3, 13.1-13.5, 14.1-14.3, 15.1-15.4, 16.1-16.2**

### Property 8: Event ID Uniqueness

*For any* sequence of server events within a session, all `event_id` values SHALL be unique. Event IDs SHALL be generated using a consistent format.

**Validates: Requirements 25.1-25.4**

### Property 9: Tenant Isolation

*For any* two tenants A and B, tenant A SHALL NOT be able to access, view, or modify sessions, conversations, or data belonging to tenant B. All queries SHALL be scoped to the authenticated tenant.

**Validates: Requirements 24.1-24.5**

### Property 10: Error Event Structure

*For any* error condition (invalid JSON, unknown event type, authentication failure, server error), the Realtime API SHALL emit an error event with correct structure: `type`, `code`, `message`, and optionally `param` and `event_id`.

**Validates: Requirements 17.1-17.5**

## Error Handling

### WebSocket Error Codes

| Code | Name | Description |
|------|------|-------------|
| 1000 | Normal Closure | Session completed normally |
| 1008 | Policy Violation | Authentication failed |
| 1011 | Internal Error | Server error |
| 4001 | Authentication Failed | Invalid or missing token |
| 4002 | Invalid Tenant | Tenant not found or invalid |
| 4003 | Tenant Suspended | Tenant account suspended |
| 4029 | Rate Limited | Too many requests |

### Error Event Types

| Type | Description |
|------|-------------|
| `invalid_request_error` | Client sent invalid data |
| `server_error` | Internal server error |
| `authentication_error` | Authentication failed |

### Error Handling Strategy

1. **Validation Errors**: Return `error` event with `invalid_request_error` type
2. **Authentication Errors**: Close connection with code 4001 or return `error` event
3. **Rate Limiting**: Return `error` event with rate limit info, optionally close with 4029
4. **Server Errors**: Log error, return sanitized `error` event with `server_error` type
5. **Unknown Events**: Return `error` event with descriptive message, continue connection

## Testing Strategy

### Dual Testing Approach

The implementation requires both unit tests and property-based tests for comprehensive coverage:

- **Unit tests**: Verify specific examples, edge cases, and error conditions
- **Property tests**: Verify universal properties across all valid inputs

### Property-Based Testing Configuration

- **Library**: `hypothesis` for Python
- **Minimum iterations**: 100 per property test
- **Tag format**: `Feature: openai-realtime-api-clone, Property {number}: {property_text}`

### Test Categories

1. **Authentication Tests**
   - Valid token authentication (query param and header)
   - Invalid token rejection
   - Expired token rejection
   - Ephemeral token creation and validation

2. **Session Tests**
   - Session creation with various configurations
   - Session update validation
   - Session termination

3. **Audio Buffer Tests**
   - Append/commit/clear sequences
   - Buffer size limits
   - Audio format conversion

4. **Conversation Tests**
   - Item CRUD operations
   - Item ordering
   - Truncation behavior

5. **Response Tests**
   - Response lifecycle events
   - Response cancellation
   - Streaming behavior

6. **Event Tests**
   - Event structure validation
   - Event ID uniqueness
   - Event ordering

7. **Multi-Tenancy Tests**
   - Tenant isolation
   - Cross-tenant access prevention

### Example Property Test

```python
# Feature: openai-realtime-api-clone, Property 8: Event ID Uniqueness
@given(st.lists(st.sampled_from(EVENT_TYPES), min_size=1, max_size=100))
@settings(max_examples=100)
def test_event_id_uniqueness(event_types: List[str]):
    """
    For any sequence of server events within a session,
    all event_id values SHALL be unique.
    """
    session = create_test_session()
    event_ids = set()
    
    for event_type in event_types:
        event = emit_event(session, event_type)
        assert event.event_id not in event_ids, f"Duplicate event_id: {event.event_id}"
        event_ids.add(event.event_id)
```
