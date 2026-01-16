# External Services Configuration Matrix SRS

**Version**: 1.1.0  
**Date**: 2026-01-12  
**Compliance**: ISO/IEC 29148:2018

> [!IMPORTANT]
> **ZERO HARDCODED VARIABLES** - All service configuration MUST be via Django environment variables. Secrets MUST be stored in Vault.

---

## 1. Purpose

This document specifies the configuration and permission matrices for all external services integrated with AgentVoiceBox. All services MUST be synchronized with deployment settings (SANDBOX/LIVE modes).

---

## 2. External Services Inventory

| Service | Integration File | Purpose | Port Range | References |
|---------|-----------------|---------|------------|------------|
| **Keycloak** | `integrations/keycloak.py` (14KB) | Authentication & SSO | 65006 | 50+ |
| **Vault** | `integrations/vault.py` (24KB) | Secrets Management | 65003 | 200+ |
| **Lago** | `integrations/lago.py` (20KB) | Usage Billing | **63690-63699** | 50+ |
| **PayPal** | `integrations/paypal.py` (315 lines) | Payment Processing | External API | NEW |
| **Temporal** | `integrations/temporal.py` (9KB) | Workflow Orchestration | 65007 | 50+ |
| **OPA** | `integrations/opa.py` (8KB) | Policy Enforcement | 65030 | 40+ |
| **Kafka** | `integrations/kafka.py` (9KB) | Event Streaming | Optional | Optional |

---

## 3. Configuration Matrix by Deployment Mode

### 3.1 SANDBOX Mode (Development)

| Service | Status | Configuration | Notes |
|---------|--------|---------------|-------|
| **Keycloak** | BYPASSED | `KEYCLOAK_BYPASS=true` | Mock JWT tokens |
| **Vault** | BYPASSED | `VAULT_FAIL_FAST=false` | Env vars only |
| **Lago** | MOCKED | `LAGO_MOCK=true` | Fake billing responses |
| **Temporal** | DISABLED | `TEMPORAL_ENABLED=false` | Direct function calls |
| **OPA** | DISABLED | `OPA_ENABLED=false` | All policies pass |
| **Kafka** | DISABLED | `KAFKA_ENABLED=false` | In-memory events |

### 3.2 LIVE Mode (Development Production-Grade)

| Service | Status | Configuration | Notes |
|---------|--------|---------------|-------|
| **Keycloak** | ENABLED | Full auth flow | Local container 65006 |
| **Vault** | ENABLED | Full secrets | Local container 65003 |
| **Lago** | ENABLED | Full billing | Isolated cluster 63690 |
| **Temporal** | ENABLED | Full workflows | Local container 65007 |
| **OPA** | ENABLED | Full policies | Local container 65030 |
| **Kafka** | DISABLED | Not required SaaS | - |

### 3.3 Production Mode

| Service | Status | Configuration | Notes |
|---------|--------|---------------|-------|
| **Keycloak** | ENABLED | Cluster / Auth0 | External managed |
| **Vault** | ENABLED | Vault cluster | External managed |
| **Lago** | ENABLED | Lago Cloud | SaaS |
| **Temporal** | ENABLED | Temporal Cloud | SaaS |
| **OPA** | ENABLED | OPA cluster | Kubernetes sidecar |
| **Kafka** | OPTIONAL | MSK / Confluent | If event streaming needed |

---

## 4. Environment Variable Matrix

### 4.1 Keycloak Configuration

| Variable | Required | Default | SANDBOX | LIVE |
|----------|----------|---------|---------|------|
| `KEYCLOAK_URL` | ✅ | - | `http://localhost:8080` | `http://keycloak:8080` |
| `KEYCLOAK_REALM` | ✅ | - | `agentvoicebox` | `agentvoicebox` |
| `KEYCLOAK_CLIENT_ID` | ✅ | - | `agentvoicebox-backend` | `agentvoicebox-backend` |
| `KEYCLOAK_CLIENT_SECRET` | ❌ | - | - | `${VAULT}` |
| `KEYCLOAK_BYPASS` | ❌ | `false` | `true` | `false` |

### 4.2 Vault Configuration

| Variable | Required | Default | SANDBOX | LIVE |
|----------|----------|---------|---------|------|
| `VAULT_ADDR` | ✅ | - | - | `http://vault:8200` |
| `VAULT_TOKEN` | ❌ | - | - | `devtoken` |
| `VAULT_ROLE_ID` | ❌ | - | - | From AppRole |
| `VAULT_SECRET_ID` | ❌ | - | - | From AppRole |
| `VAULT_MOUNT_POINT` | ❌ | `secret` | `secret` | `secret` |
| `VAULT_FAIL_FAST` | ❌ | `true` | `false` | `true` |

### 4.3 Lago Configuration (Port Range 63690-63699)

| Variable | Required | Default | SANDBOX | LIVE |
|----------|----------|---------|---------|------|
| `LAGO_API_URL` | ✅ | - | - | `http://localhost:63690` |
| `LAGO_API_KEY` | ❌ | - | - | `${VAULT}` |
| `LAGO_WEBHOOK_SECRET` | ❌ | - | - | `${VAULT}` |
| `LAGO_MOCK` | ❌ | `false` | `true` | `false` |

> [!NOTE]
> Lago cluster is **COMPLETELY ISOLATED** from VoiceBox (65xxx range).
> Deployment: `infra/lago-deployments/docker-compose.yml`

### 4.4 PayPal Configuration

