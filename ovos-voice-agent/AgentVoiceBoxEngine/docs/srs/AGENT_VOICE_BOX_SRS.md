# Software Requirements Specification: AgentVoiceBox

**Document identifier:** AVB-SRS-CODE-BASELINE
**Version:** 2.0.0
**Revision date:** 2026-07-13
**Standard style:** ISO/IEC/IEEE 29148-style SRS
**Authority:** Current repository code. This document is not a certification claim.

## 1. Introduction
### 1.1 Purpose
This Software Requirements Specification defines the requirements represented by the current AgentVoiceBox implementation. It supersedes stale documentation that described unsupported frameworks, routes, or completeness claims.

### 1.2 Scope
AgentVoiceBox provides a multi-tenant SaaS platform for agent-facing voice
infrastructure with human administration. The system includes:
- Django Ninja REST API under `/api/v2`.
- Django Channels WebSockets under `/ws/v2` and an OpenAI Realtime-style
  compatible subset under `/ws/v1/realtime`.
- Lit 3 portal frontend.
- PostgreSQL and Redis data services.
- OVOS bus integration.
- Scoped API keys, tenant plans, quotas, rate limits, and billing usage records.
- Optional integrations for Keycloak, Vault, Temporal, Lago, Kafka, OPA, and observability.

### 1.3 Definitions
- **AVB:** AgentVoiceBox.
- **OVOS:** OpenVoiceOS.
- **REST API:** Django Ninja API mounted at `/api/v2`.
- **Realtime gateway:** Agent-facing WebSocket route `/ws/v1/realtime`.
- **Compatible subset:** A deliberately limited implementation of an external
  protocol shape. Unsupported behavior must fail clearly or be documented.
- **Tenant-scoped model:** Django ORM model that associates records with a tenant.

### 1.4 References
- `backend/apps/core/api.py`
- `backend/config/urls.py`
- `backend/config/asgi.py`
- `backend/realtime/routing.py`
- `backend/apps/*/models.py`
- `portal-frontend/src/**/*.ts`
- `docker-compose.yml`

## 2. Overall Description
### 2.1 Product Perspective
AgentVoiceBox is a standalone application stack that can run locally through Docker Compose. It is not a root Next.js blog, not a Flask application, and not a FastAPI application.
The product has two first-class interfaces over the same tenant-scoped domain:
human administration and agent runtime access.

### 2.2 Product Functions
The implemented product supports:
- Tenant management and tenant settings.
- User management and profile operations.
- Project management.
- API key management.
- API-key scopes for realtime, STT, TTS, voice cloning, voice catalog reads, MCP,
  billing reads, and admin operations.
- Plan and quota enforcement for agent-facing runtime access.
- Voice session lifecycle management.
- Billing usage, invoice, alert, and Lago webhook handling.
- Voice personas, voice models, custom voices, wake words, and OVOS configuration patching.
- Theme management.
- Audit logs.
- Notifications and preferences.
- Admin dashboard and admin tenant/user APIs.
- MCP SSE/message endpoints with JSON-RPC initialize, tools/list, and tools/call.
- Realtime session/conversation data models, WebSocket consumers, and a central
  voice orchestrator.

### 2.3 User Classes
- Platform administrator: manages tenants, users, and platform dashboard data.
- Tenant administrator: manages tenant resources, projects, voice settings, API keys, and usage.
- Agent operator: configures voices, API keys, quotas, and projects for agents.
- Agent/API client: integrates with REST, MCP, and realtime WebSocket endpoints.
- End user: interacts with configured voice sessions or portal views.

### 2.4 Operating Environment
- Python 3.12-compatible Django backend.
- PostgreSQL database.
- Redis cache/session/channel layer.
- Browser environment for Lit 3 frontend.
- Docker Compose for primary local deployment.

### 2.5 Constraints
- REST APIs shall use Django Ninja.
- WebSocket APIs shall use Django Channels.
- UI components shall use Lit 3.
- Data models shall use Django ORM.
- Claims of full external API compatibility shall not be made unless implemented and tested.

