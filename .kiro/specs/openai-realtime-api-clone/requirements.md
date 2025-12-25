# Requirements Document: OpenAI Realtime API Clone

## Introduction

This document specifies the requirements for implementing a **100% OpenAI Realtime API compatible** WebSocket and REST API layer in the AgentVoiceBox platform. The implementation MUST be a complete drop-in replacement for OpenAI's Realtime API, supporting all endpoints, events, parameters, and behaviors exactly as documented by OpenAI.

The implementation uses Django 5.1+, Django Ninja (REST API), Django Channels (WebSocket), and Django ORM exclusively.

## Glossary

- **Realtime_API**: The OpenAI-compatible real-time voice API providing bidirectional audio streaming
- **Session**: A WebSocket connection context maintaining conversation state, configuration, and audio buffers
- **Conversation**: A collection of items (messages, function calls) within a session
- **Item**: A message, function call, or function call output in the conversation
- **VAD**: Voice Activity Detection - automatic speech start/stop detection
- **Turn_Detection**: Server-side detection of when user speech starts and stops
- **Client_Event**: JSON message sent from client to server over WebSocket
- **Server_Event**: JSON message sent from server to client over WebSocket
- **Ephemeral_Token**: Short-lived token for WebSocket authentication (client_secret)
- **Audio_Buffer**: Temporary storage for incoming audio before processing

---

## Requirements

### Requirement 1: WebSocket Endpoint

**User Story:** As a developer, I want to connect to `/v1/realtime` via WebSocket, so that I can have real-time bidirectional audio conversations identical to OpenAI's API.

#### Acceptance Criteria

1. THE Realtime_API SHALL accept WebSocket connections at endpoint `/v1/realtime`
2. WHEN a WebSocket connection is initiated with query parameter `?access_token={token}` THEN the Realtime_API SHALL authenticate using the ephemeral token
3. WHEN a WebSocket connection is initiated with header `Authorization: Bearer {token}` THEN the Realtime_API SHALL authenticate using the bearer token
4. WHEN authentication fails THEN the Realtime_API SHALL close the connection with appropriate WebSocket close code
5. WHEN a valid connection is established THEN the Realtime_API SHALL emit a `session.created` server event
6. THE Realtime_API SHALL support the `OpenAI-Beta: realtime=v1` header for protocol versioning

---

### Requirement 2: Client Secrets / Ephemeral Tokens

**User Story:** As a developer, I want to create ephemeral tokens for browser clients, so that I can securely connect without exposing my API key.

#### Acceptance Criteria

1. THE Realtime_API SHALL provide endpoint `POST /v1/realtime/sessions` to create ephemeral tokens
2. WHEN creating a session THEN the Realtime_API SHALL return a `client_secret` object with `value` field containing the ephemeral token
3. WHEN creating a session with optional `session` configuration THEN the Realtime_API SHALL apply the configuration to the created session
4. THE ephemeral token SHALL have a configurable expiration time (default 60 seconds)
5. WHEN an expired ephemeral token is used THEN the Realtime_API SHALL reject the connection with 401 status

---

### Requirement 3: Session Configuration

**User Story:** As a developer, I want to configure session parameters, so that I can customize voice, modalities, and behavior.

#### Acceptance Criteria

1. THE Session SHALL support `modalities` array with values `["text"]` or `["text", "audio"]`
2. THE Session SHALL support `instructions` string for system prompt
3. THE Session SHALL support `voice` selection from: `alloy`, `ash`, `ballad`, `coral`, `echo`, `sage`, `shimmer`, `verse`
4. THE Session SHALL support `input_audio_format` with values: `pcm16`, `g711_ulaw`, `g711_alaw`
5. THE Session SHALL support `output_audio_format` with values: `pcm16`, `g711_ulaw`, `g711_alaw`
6. THE Session SHALL support `input_audio_transcription` configuration with `model` field
7. THE Session SHALL support `turn_detection` configuration (see Requirement 4)
8. THE Session SHALL support `tools` array for function calling
9. THE Session SHALL support `tool_choice` with values: `auto`, `none`, `required`, or function name
10. THE Session SHALL support `temperature` between 0.6 and 1.2 (default 0.8)
11. THE Session SHALL support `max_response_output_tokens` as integer or `"inf"`
12. WHEN `session.update` client event is received THEN the Realtime_API SHALL update session configuration and emit `session.updated`

---

### Requirement 4: Turn Detection (VAD)

**User Story:** As a developer, I want server-side voice activity detection, so that the system automatically detects when users start and stop speaking.

#### Acceptance Criteria