| Variable | Required | Default | SANDBOX | LIVE |
|----------|----------|---------|---------|------|
| `PAYPAL_CLIENT_ID` | ✅ | - | Sandbox ID | Production ID |
| `PAYPAL_CLIENT_SECRET` | ✅ | - | `${VAULT}` | `${VAULT}` |
| `PAYPAL_ENVIRONMENT` | ✅ | `sandbox` | `sandbox` | `live` |
| `PAYPAL_WEBHOOK_ID` | ❌ | - | - | `${VAULT}` |
| `PAYPAL_ENABLED` | ❌ | `false` | `false` | `true` |

### 4.5 Temporal Configuration

| Variable | Required | Default | SANDBOX | LIVE |
|----------|----------|---------|---------|------|
| `TEMPORAL_HOST` | ✅ | - | - | `temporal:7233` |
| `TEMPORAL_NAMESPACE` | ✅ | - | `agentvoicebox` | `agentvoicebox` |
| `TEMPORAL_TASK_QUEUE` | ✅ | - | `default` | `default` |
| `TEMPORAL_ENABLED` | ❌ | `true` | `false` | `true` |

### 4.6 OPA Configuration

| Variable | Required | Default | SANDBOX | LIVE |
|----------|----------|---------|---------|------|
| `OPA_URL` | ✅ | - | - | `http://opa:8181` |
| `OPA_DECISION_PATH` | ✅ | - | `/v1/data/agentvoicebox/allow` | Same |
| `OPA_TIMEOUT_SECONDS` | ❌ | `3` | `3` | `3` |
| `OPA_ENABLED` | ❌ | `true` | `false` | `true` |

### 4.7 Kafka Configuration

| Variable | Required | Default | SANDBOX | LIVE |
|----------|----------|---------|---------|------|
| `KAFKA_BOOTSTRAP_SERVERS` | ✅ | - | - | - |
| `KAFKA_CONSUMER_GROUP` | ✅ | - | - | - |
| `KAFKA_ENABLED` | ❌ | `false` | `false` | `false` |
| `KAFKA_SECURITY_PROTOCOL` | ❌ | `PLAINTEXT` | - | - |

---

## 5. Permission Matrix (Vault Policies)

### 5.1 Backend Service Policy

| Path | Permissions | Purpose |
|------|-------------|---------|
| `secret/data/agentvoicebox/backend/*` | read | App secrets |
| `secret/data/agentvoicebox/shared/*` | read | Shared secrets |
| `transit/encrypt/api-keys` | update | Encrypt API keys |
| `transit/decrypt/api-keys` | update | Decrypt API keys |
| `database/creds/backend` | read | Dynamic DB creds |

### 5.2 Keycloak Policy

| Path | Permissions | Purpose |
|------|-------------|---------|
| `secret/data/agentvoicebox/keycloak/*` | read | KC config |
| `database/creds/keycloak` | read | KC DB creds |
| `pki/issue/keycloak` | update | TLS certs |

### 5.3 Temporal Worker Policy

| Path | Permissions | Purpose |
|------|-------------|---------|
| `secret/data/agentvoicebox/temporal/*` | read | Temporal config |
| `secret/data/agentvoicebox/workers/*` | read | Worker secrets |
| `database/creds/temporal-worker` | read | Worker DB creds |

---

## 6. OPA Permission Policies

### 6.1 Decision Path Structure

```
/v1/data/agentvoicebox/allow
```

### 6.2 Input Context

```json
{
  "input": {
    "user": {
      "id": "uuid",
      "roles": ["admin", "user"],
      "tenant_id": "uuid"
    },
    "resource": {
      "type": "voice_session",
      "id": "uuid",
      "tenant_id": "uuid"
    },
    "action": "create"
  }
}
```

### 6.3 Policy Rules

| Resource | Action | Roles Required |
|----------|--------|----------------|
| `tenant` | read | any authenticated |
| `tenant` | update | `tenant_admin` |
| `user` | read | self or `admin` |
| `user` | delete | `admin` |
| `voice_session` | create | `user`, `admin` |
| `voice_session` | read | owner or `admin` |
| `billing` | read | `billing_admin`, `admin` |
| `billing` | update | `admin` |

---

## 7. Database Model Integrations

### 7.1 Tenant Model (apps/tenants/models.py)

| Field | External Service | Purpose |
|-------|-----------------|---------|
| `keycloak_group_id` | Keycloak | Tenant group membership |
| `billing_customer_id` | Lago/Stripe | External billing ID |

### 7.2 User Model (apps/users/models.py)

| Field | External Service | Purpose |
|-------|-----------------|---------|
| `keycloak_id` | Keycloak | SSO identity link |

### 7.3 Invoice Model (apps/billing/models.py)

| Field | External Service | Purpose |
|-------|-----------------|---------|
| `lago_invoice_id` | Lago | Invoice sync |
| `lago_event_id` | Lago | Usage event tracking |

---

## 8. Sync Status

| Source | External Service | Sync Type |
|--------|-----------------|-----------|
| User profile | Keycloak | Bidirectional |
| Usage events | Lago | Push (Django → Lago) |
| Invoices | Lago | Pull (Lago → Django) |
| Secrets | Vault | Pull on startup |
| Policies | OPA | Query per request |
| Workflows | Temporal | Bidirectional |

---

## 9. Implementation Tasks

| ID | Task | Priority |
|----|------|----------|
| EXT-001 | Add `KEYCLOAK_BYPASS` env var | P1 |
| EXT-002 | Add `LAGO_MOCK` env var | P1 |
| EXT-003 | Add `TEMPORAL_ENABLED` env var | P1 |
| EXT-004 | Update docker-compose with mode profiles | P1 |
| EXT-005 | Create Vault policy sync script | P2 |
| EXT-006 | Document OPA policy rules | P2 |

---

**Document Status**: READY FOR REVIEW
