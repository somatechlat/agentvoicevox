# AgentVoiceBox Monorepo

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11
**Source of truth:** Code under `ovos-voice-agent/AgentVoiceBoxEngine`.

## 1. Purpose
This repository contains the AgentVoiceBox platform stack and supporting documentation. The active platform implementation is in `ovos-voice-agent/AgentVoiceBoxEngine`.

## 2. Implemented System Overview
AgentVoiceBox is implemented as:
- Django 5.1 + Django Ninja REST API at `/api/v2`.
- Django Channels WebSocket API at `/ws/v2/*` with an experimental OpenAI-like gateway at `/ws/v1/realtime`.
- Lit 3 + Vite portal frontend.
- PostgreSQL and Redis persistence/cache infrastructure.
- OVOS message-bus integration for voice configuration and voice event flow.

No root Next.js blog application is active in this repository.

## 3. Repository Layout
- `ovos-voice-agent/AgentVoiceBoxEngine/`: active platform source, Docker stack, frontend, backend, infrastructure, and SRS documents.
- `docs/`: supporting project notes and generated Sphinx source.
- `documents/`: marketing/reference material.

## 4. Local Quick Start
```bash
cd ovos-voice-agent/AgentVoiceBoxEngine
docker compose -p agentvoicebox up -d
```

Default service URLs from the primary compose file:
- Portal frontend: http://localhost:65027
- Django API: http://localhost:65020/api/v2
- API docs: http://localhost:65020/api/v2/docs
- WebSockets: ws://localhost:65020/ws/v2/...
- Experimental realtime gateway: ws://localhost:65020/ws/v1/realtime
- OVOS bus host port: ws://localhost:65081

## 5. Canonical Documentation
- Platform SRS: `ovos-voice-agent/AgentVoiceBoxEngine/docs/srs/AgentVoiceBox_SRS.md`
- Architecture: `ovos-voice-agent/AgentVoiceBoxEngine/ARCHITECTURE.md`
- Local development: `ovos-voice-agent/AgentVoiceBoxEngine/docs/LOCAL_DEVELOPMENT.md`
- Portal frontend: `ovos-voice-agent/AgentVoiceBoxEngine/portal-frontend/README.md`
- Infrastructure: `ovos-voice-agent/AgentVoiceBoxEngine/infra/README.md`

## 6. Documentation Control
All documentation must match code. If a requirement, route, framework, or service is not implemented in code, it must be labeled planned, optional, or not implemented.