1. THE Turn_Detection SHALL support `type` values: `server_vad`, `semantic_vad`
2. THE Turn_Detection SHALL support `threshold` between 0.0 and 1.0 (default 0.5)
3. THE Turn_Detection SHALL support `prefix_padding_ms` (default 300ms)
4. THE Turn_Detection SHALL support `silence_duration_ms` (default 200ms)
5. THE Turn_Detection SHALL support `create_response` boolean (default true)
6. THE Turn_Detection SHALL support `interrupt_response` boolean (default true)
7. WHEN speech is detected in server_vad mode THEN the Realtime_API SHALL emit `input_audio_buffer.speech_started`
8. WHEN speech stops in server_vad mode THEN the Realtime_API SHALL emit `input_audio_buffer.speech_stopped`
9. WHEN `create_response` is true and speech stops THEN the Realtime_API SHALL automatically create a response

---

### Requirement 5: Client Events - Session

**User Story:** As a developer, I want to send session events, so that I can update configuration during the conversation.

#### Acceptance Criteria

1. WHEN client sends `session.update` event THEN the Realtime_API SHALL update session configuration
2. THE `session.update` event SHALL accept all session configuration fields except `voice` after first use
3. WHEN session is updated successfully THEN the Realtime_API SHALL emit `session.updated` with full effective configuration
4. IF session update fails THEN the Realtime_API SHALL emit `error` event with details

---

### Requirement 6: Client Events - Input Audio Buffer

**User Story:** As a developer, I want to stream audio to the server, so that my voice input is processed in real-time.

#### Acceptance Criteria

1. WHEN client sends `input_audio_buffer.append` with base64 `audio` THEN the Realtime_API SHALL append to the input buffer
2. THE `input_audio_buffer.append` event SHALL NOT trigger a server confirmation response
3. WHEN client sends `input_audio_buffer.commit` THEN the Realtime_API SHALL commit the buffer and emit `input_audio_buffer.committed`
4. WHEN client sends `input_audio_buffer.clear` THEN the Realtime_API SHALL clear the buffer and emit `input_audio_buffer.cleared`
5. WHEN buffer is committed THEN the Realtime_API SHALL create a user message item and emit `conversation.item.created`
6. THE audio buffer SHALL support up to 15 MiB per append event

---

### Requirement 7: Client Events - Conversation Items

**User Story:** As a developer, I want to manage conversation items, so that I can add context, delete items, and truncate audio.

#### Acceptance Criteria

1. WHEN client sends `conversation.item.create` THEN the Realtime_API SHALL add item to conversation and emit `conversation.item.created`
2. THE `conversation.item.create` SHALL support `previous_item_id` for insertion position
3. THE `conversation.item.create` SHALL support item types: `message`, `function_call`, `function_call_output`
4. THE message item SHALL support roles: `system`, `user`, `assistant`
5. WHEN client sends `conversation.item.delete` with `item_id` THEN the Realtime_API SHALL remove item and emit `conversation.item.deleted`
6. WHEN client sends `conversation.item.truncate` THEN the Realtime_API SHALL truncate assistant audio and emit `conversation.item.truncated`
7. THE `conversation.item.truncate` SHALL accept `item_id`, `content_index`, and `audio_end_ms`
8. WHEN client sends `conversation.item.retrieve` THEN the Realtime_API SHALL return item and emit `conversation.item.retrieved`

---

### Requirement 8: Client Events - Response

**User Story:** As a developer, I want to control response generation, so that I can trigger responses manually or cancel them.

#### Acceptance Criteria

1. WHEN client sends `response.create` THEN the Realtime_API SHALL generate a response via model inference
2. THE `response.create` SHALL support optional `response` configuration object
3. THE response configuration SHALL support `modalities`, `instructions`, `voice`, `output_audio_format`, `tools`, `tool_choice`, `temperature`, `max_output_tokens`
4. THE response configuration SHALL support `conversation` field with values `auto` or `none`
5. THE response configuration SHALL support `input` array for custom context
6. WHEN client sends `response.cancel` THEN the Realtime_API SHALL cancel in-progress response and emit `response.cancelled`
7. IF no response is in progress THEN `response.cancel` SHALL emit `error` event

---

### Requirement 9: Server Events - Session

**User Story:** As a developer, I want to receive session events, so that I know when sessions are created and updated.

#### Acceptance Criteria

1. WHEN WebSocket connection is established THEN the Realtime_API SHALL emit `session.created` with session object
2. THE `session.created` event SHALL include `session` object with `id`, `object`, `model`, and all configuration fields
3. WHEN session is updated THEN the Realtime_API SHALL emit `session.updated` with full session object
4. THE session object SHALL have `object` value `realtime.session`

---

### Requirement 10: Server Events - Conversation

**User Story:** As a developer, I want to receive conversation events, so that I can track conversation state.

#### Acceptance Criteria

