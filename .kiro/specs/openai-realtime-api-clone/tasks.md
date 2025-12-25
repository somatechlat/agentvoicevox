# Implementation Plan: OpenAI Realtime API Clone

## Overview

This implementation plan creates a 100% OpenAI Realtime API compatible WebSocket and REST API layer using Django 5.1+, Django Ninja, Django Channels, and Django ORM. The implementation integrates with the existing AgentVoiceBox multi-tenant infrastructure.

## Tasks

- [-] 1. Create Django app structure and models
  - [-] 1.1 Create `realtime` Django app with models
    - Create `backend/apps/realtime/` app structure
    - Implement `RealtimeSession`, `Conversation`, `ConversationItem`, `Response` models
    - Add tenant scoping via `TenantScopedModel`
    - Create database migrations
    - _Requirements: 3.1-3.12, 19.1-19.6, 20.1-20.7_

  - [x] 1.2 Create Pydantic schemas for all events
    - Implement all client event schemas (9 event types)
    - Implement all server event schemas (28+ event types)
    - Implement configuration schemas (SessionConfig, TurnDetection, Tool, etc.)
    - _Requirements: 5.1-5.4, 6.1-6.6, 7.1-7.8, 8.1-8.7, 9.1-9.4, 10.1-10.6, 11.1-11.3, 12.1-12.6, 13.1-13.5, 14.1-14.3, 15.1-15.4, 16.1-16.2, 17.1-17.5_

  - [ ] 1.3 Write property test for session configuration validation
    - **Property 2: Session Configuration Validation**
    - **Validates: Requirements 3.1-3.12**

- [ ] 2. Implement ephemeral token service
  - [ ] 2.1 Create token service with Redis storage
    - Implement `EphemeralTokenService` class
    - Store tokens in Redis with TTL
    - Generate secure random tokens
    - Implement token validation and revocation
    - _Requirements: 2.1-2.5_

  - [ ] 2.2 Write property test for authentication validation
    - **Property 1: Authentication Validation**
    - **Validates: Requirements 1.2, 1.3, 1.4, 2.4, 2.5**

- [ ] 3. Checkpoint - Verify models and token service
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 4. Implement REST API endpoints
  - [ ] 4.1 Create Django Ninja router for `/v1/realtime/*`
    - Implement `POST /v1/realtime/sessions` - create session with ephemeral token
    - Implement `GET /v1/realtime/sessions` - list sessions (admin)
    - Implement `GET /v1/realtime/sessions/{id}` - get session details
    - Implement `DELETE /v1/realtime/sessions/{id}` - terminate session
    - Add authentication via API key and JWT
    - _Requirements: 23.1-23.5, 24.1-24.5_

  - [ ] 4.2 Register router in Django Ninja API
    - Add router to main API configuration
    - Configure OpenAPI documentation
    - _Requirements: 23.1-23.5_

- [ ] 5. Implement WebSocket consumer
  - [ ] 5.1 Create `RealtimeConsumer` base structure
    - Implement connection handling with authentication
    - Support `?access_token={token}` query parameter
    - Support `Authorization: Bearer {token}` header
    - Support `OpenAI-Beta: realtime=v1` header
    - Emit `session.created` on successful connection
    - _Requirements: 1.1-1.6_

  - [ ] 5.2 Implement event routing and dispatching
    - Create event type to handler mapping
    - Implement JSON message parsing with validation
    - Handle unknown event types with error response
    - _Requirements: 17.4, 17.5_

  - [ ] 5.3 Implement session event handlers
    - Implement `session.update` handler
    - Emit `session.updated` on success
    - Emit `error` on validation failure
    - _Requirements: 5.1-5.4_

  - [ ] 5.4 Write property test for event structure validation
    - **Property 7: Event Structure Validation**
    - **Validates: Requirements 9.1-9.4, 10.1-10.6, 11.1-11.3, 13.1-13.5, 14.1-14.3, 15.1-15.4, 16.1-16.2**

