<!-- WARNING: This documentation uses real data. Do NOT mock or use fake data. -->
# AgentVoiceBox Monorepo

## 1. Purpose
This repository contains the **AgentVoiceBox** platform stack (Django + Channels + Django Ninja + Lit 3/Bun)
and its supporting documentation. The production-ready stack lives under
`ovos-voice-agent/AgentVoiceBoxEngine`.

## 2. System Overview
**Active API surface**: `/api/v2` (REST) and `/ws/v2` (WebSockets).  
**OpenAI-compatible `/v1` endpoints**: not implemented in this codebase.

## 3. Repository Layout
- `ovos-voice-agent/AgentVoiceBoxEngine/`: Main platform (backend, frontend, Docker stack, infra, SRS).
- `ovos-voice-agent/`: Legacy sprint artifacts and experiments (not production, not wired to the Django stack).
- `docs/`: Project notes (architecture notes, compliance report, model selection).
- `documents/`: Marketing content.

## 4. Quick Start (Docker)
```bash
cd ovos-voice-agent/AgentVoiceBoxEngine
docker compose -p agentvoicebox up -d
```

Default service URLs (shared services + app stack):
- Portal Frontend: http://localhost:65027
- Django API: http://localhost:65020/api/v2
- WebSockets: ws://localhost:65020/ws/v2/...
- Keycloak: http://localhost:65006
- Prometheus: http://localhost:65011

Local overrides: `ovos-voice-agent/AgentVoiceBoxEngine/backend/.env.example`.

## 5. Canonical Documentation
- Platform overview: `ovos-voice-agent/AgentVoiceBoxEngine/README.md`
- Local development: `ovos-voice-agent/AgentVoiceBoxEngine/docs/LOCAL_DEVELOPMENT.md`
- OpenAPI (runtime): `http://localhost:65020/api/v2/docs`
- WebSocket reference: `ovos-voice-agent/AgentVoiceBoxEngine/docs/asyncapi.yaml`

## 6. Requirements (SRS)
- Core SRS: `ovos-voice-agent/AgentVoiceBoxEngine/docs/srs/AgentVoiceBox_SRS.md`
- MCP SRS: `ovos-voice-agent/AgentVoiceBoxEngine/docs/srs/MCP_Architecture_SRS.md`
- Configuration SRS: `ovos-voice-agent/AgentVoiceBoxEngine/docs/srs/Configuration_Settings_SRS.md`
- Developer Mode SRS: `ovos-voice-agent/AgentVoiceBoxEngine/docs/srs/Developer_Mode_Configuration_SRS.md`
- External Services SRS: `ovos-voice-agent/AgentVoiceBoxEngine/docs/srs/External_Services_Configuration_SRS.md`

## 7. Infrastructure References
- Infrastructure overview (standalone + SaaS): `ovos-voice-agent/AgentVoiceBoxEngine/infra/README.md`
- Docker deployment (shared services + app stack): `ovos-voice-agent/AgentVoiceBoxEngine/infra/docker/README.md`
- Lago billing cluster: `ovos-voice-agent/AgentVoiceBoxEngine/infra/lago-deployments/README.md`

## 8. Frontend
- Portal frontend: `ovos-voice-agent/AgentVoiceBoxEngine/portal-frontend/README.md`

## 9. Port Authority (Canonical)
These ports are the authoritative local defaults used across docs and compose files:
- Vault: `65003`
- PostgreSQL: `65004`
- Redis: `65005`
- Keycloak: `65006`
- Temporal: `65007`
- Django API: `65020`
- Portal Frontend: `65027`
- Observability stack: `65011` (Prometheus)
- Lago (isolated): `63690`