1. WHEN session is created THEN the Realtime_API SHALL emit `conversation.created` with conversation object
2. THE conversation object SHALL have `id` and `object` value `realtime.conversation`
3. WHEN item is created THEN the Realtime_API SHALL emit `conversation.item.created` with `previous_item_id` and `item`
4. WHEN item is deleted THEN the Realtime_API SHALL emit `conversation.item.deleted` with `item_id`
5. WHEN item is truncated THEN the Realtime_API SHALL emit `conversation.item.truncated` with `item_id`, `content_index`, `audio_end_ms`
6. WHEN item is retrieved THEN the Realtime_API SHALL emit `conversation.item.retrieved` with `item`

---

### Requirement 11: Server Events - Input Audio Transcription

**User Story:** As a developer, I want to receive transcriptions of user audio, so that I can display what the user said.

#### Acceptance Criteria

1. WHEN input audio transcription is enabled and transcription completes THEN the Realtime_API SHALL emit `conversation.item.input_audio_transcription.completed`
2. THE transcription event SHALL include `item_id`, `content_index`, and `transcript`
3. IF transcription fails THEN the Realtime_API SHALL emit `conversation.item.input_audio_transcription.failed` with error details

---

### Requirement 12: Server Events - Response Lifecycle

**User Story:** As a developer, I want to receive response lifecycle events, so that I can track response generation progress.

#### Acceptance Criteria

1. WHEN response generation starts THEN the Realtime_API SHALL emit `response.created` with response object in `in_progress` status
2. WHEN new output item is added THEN the Realtime_API SHALL emit `response.output_item.added` with `response_id`, `output_index`, `item`
3. WHEN output item is complete THEN the Realtime_API SHALL emit `response.output_item.done`
4. WHEN content part is added THEN the Realtime_API SHALL emit `response.content_part.added`
5. WHEN content part is complete THEN the Realtime_API SHALL emit `response.content_part.done`
6. WHEN response is complete THEN the Realtime_API SHALL emit `response.done` with full response object including `usage` statistics

---

### Requirement 13: Server Events - Audio Streaming

**User Story:** As a developer, I want to receive audio deltas, so that I can play audio as it's generated.

#### Acceptance Criteria

1. WHEN audio is generated THEN the Realtime_API SHALL emit `response.audio.delta` with base64 `delta`
2. THE audio delta event SHALL include `response_id`, `item_id`, `output_index`, `content_index`
3. WHEN audio generation is complete THEN the Realtime_API SHALL emit `response.audio.done`
4. WHEN audio transcript is generated THEN the Realtime_API SHALL emit `response.audio_transcript.delta` with text `delta`
5. WHEN audio transcript is complete THEN the Realtime_API SHALL emit `response.audio_transcript.done` with full `transcript`

---

### Requirement 14: Server Events - Text Streaming

**User Story:** As a developer, I want to receive text deltas, so that I can display text as it's generated.

#### Acceptance Criteria

1. WHEN text is generated THEN the Realtime_API SHALL emit `response.text.delta` with `delta`
2. THE text delta event SHALL include `response_id`, `item_id`, `output_index`, `content_index`
3. WHEN text generation is complete THEN the Realtime_API SHALL emit `response.text.done` with full `text`

---

### Requirement 15: Server Events - Function Calling

**User Story:** As a developer, I want to receive function call events, so that I can execute functions and return results.

#### Acceptance Criteria

1. WHEN function call arguments are generated THEN the Realtime_API SHALL emit `response.function_call_arguments.delta` with JSON `delta`
2. THE function call event SHALL include `response_id`, `item_id`, `output_index`, `call_id`
3. WHEN function call is complete THEN the Realtime_API SHALL emit `response.function_call_arguments.done` with full `arguments`
4. THE function tool definition SHALL support `type`, `name`, `description`, `parameters` (JSON Schema)

---

### Requirement 16: Server Events - Rate Limits

**User Story:** As a developer, I want to receive rate limit updates, so that I can track my usage.

#### Acceptance Criteria

1. WHEN response starts THEN the Realtime_API SHALL emit `rate_limits.updated` with rate limit information
2. THE rate limit event SHALL include array of `rate_limits` with `name`, `limit`, `remaining`, `reset_seconds`

---

### Requirement 17: Server Events - Errors

**User Story:** As a developer, I want to receive error events, so that I can handle failures gracefully.

#### Acceptance Criteria

1. WHEN an error occurs THEN the Realtime_API SHALL emit `error` event
2. THE error event SHALL include `error` object with `type`, `code`, `message`, `param`, `event_id`
3. THE error types SHALL include: `invalid_request_error`, `server_error`, `authentication_error`
4. WHEN client sends invalid JSON THEN the Realtime_API SHALL emit error with `invalid_request_error` type
5. WHEN client sends unknown event type THEN the Realtime_API SHALL emit error with descriptive message

---

### Requirement 18: Audio Formats

