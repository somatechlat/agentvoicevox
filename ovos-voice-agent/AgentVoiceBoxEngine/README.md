# AgentVoiceBox Documentation Baseline

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11
**Source of truth:** Repository source code under `ovos-voice-agent/AgentVoiceBoxEngine`
**Documentation style:** ISO/IEC/IEEE 29148-style structure for clarity; this repository does not claim external ISO certification.

## 1. Purpose
This document records the implemented AgentVoiceBox system as reflected by the code. Requirements, plans, and claims in this file are subordinate to the running implementation.

## 2. Implemented Product Scope
AgentVoiceBox is a Django-based voice AI platform with a Lit 3 administration frontend and OVOS message-bus integration.

Implemented runtime surfaces:
- REST API: Django Ninja mounted at `/api/v2/`.
- REST API documentation: `/api/v2/docs` and `/api/v2/openapi.json`.
- Health checks: `/health/` and `/health/ready/`.
- WebSockets: Django Channels routes under `/ws/v2/*` plus an experimental OpenAI-like gateway at `/ws/v1/realtime`.
- Frontend: Lit 3 + Vite application in `portal-frontend/`.
- Persistence/cache: PostgreSQL and Redis.
- Voice integration: OVOS message bus through `ovos-bus-client`.

## 3. Implemented Backend Modules
The active Django apps are:
- `apps.core`: API registration, middleware, exceptions, cache, permissions, health views.
- `apps.tenants`: tenant records, tenant settings, onboarding, tenant-scoped access.
- `apps.users`: custom user model, profile, user administration.
- `apps.projects`: project CRUD and voice configuration.
- `apps.api_keys`: API key lifecycle and validation.
- `apps.sessions`: voice session lifecycle and session events.
- `apps.billing`: usage events, invoices, billing alerts, Lago integration.
- `apps.voice`: voice personas, voice models, custom voices, wake words, OVOS configuration bridge.
- `apps.themes`: tenant theme management.
- `apps.audit`: audit log records and export.
- `apps.notifications`: notifications and preferences.
- `apps.workflows`: Temporal workflow definitions, activities, schedules, and management commands.
- `apps.realtime`: realtime sessions, conversations, responses, ephemeral tokens, OVOS bridge, and OpenAI-like schemas.
- `apps.mcp`: MCP tools and SSE/message endpoints.

## 4. Implemented API Baseline
All REST paths below are mounted under `/api/v2` unless noted otherwise.

Router prefixes:
- `/tenants`
- `/onboarding`
- `/users`
- `/user`
- `/projects`
- `/api-keys`
- `/sessions`
- `/billing`
- `/voice`
- `/voice-cloning`
- `/wake-words`
- `/themes`
- `/audit`
- `/notifications`
- `/admin/tenants`
- `/admin/users`
- `/admin`
- `/mcp`

WebSocket routes:
- `/ws/v2/events`
- `/ws/v2/sessions/{session_id}`
- `/ws/v2/stt/transcription`
- `/ws/v2/tts/stream`
- `/ws/v1/realtime`

## 5. Implemented Frontend Baseline
The frontend is not Next.js or React. It is a Lit 3/Vite TypeScript application with custom elements for layout, login, dashboard, setup, settings, voice management, voice cloning, and voice playground views. API access is centralized through TypeScript services in `portal-frontend/src/services`.

## 6. Operational Baseline
The primary compose file defines these local services:
- PostgreSQL on host port `65004`.
- Redis on host port `65005`.
- Django API on host port `65020`.
- Portal frontend on host port `65027`.
- OVOS message bus on host port `65081`.
- OVOS core, listener, and audio containers on the internal Docker network.

The primary compose file documents a 10 GB memory budget. This documentation states that budget as an implementation target, not as a verified runtime measurement.

## 7. Constraints
- New REST APIs must use Django Ninja.
- New WebSocket handlers must use Django Channels.
- New UI must use Lit 3 Web Components.
- New database models must use Django ORM and migrations.
- Documentation must not claim unsupported routes, frameworks, or production guarantees.

## 8. Known Gaps And Risks
- `/ws/v1/realtime` is an experimental OpenAI-like gateway, not a complete OpenAI Realtime API replacement.
- Some generated/cache/local files are present in the repository and should not be treated as source documentation.
- Some infrastructure manifests describe optional deployments that are not the primary local compose stack.
- Security-sensitive local files are present in the working tree; these should be reviewed separately before publication.
