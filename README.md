<!-- WARNING: This documentation uses real data. Do NOT mock or use fake data. -->
# AgentVoiceBox Monorepo

This repository contains two primary components:

1) A public-facing blog/marketing site (Next.js) at the repo root.
2) The AgentVoiceBox platform stack (Django + Channels + Ninja + Next.js portal) under `ovos-voice-agent/AgentVoiceBoxEngine`.

## Repository Layout

- `src/`, `public/`, `_posts/`: Next.js blog site at the repo root.
- `ovos-voice-agent/AgentVoiceBoxEngine/`: Main platform (Django backend, Channels WebSockets, portal frontend, Docker stack).
- `ovos-voice-agent/`: Legacy sprint artifacts and experiments (not production, not wired to the Django stack).
- `docs/`, `documents/`: Project notes and marketing content.

## Quick Start

### Blog Site (Root)

```bash
npm install
npm run dev
```

The blog reads Markdown posts from `/_posts`.

### AgentVoiceBox Platform (Docker)

```bash
cd ovos-voice-agent/AgentVoiceBoxEngine

docker compose -p agentvoicebox up -d
```

Default service URLs (from `ovos-voice-agent/AgentVoiceBoxEngine/docker-compose.yml`):

- Portal Frontend: http://localhost:65027
- Django API: http://localhost:65020/api/v2
- WebSockets (Channels): ws://localhost:65020/ws/v2/...
- Keycloak: http://localhost:65024
- Grafana: http://localhost:65029

For local env overrides, see `ovos-voice-agent/AgentVoiceBoxEngine/backend/.env.example`.

## Documentation

- Platform docs: `ovos-voice-agent/AgentVoiceBoxEngine/README.md`
- Local development: `ovos-voice-agent/AgentVoiceBoxEngine/docs/LOCAL_DEVELOPMENT.md`
- API reference: `/api/v2/docs` served by Django Ninja when the stack is running.
