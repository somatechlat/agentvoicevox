# Integrations

**Document status:** Code-aligned baseline
**Revision date:** 2026-07-13
**Source of truth:** `backend/config/settings/settings_config.py`, `backend/apps/*/integrations/`, `backend/integrations/`

## 1. Purpose
This document lists all external service integrations that the backend connects to, based on environment variables and import paths in the codebase.

## 2. Implemented Integrations

| Service | Config Variable(s) | Purpose |
|---|---|---|
| **Keycloak** | `keycloak_url`, `keycloak_realm`, `keycloak_client_id`, `keycloak_client_secret` | OAuth2/OIDC identity provider. JWT validation, user/group management, tenant RBAC. |
| **PostgreSQL** | `db_host`, `db_port`, `db_name`, `db_user`, `db_password` | Primary relational database. |
| **Redis** | `redis_url`, `redis_cache_db`, `redis_session_db`, `redis_channel_db` | Cache, session store, Django Channels layer, worker streams. |
| **Temporal** | `temporal_host`, `temporal_namespace`, `temporal_task_queue` | Durable workflow execution engine for voice sessions, billing sync, cleanup, onboarding. |
| **HashiCorp Vault** | `vault_addr`, `vault_token`, `vault_role_id`, `vault_secret_id`, `vault_mount_point` | Secrets management. |
| **OPA** | `opa_url`, `opa_decision_path`, `opa_timeout_seconds`, `opa_enabled` | Policy-as-code authorization decisions. |
| **Kafka** | `kafka_bootstrap_servers`, `kafka_consumer_group`, `kafka_enabled` | Event streaming (disabled by default). |
| **Lago** | `lago_api_url`, `lago_api_key`, `lago_webhook_secret` | Billing metering and subscription management. |
| **PayPal** | `paypal_client_id`, `paypal_client_secret`, `paypal_environment`, `paypal_webhook_id`, `paypal_enabled` | Payment processing (disabled by default). |
| **OVOS Bus** | `ovos_bus_host`, `ovos_bus_port` | OpenVoiceOS message bus for voice configuration and event flow. |
| **LLM Providers** | `groq_api_key`, `openai_api_key`, `groq_api_base`, `openai_api_base`, `ollama_base_url` | LLM inference for voice conversation. Provider priority configurable via `llm_provider_priority`. |
| **Sentry** | `sentry_dsn` | Error tracking and performance monitoring (optional). |
| **Prometheus** | `prometheus_enabled` | Metrics collection (enabled by default). |

## 3. Default Local Stack Ports
- PostgreSQL: 65004
- Redis: 65005
- Django API: 65020
- Portal Frontend: 65027
- OVOS Bus: 65081
- Keycloak: 65006

## 4. Known Gaps
- `apps.llm` and `apps.stt` Sphinx ghost modules were removed — no corresponding backend code exists for these as standalone Django apps.
- `apps.mcp` Sphinx module was added — it exists as a backend app.
- Vault, Temporal, OPA, Kafka, Lago, and Prometheus are referenced in settings but not all have docker-compose service definitions in the primary compose file.
