# AgentVoiceBox - Development Tasks

**ISO/IEC 29148:2018 Compliant Task Registry**  
**Version**: 1.0.0  
**Last Updated**: 2026-01-12

---

## Priority Legend

| Priority | Description |
|----------|-------------|
| P0 | Critical - Blocks production |
| P1 | High - Required for release |
| P2 | Medium - Should complete this sprint |
| P3 | Low - Nice to have |

---

## Security Tasks

### SEC-001: Billing Webhook Signature Verification
- **Priority**: P1
- **Source**: `apps/billing/api.py:236`
- **Description**: Implement webhook signature verification for Lago billing webhooks to prevent unauthorized webhook injection attacks.
- **Acceptance Criteria**: 
  - Verify X-Lago-Signature header using HMAC-SHA256
  - Reject webhooks with invalid signatures with 401 response
  - Log failed verification attempts to audit trail

---

## Authorization Tasks

### AUTH-001: Audit API Permission Checks
- **Priority**: P1
- **Source**: `apps/audit/api.py:101,132,148,171,195,218,231`
- **Description**: Implement explicit permission checks for all Audit API endpoints using decorator-based role enforcement.
- **Endpoints Requiring Checks**:
  - `get_audit_logs` - Requires OPERATOR role
  - `get_audit_log_detail` - Requires OPERATOR role  
  - `export_audit_logs` - Requires ADMIN role
  - `get_audit_statistics` - Requires OPERATOR role
  - `purge_old_logs` - Requires ADMIN role
- **Acceptance Criteria**:
  - All endpoints enforce role-based access via `@require_role()` decorator
  - Unauthorized requests return 403 PermissionDeniedError

### AUTH-002: STT API Permission Checks
- **Priority**: P1
- **Source**: `apps/stt/api.py:37,56,83,109`
- **Description**: Implement explicit permission checks for all STT configuration endpoints.
- **Endpoints Requiring Checks**:
  - `get_stt_config` - Requires ADMIN or DEVELOPER role
  - `update_stt_config` - Requires ADMIN role
  - `get_stt_metrics` - Requires OPERATOR role
  - `test_stt` - Requires DEVELOPER role
- **Acceptance Criteria**:
  - All endpoints enforce role-based access via `@require_role()` decorator

### AUTH-003: LLM API Permission Checks
- **Priority**: P1
- **Source**: `apps/llm/api.py:37,71,128`
- **Description**: Implement explicit permission checks for all LLM configuration endpoints.
- **Endpoints Requiring Checks**:
  - `get_llm_config` - Requires ADMIN role
  - `update_llm_config` - Requires ADMIN role
  - `test_llm` - Requires DEVELOPER role
- **Acceptance Criteria**:
  - All endpoints enforce role-based access via `@require_role()` decorator

---

## Infrastructure Tasks

### CACHE-001: Tenant Cache Invalidation
- **Priority**: P2
- **Source**: `apps/core/cache.py:168-171`
- **Description**: Implement pattern-based cache invalidation for tenant data using django-redis raw connection.
- **Technical Approach**:
  ```python
  from django_redis import get_redis_connection
  conn = get_redis_connection("default")
  keys = conn.scan_iter(f"tenant:{tenant_id}:*")
  if keys:
      conn.delete(*keys)
  ```
- **Acceptance Criteria**:
  - `clear_tenant()` method properly invalidates all tenant-prefixed keys
  - Performance tested with 10,000+ keys

---

## Task Statistics

| Category | Count | Priority |
|----------|-------|----------|
| Security | 1 | P1 |
| Authorization | 3 | P1 |
| Infrastructure | 1 | P2 |
| **Total** | **5** | - |
