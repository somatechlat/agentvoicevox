# AgentVoiceBox Local Development Specification

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11
**Source of truth:** `docker-compose.yml`, `backend/`, and `portal-frontend/`.

## 1. Purpose
This document defines the local development baseline for the implemented AgentVoiceBox stack.

## 2. Prerequisites
- Docker and Docker Compose.
- Python tooling for backend-only development.
- Bun or Node-compatible tooling for the Vite/Lit frontend.

## 3. Primary Stack Startup
```bash
cd ovos-voice-agent/AgentVoiceBoxEngine
docker compose -p agentvoicebox up -d
```

## 4. Local Services
- Portal frontend: http://localhost:65027
- Django API: http://localhost:65020/api/v2
- API docs: http://localhost:65020/api/v2/docs
- API schema: http://localhost:65020/api/v2/openapi.json
- Health: http://localhost:65020/health/
- Readiness: http://localhost:65020/health/ready/
- WebSockets: ws://localhost:65020/ws/v2/...
- Experimental realtime gateway: ws://localhost:65020/ws/v1/realtime
- PostgreSQL: localhost:65004
- Redis: localhost:65005
- OVOS bus: localhost:65081

## 5. Backend Development
Backend source is under `backend/`. The Django API is registered in `apps.core.api`. Settings are split under `backend/config/settings`.

Useful commands from `backend/`:
```bash
python manage.py check
python manage.py migrate
pytest
```

## 6. Frontend Development
Frontend source is under `portal-frontend/` and uses Lit 3 with Vite.

Useful commands from `portal-frontend/`:
```bash
bun install
bun run dev
bun run build
bun run type-check
bun run test:e2e
```

## 7. Documentation Rules
If local behavior changes, update this file and the SRS in the same change. Do not document planned routes or services as implemented.
