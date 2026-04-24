# Architecture Overview

This document summarizes the **implemented** architecture of AgentVoiceBox and aligns it with the authoritative requirements in the `SRS_ISO_AgentVoiceBox.md` document.

## 1. System Boundaries and Entry Points
- **REST API Gateway**: Django Ninja under `/v1/voice/ovos/` (see `backend/apps/voice/api.py`). This acts as the synchronous bridge to the cognitive core.
- **Portal Frontend**: Lit 3 + Vite app under `portal-frontend/` providing administrative UI, Voice Cloning library, and system metrics.
- **Intelligence Bus**: OVOS Message Bus on port `8181` acting as the central nervous system.
- **Cognitive Engines**: OVOS Core (Intent mapping), OVOS Listener (STT), OVOS Audio (TTS/Playback).

## 2. Infrastructure Constraints (10GB Limit)
AgentVoiceBox is explicitly designed to operate entirely offline in a fully sovereign, multi-tenant capable local deployment.
- **Total Cluster Memory**: The total `docker-compose` cluster memory limit is strictly capped at **10 GB**.
- **Port Isolation**: All services must operate strictly within the `65000-65099` port range.
- **Swap Thrashing Prevention**: Memory swap limits are hard-locked to match memory allocations (`memswap_limit = memory`) to ensure deterministic performance.

## 3. Data Persistence (Postgres & Redis)
Core data models are implemented with Django ORM:
- Sessions: `backend/apps/sessions/models.py`
- Tenants and scoping: `backend/apps/tenants/models.py`
- Voice personas and TTS metadata: `backend/apps/voice/models.py`

PostgreSQL runs with isolated shared memory limits (`shm_size: 256mb`) for resilience. Redis operates as the caching and session backend.

## 4. OVOS Configuration Bridge
Instead of hardcoding settings, the API natively queries and patches the live `mycroft.conf` configuration via the `OVOSConfigBridge` singleton (`backend/apps/voice/ovos_bridge.py`). This allows the Lit 3 frontend to reconfigure Wake Words, Audio paths, and Skills synchronously on the fly.

## 5. UI/UX and Internationalization
The frontend is built using standard Lit Web Components. It features:
- A custom, lightweight reactive i18n module (`src/utils/i18n.ts`).
- Contextual help tooltips (`<ui-tooltip>`) across all configuration fields.
- A glassmorphic, SaaS-grade visual design.

## 6. Authoritative References
- Core ISO Document: `SRS_ISO_AgentVoiceBox.md`
- Agent Directives: `agent.md`