## 3. Specific Requirements
### 3.1 External Interface Requirements
#### 3.1.1 REST API
REQ-REST-001: The system shall mount the Django Ninja API at `/api/v2/`.
REQ-REST-002: The system shall expose OpenAPI documentation at `/api/v2/docs`.
REQ-REST-003: The system shall expose OpenAPI JSON at `/api/v2/openapi.json`.
REQ-REST-004: The system shall register routers for tenants, onboarding, users, user profile, projects, API keys, sessions, billing, voice, voice cloning, wake words, themes, audit, notifications, admin tenants, admin users, admin dashboard, and MCP.

#### 3.1.2 WebSocket API
REQ-WS-001: The system shall route event streaming at `/ws/v2/events`.
REQ-WS-002: The system shall route voice sessions at `/ws/v2/sessions/{session_id}`.
REQ-WS-003: The system shall route STT streaming at `/ws/v2/stt/transcription`.
REQ-WS-004: The system shall route TTS streaming at `/ws/v2/tts/stream`.
REQ-WS-005: The system shall expose an experimental OpenAI-like gateway at `/ws/v1/realtime`.
REQ-WS-006: The realtime gateway shall require API key authentication for agent
runtime access.
REQ-WS-007: The realtime gateway shall enforce API key scopes, tenant status,
plan capacity, and rate limits before performing voice work.

#### 3.1.3 User Interface
REQ-UI-001: The portal shall be implemented with Lit 3 custom elements.
REQ-UI-002: The portal shall use TypeScript services for API, authentication, administration, voice, formatting, permissions, serialization, JWT utilities, and i18n.
REQ-UI-003: The portal shall provide views for login, auth callback, dashboard, setup, settings, voice management, voice cloning, and voice playground.

### 3.2 Functional Requirements
REQ-FUNC-001: The system shall persist tenant, user, project, API key, session, billing, voice, theme, audit, notification, and realtime records through Django ORM models.
REQ-FUNC-002: The system shall apply tenant context through middleware and tenant-scoped models.
REQ-FUNC-003: The system shall support API key creation, update, revocation, rotation, deletion, and validation.
REQ-FUNC-003A: The system shall support agent-oriented API key scopes:
`realtime`, `stt`, `tts`, `voice_clone`, `voices_read`, `mcp`,
`billing_read`, and `admin`.
REQ-FUNC-004: The system shall support session creation, start, completion, termination, stats, and event retrieval.
REQ-FUNC-005: The system shall send OVOS configuration patch events through the OVOS bus bridge.
REQ-FUNC-006: The system shall support custom voice upload/list/get/delete/default routes under `/api/v2/voice-cloning`.
REQ-FUNC-007: The system shall support MCP SSE and JSON-RPC message endpoints
under `/api/v2/mcp`.
REQ-FUNC-008: The system shall centralize plan enforcement for realtime
sessions, custom voices, audio minutes, STT minutes, TTS minutes, input tokens,
output tokens, API calls, allowed providers, and rate-limit tier.
REQ-FUNC-009: The system shall provide a central voice orchestrator for
agent-facing text/audio session flow.

### 3.3 Nonfunctional Requirements
REQ-NFR-001: The primary compose stack should remain within the documented 10 GB memory target unless the compose file is deliberately revised.
REQ-NFR-002: Authentication shall require validated JWTs or API keys; auth bypass behavior is not part of the runtime.
REQ-NFR-003: Documentation shall label experimental or partial compatibility accurately.
REQ-NFR-004: Security-sensitive local files shall not be treated as public release artifacts.
REQ-NFR-005: Agent runtime operations shall fail closed when required providers
or scopes are not configured.

## 4. Verification
Implemented verification assets include pytest/property tests in `backend/tests`. Playwright E2E tests are configured in `portal-frontend/` but the `e2e/` and `__tests__/` directories contain no test files. Passing tests were not asserted by this documentation update unless explicitly run in a separate verification task.

## 5. Traceability
This SRS maps to code modules, not to aspirational planning documents. Historical planning documents were removed; the code and this SRS take precedence.
