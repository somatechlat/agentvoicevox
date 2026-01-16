# AgentVoiceBox Local Development (Django)

This guide covers running the Django-based AgentVoiceBox stack with Docker Compose.

## Prerequisites

- Docker Desktop 4.x+ with Docker Compose v2
- 10GB+ available RAM for Docker
- Git

## Quick Start

```bash
# Start shared services
cd ovos-voice-agent/AgentVoiceBoxEngine/infra/standalone
docker compose -p shared-services up -d

# Start application stack
cd ../../
docker compose -p agentvoicebox up -d
```

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Django API | http://localhost:65020 | REST and WebSocket entry point |
| API Docs | http://localhost:65020/api/v2/docs | Django Ninja OpenAPI |
| Portal Frontend | http://localhost:65027 | Customer portal UI |
| PostgreSQL | localhost:65004 | Database |
| Redis | localhost:65005 | Cache/session store |
| Keycloak | http://localhost:65006 | Identity provider |
| Lago | http://localhost:63690 | Billing engine (isolated cluster) |
| Vault | http://localhost:65003 | Secrets |
| Prometheus | http://localhost:65011 | Metrics |
| OPA | http://localhost:65030 | Policy engine (if running separately) |

## Health Checks

```bash
curl http://localhost:65020/health/
curl http://localhost:65020/health/ready/
```

## REST API

The REST API is served under `/api/v2`:

- `GET /api/v2/tenants`
- `GET /api/v2/users`
- `GET /api/v2/projects`
- `GET /api/v2/api-keys`
- `GET /api/v2/sessions`
- `GET /api/v2/voice`
- `GET /api/v2/themes`
- `GET /api/v2/notifications`
- `GET /api/v2/audit`
- `GET /api/v2/billing`

See the live API docs for full request/response schemas:

`http://localhost:65020/api/v2/docs`

## WebSocket Endpoints

- `ws://localhost:65020/ws/v2/events`
- `ws://localhost:65020/ws/v2/sessions/{session_id}`
- `ws://localhost:65020/ws/v2/stt/transcription`
- `ws://localhost:65020/ws/v2/tts/stream`

Auth uses Keycloak JWTs passed as `?token=` or `Authorization: Bearer`.

## Environment Configuration

The Django backend reads environment variables defined in:

- `backend/.env.example` (copy to `.env` for local overrides)

The Docker Compose file provides sane defaults for local dev; only override values if needed.

## Logs

```bash
# All services
docker compose -p agentvoicebox logs -f

# Django API only
docker compose -p agentvoicebox logs -f django-api
```

## Running Tests (Backend)

```bash
cd ovos-voice-agent/AgentVoiceBoxEngine/backend
pip install -r requirements.txt -r ../requirements-dev.txt
pytest -v
```
