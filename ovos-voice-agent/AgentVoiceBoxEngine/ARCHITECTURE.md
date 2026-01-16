# Architecture Overview

This document summarizes the **implemented** architecture of AgentVoiceBox and aligns it with the
authoritative requirements in the SRS documents under `docs/srs/`.

## 1. System Boundaries and Entry Points
- **REST API**: Django Ninja under `/api/v2` (see `backend/config/urls.py`).
- **WebSockets**: Django Channels under `/ws/v2` (see `backend/realtime/routing.py`).
- **Portal Frontend**: Lit 3 + Bun app under `portal-frontend/`.
- **Workers**: LLM/STT/TTS workers under `workers/` and workflow activities under `backend/apps/workflows/`.

## 2. Data Persistence (Postgres)
Core data models are implemented with Django ORM:
- Sessions: `backend/apps/sessions/models.py`
- Tenants and scoping: `backend/apps/tenants/models.py`
- Audit logs: `backend/apps/audit/models.py`
- Voice personas and TTS metadata: `backend/apps/voice/models.py`

Multi-tenant isolation is enforced via `TenantScopedModel` in `backend/apps/tenants/models.py`.

## 3. Event Streaming (Kafka, Optional)
Kafka is an **optional** integration (see `docs/srs/External_Services_Configuration_SRS.md`).
The standard topic names are defined in `backend/integrations/kafka.py`:
- `agentvoicebox.audit`
- `agentvoicebox.sessions`
- `agentvoicebox.billing`
- `agentvoicebox.notifications`
- `agentvoicebox.metrics`

Kafka is enabled/disabled via Django settings (`KAFKA.ENABLED`).

## 4. Policy Enforcement (OPA)
OPA integration is implemented in `backend/integrations/opa.py` and configured via settings
(`OPA.URL`, `OPA.DECISION_PATH`, `OPA.TIMEOUT_SECONDS`, `OPA.ENABLED`).

Current policy rules are defined in `policies/voice.rego` under the `voice` package. The file currently
includes allow rules for `/v1/realtime/client_secrets` and `/v1/realtime/sessions`; these endpoints are
part of the roadmap and are not the active API surface (see `ROADMAP.md`).

## 5. Observability
- **Metrics**: `/metrics` is exposed via `django_prometheus` (see `backend/config/urls.py` and
  `backend/config/settings/base.py`).
- **Logging**: Log level/format and Sentry DSN are configured in
  `backend/config/settings/settings_config.py`.

## 6. Deployment Notes
- The API gateway runs under Gunicorn with Uvicorn workers using `config.asgi:application`
  (see `backend/Dockerfile`).
- Environment defaults are defined in `settings.example.env` and `backend/.env.example`.
- For production secret management, refer to Vault requirements in
  `docs/srs/External_Services_Configuration_SRS.md`.

## 7. Authoritative References
- Core SRS: `docs/srs/AgentVoiceBox_SRS.md`
- MCP SRS: `docs/srs/MCP_Architecture_SRS.md`
- External services SRS: `docs/srs/External_Services_Configuration_SRS.md`