- [ ] 6. Checkpoint - Verify WebSocket connection and session events
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 7. Implement audio buffer service
  - [ ] 7.1 Create `AudioService` for buffer management
    - Implement audio buffer storage in Redis
    - Implement `append_audio` method
    - Implement `commit_buffer` method (creates conversation item)
    - Implement `clear_buffer` method
    - Support 15 MiB max per append
    - _Requirements: 6.1-6.6_

  - [ ] 7.2 Implement audio format conversion
    - Implement PCM16 (24kHz, mono, little-endian) support
    - Implement G.711 μ-law (8kHz) support
    - Implement G.711 A-law (8kHz) support
    - Implement base64 encoding/decoding
    - _Requirements: 18.1-18.4_

  - [ ] 7.3 Implement audio buffer event handlers
    - Implement `input_audio_buffer.append` handler
    - Implement `input_audio_buffer.commit` handler
    - Implement `input_audio_buffer.clear` handler
    - Emit appropriate server events
    - _Requirements: 6.1-6.6_

  - [ ] 7.4 Write property test for audio buffer consistency
    - **Property 3: Audio Buffer Consistency**
    - **Validates: Requirements 6.1-6.6**

  - [ ] 7.5 Write property test for audio format round-trip
    - **Property 6: Audio Format Round-Trip**
    - **Validates: Requirements 18.1-18.4**

- [ ] 8. Implement conversation service
  - [ ] 8.1 Create `ConversationService` for item management
    - Implement conversation creation
    - Implement item creation with position ordering
    - Implement item deletion
    - Implement item truncation
    - Support all item types (message, function_call, function_call_output)
    - _Requirements: 7.1-7.8, 19.1-19.6_

  - [ ] 8.2 Implement conversation event handlers
    - Implement `conversation.item.create` handler
    - Implement `conversation.item.delete` handler
    - Implement `conversation.item.truncate` handler
    - Emit appropriate server events
    - _Requirements: 7.1-7.8, 10.1-10.6_

  - [ ] 8.3 Write property test for conversation item consistency
    - **Property 4: Conversation Item Consistency**
    - **Validates: Requirements 7.1-7.8**

- [ ] 9. Checkpoint - Verify audio and conversation handling
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement VAD (Voice Activity Detection)
  - [ ] 10.1 Create VAD service integration
    - Implement server_vad mode
    - Implement semantic_vad mode (if available)
    - Support threshold, prefix_padding_ms, silence_duration_ms configuration
    - _Requirements: 4.1-4.6_

  - [ ] 10.2 Implement VAD event emission
    - Emit `input_audio_buffer.speech_started` on speech detection
    - Emit `input_audio_buffer.speech_stopped` on silence detection
    - Auto-create response when `create_response` is true
    - Handle response interruption when `interrupt_response` is true
    - _Requirements: 4.7-4.9_

- [ ] 11. Implement response service
  - [ ] 11.1 Create `ResponseService` for response generation
    - Implement response creation with configuration
    - Implement response cancellation
    - Track response status (in_progress, completed, cancelled, incomplete, failed)
    - Calculate and store usage statistics
    - _Requirements: 8.1-8.7, 20.1-20.7_

  - [ ] 11.2 Implement response streaming
    - Stream text deltas via `response.text.delta`
    - Stream audio deltas via `response.audio.delta`
    - Stream audio transcript via `response.audio_transcript.delta`
    - Stream function call arguments via `response.function_call_arguments.delta`
    - _Requirements: 13.1-13.5, 14.1-14.3, 15.1-15.4_

  - [ ] 11.3 Implement response lifecycle events
    - Emit `response.created` on start
    - Emit `response.output_item.added` for each output item
    - Emit `response.content_part.added` for each content part
    - Emit `response.done` on completion with usage stats
    - Emit `rate_limits.updated` with rate limit info
    - _Requirements: 12.1-12.6, 16.1-16.2_

  - [ ] 11.4 Implement response event handlers
    - Implement `response.create` handler
    - Implement `response.cancel` handler
    - _Requirements: 8.1-8.7_

  - [ ] 11.5 Write property test for response lifecycle events
    - **Property 5: Response Lifecycle Events**
    - **Validates: Requirements 8.1-8.7, 12.1-12.6**

