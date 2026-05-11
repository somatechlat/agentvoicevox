# Docker Full-System Test TODO

**Document status:** actionable test readiness checklist
**Revision date:** 2026-05-11
**Source of truth:** current code, `docker-compose.yml`, `docker-compose.test.yml`, backend settings, and frontend package scripts.

## 1. Purpose
This checklist records the remaining work needed before the full AgentVoiceBox system can be tested reliably in Docker.

## 2. Current Blocking Issues
- [ ] Fix `docker-compose.test.yml` build contexts. The `gateway` service uses `context: .` and `dockerfile: Dockerfile`, but the implemented backend Dockerfile is `backend/Dockerfile`.
- [ ] Fix the `portal` test service. `Dockerfile.portal` does not exist; the implemented frontend Dockerfile is `portal-frontend/Dockerfile`.
- [ ] Decide whether the test compose should run the active full stack or a separate integration stack. The active full stack is `docker-compose.yml`; the test compose currently uses old service names (`gateway`, `portal`) and old ports (`25000`, `28000`).
- [ ] Align test environment variable names with `backend/config/settings/settings_config.py`. The settings loader expects names such as `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `DJANGO_SETTINGS_MODULE`, `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `REDIS_URL`, `KEYCLOAK_URL`, and related integration variables.
- [ ] Fix backend test database settings. `backend/config/settings/testing.py` currently points to `localhost:65004`, but the test compose Postgres service is available inside Docker as `postgres:5432` and from the host as `localhost:15432`.
- [ ] Fix the gateway health check path. The implemented Django health endpoint is `/health/`; the test compose checks `/health`.
- [ ] Confirm Keycloak health checks. The Keycloak service should explicitly enable health endpoints if the image requires `KC_HEALTH_ENABLED=true`.
- [ ] Decide whether `docker-compose.test.yml` should include OVOS bus/core/listener/audio. Full-system voice tests need them; backend-only integration tests do not.
- [ ] Decide whether test compose should include Vault, Temporal, OPA, Kafka, Lago, and Prometheus. Current Django settings and integrations reference these services, but the test compose does not define them.
- [ ] Remove or isolate committed local secrets and auth artifacts before treating Docker tests as release validation.

## 3. Backend Test Readiness
- [ ] From `backend/`, run `python manage.py check` with the same `DJANGO_SETTINGS_MODULE` used by Docker.
- [ ] Run `python manage.py migrate` against the Docker Postgres database.
- [ ] Run `pytest` from `backend/`.
- [ ] Run property tests under `backend/tests/test_property_*.py`.
- [ ] Verify `/health/`, `/health/ready/`, `/api/v2/docs`, and `/api/v2/openapi.json` inside the Docker network and from the host.
- [ ] Verify tenant, user, project, API key, session, billing, voice, theme, audit, notification, admin, and MCP routers are present in `/api/v2/openapi.json`.

## 4. Frontend Test Readiness
- [ ] From `portal-frontend/`, run `bun install`.
- [ ] Run `bun run type-check`.
- [ ] Run `bun run build`.
- [ ] Start the portal against the Docker API URL.
- [ ] Run Playwright smoke tests for login, setup, dashboard, settings, voice manager, voice cloning, and voice playground.
- [ ] Verify the frontend uses the correct API base URL: `http://localhost:65020` for the primary local stack.

## 5. Docker Stack Test Sequence
- [ ] Clean old containers and volumes only after confirming no needed local data is present.
- [ ] Build the primary stack: `docker compose -p agentvoicebox build`.
- [ ] Start the primary stack: `docker compose -p agentvoicebox up -d`.
- [ ] Wait for PostgreSQL, Redis, Django API, portal frontend, and OVOS bus to be healthy or reachable.
- [ ] Run backend migrations in the Django container.
- [ ] Run backend tests against the running Docker services.
- [ ] Run frontend type-check/build locally or in a frontend test container.
- [ ] Run Playwright E2E tests against `http://localhost:65027`.
- [ ] Capture logs for any failing services: `docker compose -p agentvoicebox logs --tail=200 <service>`.
- [ ] Shut down with `docker compose -p agentvoicebox down` after collecting results.

## 6. Full-System Voice Test Scope
- [ ] Verify OVOS bus connectivity from Django (`OVOS_BUS_HOST=ovos-bus`, `OVOS_BUS_PORT=8181`).
- [ ] Verify `GET /api/v2/voice/ovos/config` returns either live OVOS config or a clearly handled empty result.
- [ ] Verify `PATCH /api/v2/voice/ovos/config` emits `configuration.patch` without crashing.
- [ ] Verify `/ws/v2/events` connects.
- [ ] Verify `/ws/v2/sessions/{session_id}` connects for an authenticated or local-bypass test session.
- [ ] Verify `/ws/v1/realtime` sends `session.created` and handles invalid JSON with an error event.
- [ ] Label `/ws/v1/realtime` results as experimental until response generation and full event compatibility are implemented.

## 7. Documentation Completion Criteria
- [ ] Update this TODO when `docker-compose.test.yml` is repaired.
- [ ] Update `docs/LOCAL_DEVELOPMENT.md` with the final Docker test command sequence.
- [ ] Update the SRS if Docker test scope changes implemented interfaces.
- [ ] Record the exact test commands and pass/fail results in `TASKS.md`.
