# Security

**Document status:** Code-aligned baseline
**Revision date:** 2026-07-13
**Source of truth:** `backend/apps/core/permissions/`, `backend/realtime/middleware.py`, `docker-compose.yml`, `backend/config/settings/settings_config.py`

## 1. Purpose
This document describes the security mechanisms implemented in the codebase and known security issues that require remediation.

## 2. Implemented Security Mechanisms

### 2.1 Authentication
- **Keycloak OAuth2/OIDC** with PKCE (S256) for browser flows.
- JWT token validation via `keycloak_client.validate_token()` in `WebSocketAuthMiddleware`.
- Direct Access Grants (email/password) for programmatic login.
- Token auto-refresh 60 seconds before expiry.

### 2.2 Authorization
- **Role-based access control** via `apps.core.permissions` with roles: `viewer`, `operator`, `supervisor`, `tenant_admin`, `saas_admin`.
- **`@require_granular_role` decorator** enforced on all API endpoints (audit, voice, etc.).
- **OPA integration** for policy-as-code authorization (configurable, `opa_enabled` setting).
- **Plan enforcement** via `plan_enforcement_service.require_scope()` on MCP tools.
- **Tenant isolation** — queries scoped to `request.tenant` throughout the codebase.

### 2.3 API Key Management
- API key validation via `APIKeyService.validate_key()` with IP address logging.
- API key scopes and plan enforcement on WebSocket connections.

### 2.4 WebSocket Security
- `AllowedHostsOriginValidator` on WebSocket connections.
- JWT or API key authentication required on every WebSocket connection.

### 2.5 Audit Logging
- Immutable audit logs at `apps.audit` with actor, action, resource, old/new values.
- Filter by actor, action, resource type/date, with CSV export.
- Role-gated access: `operator` role required for viewing.

## 3. Known Security Issues (Must Remediate)

### 3.1 Hardcoded Secrets in docker-compose.yml
- `DJANGO_SECRET_KEY: shared_secure_2024` — committed to source control.
- `POSTGRES_PASSWORD: agentvoicebox` — default password in primary compose.
- `DJANGO_SECRET_KEY: local-compose-dev-secret-key-...` — committed dev secret.

### 3.2 Auth Token Key Inconsistency
- `auth-service.ts` stores tokens under `auth_tokens` in localStorage.
- `customVoicesApi` reads `localStorage.getItem('auth_token')` — different key.
- This will cause API calls to fail silently (no auth token found).

### 3.3 Keycloak Client Secret
- `keycloak_client_secret` is optional in settings but no fallback for production.
- No secret rotation mechanism implemented.

### 3.4 No Rate Limiting on WebSocket Auth
- `WebSocketAuthMiddleware` performs Keycloak token validation on every connection attempt with no rate limiting.

## 4. Recommended Actions
- Remove all hardcoded secrets from `docker-compose.yml` and use `.env` files.
- Fix `auth_token` → `auth_tokens` key mismatch in `customVoicesApi`.
- Add WebSocket authentication rate limiting.
- Rotate committed secrets before any production deployment.