- [ ] 12. Checkpoint - Verify response generation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement transcription service
  - [ ] 13.1 Integrate with STT worker for transcription
    - Connect to existing STT worker via Redis/Channels
    - Process committed audio buffers
    - Support configurable transcription model
    - _Requirements: 11.1-11.3_

  - [ ] 13.2 Implement transcription events
    - Emit `conversation.item.input_audio_transcription.completed` on success
    - Emit `conversation.item.input_audio_transcription.failed` on error
    - _Requirements: 11.1-11.3_

- [ ] 14. Implement noise reduction
  - [ ] 14.1 Add noise reduction configuration
    - Support `near_field` and `far_field` types
    - Apply noise reduction before VAD and model processing
    - Make configuration nullable to disable
    - _Requirements: 21.1-21.4_

- [ ] 15. Implement output audio buffer events
  - [ ] 15.1 Add output buffer event emission
    - Emit `output_audio_buffer.started` when streaming begins
    - Emit `output_audio_buffer.stopped` when streaming ends
    - Implement `output_audio_buffer.clear` handler
    - _Requirements: 22.1-22.4_

- [ ] 16. Implement event ID generation and ordering
  - [ ] 16.1 Create event ID generator
    - Generate unique event IDs for all server events
    - Use consistent format (e.g., `evt_xxx`)
    - Ensure uniqueness within session
    - _Requirements: 25.1-25.4_

  - [ ] 16.2 Write property test for event ID uniqueness
    - **Property 8: Event ID Uniqueness**
    - **Validates: Requirements 25.1-25.4**

- [ ] 17. Implement error handling
  - [ ] 17.1 Create comprehensive error handling
    - Implement error event emission for all error types
    - Include `type`, `code`, `message`, `param`, `event_id` in errors
    - Handle invalid JSON with `invalid_request_error`
    - Handle unknown events with descriptive error
    - Handle authentication errors appropriately
    - _Requirements: 17.1-17.5_

  - [ ] 17.2 Write property test for error event structure
    - **Property 10: Error Event Structure**
    - **Validates: Requirements 17.1-17.5**

- [ ] 18. Checkpoint - Verify all event types and error handling
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Implement multi-tenancy and isolation
  - [ ] 19.1 Add tenant scoping to all queries
    - Ensure all session queries are tenant-scoped
    - Ensure all conversation queries are tenant-scoped
    - Prevent cross-tenant data access
    - _Requirements: 24.1-24.5_

  - [ ] 19.2 Write property test for tenant isolation
    - **Property 9: Tenant Isolation**
    - **Validates: Requirements 24.1-24.5**

- [ ] 20. Wire WebSocket routing
  - [ ] 20.1 Add `/v1/realtime` route to WebSocket routing
    - Update `realtime/routing.py` with new route
    - Ensure authentication middleware is applied
    - _Requirements: 1.1_

  - [ ] 20.2 Update ASGI configuration
    - Ensure new consumer is properly registered
    - Verify routing works with existing consumers
    - _Requirements: 1.1_

- [ ] 21. Final checkpoint - Full integration testing
  - Ensure all tests pass, ask the user if questions arise.
  - Verify OpenAI SDK compatibility
  - Test with real audio streaming

## Notes

- All tasks including property-based tests are required for comprehensive coverage
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties using `hypothesis`
- Unit tests validate specific examples and edge cases
- All code uses Django 5.1+, Django Ninja, Django Channels, Django ORM exclusively
- No Flask, SQLAlchemy, or non-Django Python frameworks