**User Story:** As a developer, I want to use various audio formats, so that I can integrate with different audio systems.

#### Acceptance Criteria

1. THE Realtime_API SHALL support `pcm16` format (16-bit PCM, 24kHz, mono, little-endian)
2. THE Realtime_API SHALL support `g711_ulaw` format (G.711 μ-law, 8kHz)
3. THE Realtime_API SHALL support `g711_alaw` format (G.711 A-law, 8kHz)
4. THE audio data SHALL be base64 encoded in all events

---

### Requirement 19: Conversation Item Types

**User Story:** As a developer, I want to use different item types, so that I can build complex conversations.

#### Acceptance Criteria

1. THE Item SHALL support type `message` with roles `system`, `user`, `assistant`
2. THE Item SHALL support type `function_call` with `name`, `call_id`, `arguments`
3. THE Item SHALL support type `function_call_output` with `call_id`, `output`
4. THE message content SHALL support parts: `input_text`, `input_audio`, `text`, `audio`
5. THE Item SHALL have `id`, `type`, `status`, `role` (for messages), `content` fields
6. THE Item status SHALL be: `completed`, `incomplete`, `in_progress`

---

### Requirement 20: Response Object

**User Story:** As a developer, I want complete response objects, so that I can track response state and usage.

#### Acceptance Criteria

1. THE Response object SHALL have `id`, `object` (`realtime.response`), `status`, `status_details`
2. THE Response status SHALL be: `in_progress`, `completed`, `cancelled`, `incomplete`, `failed`
3. THE Response SHALL include `output` array of conversation items
4. THE Response SHALL include `usage` object with token counts
5. THE usage object SHALL include `total_tokens`, `input_tokens`, `output_tokens`
6. THE usage object SHALL include `input_token_details` with `cached_tokens`, `text_tokens`, `audio_tokens`
7. THE usage object SHALL include `output_token_details` with `text_tokens`, `audio_tokens`

---

### Requirement 21: Input Audio Noise Reduction

**User Story:** As a developer, I want noise reduction on input audio, so that VAD and model performance is improved.

#### Acceptance Criteria

1. THE Session SHALL support `input_audio_noise_reduction` configuration
2. THE noise reduction SHALL support `type` values: `near_field`, `far_field`
3. WHEN noise reduction is enabled THEN the Realtime_API SHALL filter audio before VAD and model processing
4. THE noise reduction configuration SHALL be nullable to disable

---

### Requirement 22: Output Audio Buffer Events (WebRTC)

**User Story:** As a developer using WebRTC, I want output buffer events, so that I can track audio playback state.

#### Acceptance Criteria

1. WHEN client sends `output_audio_buffer.clear` THEN the Realtime_API SHALL clear output buffer and emit `output_audio_buffer.cleared`
2. WHEN server starts streaming audio THEN the Realtime_API SHALL emit `output_audio_buffer.started`
3. WHEN server finishes streaming audio THEN the Realtime_API SHALL emit `output_audio_buffer.stopped`
4. THE output buffer events SHALL include `event_id`, `response_id`

---

### Requirement 23: REST API Endpoints

**User Story:** As a developer, I want REST endpoints for session management, so that I can create sessions and manage them via HTTP.

#### Acceptance Criteria

1. THE Realtime_API SHALL provide `POST /v1/realtime/sessions` to create sessions with ephemeral tokens
2. THE Realtime_API SHALL provide `GET /v1/realtime/sessions` to list active sessions (admin)
3. THE Realtime_API SHALL provide `GET /v1/realtime/sessions/{session_id}` to get session details
4. THE Realtime_API SHALL provide `DELETE /v1/realtime/sessions/{session_id}` to terminate session
5. THE Realtime_API SHALL provide `POST /v1/realtime/calls` for WebRTC SDP exchange (optional)

---

### Requirement 24: Authentication and Multi-Tenancy

**User Story:** As a platform operator, I want multi-tenant authentication, so that each tenant's sessions are isolated.

#### Acceptance Criteria

1. THE Realtime_API SHALL authenticate via API key in `Authorization: Bearer {key}` header
2. THE Realtime_API SHALL authenticate via ephemeral token in `?access_token={token}` query parameter
3. WHEN authenticated THEN the Realtime_API SHALL extract tenant context from the token
4. THE Realtime_API SHALL isolate sessions by tenant
5. THE Realtime_API SHALL enforce tenant rate limits and quotas

---

### Requirement 25: Event ID and Ordering

**User Story:** As a developer, I want event IDs, so that I can track and correlate events.

#### Acceptance Criteria

1. ALL server events SHALL include `event_id` field with unique identifier
2. THE client MAY include `event_id` in client events for correlation
3. WHEN error is caused by client event THEN the error SHALL include `event_id` of the causing event
4. THE events SHALL be delivered in order within a session

