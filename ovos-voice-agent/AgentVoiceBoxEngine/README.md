<p align="center">
  <img src="https://raw.githubusercontent.com/OpenVoiceOS/ovos-media/main/logos/ovos-logo.png" alt="AgentVoiceBox Logo" width="200"/>
</p>

<h1 align="center">AgentVoiceBox</h1>

<p align="center">
  <strong>Sovereign Voice AI Platform (Powered by OVOS)</strong>
</p>

---

## What is AgentVoiceBox?

AgentVoiceBox is a production-hardened, standalone voice AI gateway built on the OpenVoiceOS (OVOS) intelligence bus. It provides a drop-in, sovereign replacement for external voice APIs, managed through a comprehensive Lit 3 administration portal and orchestrated via a Django Ninja backend.

This cluster enforces strict **10 GB memory limits** and isolates all traffic within the `65000-65099` port range.

## Architecture (Production Hardened)

```
┌─────────────────────────────────────────────────────────────────┐
│                 Portal Frontend (Admin UX & i18n)               │
│                  (Lit 3 + Vite, port 65027, 512MB)              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Django API Gateway (Ninja)                   │
│          REST: /v1/voice/ovos/* (port 65020, 2GB)               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OVOS Message Bus                         │
│                  (Intelligence Backbone, 256MB)                 │
└─────────────────────────────────────────────────────────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
  ┌─────────────────┐ ┌───────────────┐ ┌─────────────────┐
  │   OVOS Core     │ │ OVOS Listener │ │   OVOS Audio    │
  │ (Intent, 2GB)   │ │  (STT, 1.5GB) │ │   (TTS, 1.5GB)  │
  └─────────────────┘ └───────────────┘ └─────────────────┘
```

## Key Components

- **Django REST API (Ninja)**: Provides synchronous config patching and voice cloning bridges.
- **Portal Frontend**: Lit 3 app providing exhaustive configuration of `mycroft.conf` (Skills, Audio, VAD) with native i18n (English/Spanish).
- **OVOS Engine**: Complete sovereign stack (Bus, Core, Listener, Audio) operating entirely offline.
- **Storage**: PostgreSQL (1.5GB) and Redis (256MB) for agent state and cache persistence.

## Quick Start (Docker)

```bash
cd ovos-voice-agent/AgentVoiceBoxEngine

docker compose -p agentvoicebox up -d
```

### Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| **Portal Frontend** | http://localhost:65027 | Administration UI, Voice Cloning, Settings |
| **Django API** | http://localhost:65020/api/v2 | Agent API & Gateway endpoints |
| **API Docs (Ninja)** | http://localhost:65020/api/v2/docs | Swagger UI |
| **OVOS Bus** | ws://localhost:65081 | Raw websocket event bus |

## Configuration & Standards

- **Memory:** The cluster must not exceed 10GB total RAM. Swap memory is matched to container memory limits to prevent thrashing (`memswap_limit = memory`).
- **Frameworks:** Strictly **Django Ninja** for APIs and **Lit 3** for web components. No FastAPI, no Alpine.js.
- **Documentation:** See `SRS_ISO_AgentVoiceBox.md` for the complete ISO/IEC 29148:2018 Software Requirements Specification.
- **Agent Rules:** See `agent.md` for mandatory Vibe Coding compliance directives.
