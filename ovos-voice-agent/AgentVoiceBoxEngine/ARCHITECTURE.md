# AgentVoiceBox Architecture Specification

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11
**Source of truth:** Running source code in `backend/`, `portal-frontend/`, and `docker-compose.yml`.

## 1. Introduction
### 1.1 Purpose
This document describes the implemented AgentVoiceBox architecture using ISO-style organization. It replaces older claims that referenced `/v1/voice/ovos/*`, Next.js, React, Flask, FastAPI, or SQLAlchemy as active architecture.

### 1.2 Scope
The active system is a Django/Lit/OVOS platform with REST, WebSocket, portal UI, tenant administration, voice configuration, and optional integrations.

## 2. System Context
External actors and systems:
- Browser users access the Lit portal.
- API clients access Django Ninja REST endpoints under `/api/v2`.
- WebSocket clients access Django Channels endpoints under `/ws/v2` or the experimental `/ws/v1/realtime` gateway.
- OVOS services communicate through the OVOS message bus.
- Optional services include Keycloak, Vault, Temporal, Lago, Kafka, OPA, Prometheus, and Grafana.

## 3. Logical Architecture
### 3.1 Frontend Layer
The frontend is a Vite/Lit 3 TypeScript app in `portal-frontend/`. It defines custom elements for login, setup, dashboard, settings, voice management, voice cloning, and playground workflows.

### 3.2 API Layer
The REST API is a single Django Ninja `NinjaAPI` instance in `backend/apps/core/api.py`. Django mounts it at `/api/v2/`.

### 3.3 WebSocket Layer
Django Channels is configured in `backend/config/asgi.py` and `backend/realtime/routing.py`. Implemented routes are:
- `/ws/v2/events`
- `/ws/v2/sessions/{session_id}`
- `/ws/v2/stt/transcription`
- `/ws/v2/tts/stream`
- `/ws/v1/realtime`

### 3.4 Domain Layer
Domain behavior is split across Django apps: tenants, users, projects, API keys, sessions, billing, voice, themes, audit, notifications, workflows, realtime, and MCP.

### 3.5 Voice Integration Layer
`apps.voice.ovos_bridge.OVOSConfigBridge` sends configuration patches and session configuration to OVOS. `apps.realtime.ovos_bus.OVOSIntelligenceBridge` registers session callbacks and forwards utterances to the OVOS bus.

### 3.6 Data Layer
PostgreSQL stores tenant, user, project, API key, session, billing, voice, theme, audit, notification, workflow-adjacent, and realtime models. Redis supports cache, sessions, Channels, rate limiting, and workflow-related queues where configured.

## 4. Deployment Architecture
The primary local stack is `docker-compose.yml`:
- `postgres`: `65004:5432`
- `redis`: `65005:6379`
- `django-api`: `65020:8000`
- `portal-frontend`: `65027:65027`
- `ovos-bus`: `65081:8181`
- `ovos-core`, `ovos-listener`, `ovos-audio`: internal network services

## 5. Architectural Constraints
- REST APIs must use Django Ninja.
- WebSockets must use Django Channels.
- UI must use Lit 3 Web Components.
- Database access must use Django ORM.
- The primary compose stack targets a 10 GB memory budget.
- Documentation must not describe optional or planned services as required runtime behavior unless the code wires them into the active stack.

## 6. Known Architecture Gaps
- `/ws/v1/realtime` is partial and experimental; it is not documented as a full OpenAI Realtime implementation.
- Some optional deployment manifests include workers or external services not present in the primary compose stack.
- Several older planning documents were aspirational and have been superseded by this code-aligned baseline.
