# AgentVoiceBox Architecture Analysis Report

## Executive Summary

This report analyzes the AgentVoiceBox codebase to identify:
- Mock data and placeholder implementations
- Duplicate/overlapping code
- Legacy/broken components
- Technical debt

---

## 1. MOCK DATA INVENTORY

### 1.1 Portal Frontend Mock Data (CRITICAL)

**Location:** `portal-frontend/src/lib/api.ts`

The frontend has extensive mock data that bypasses real API calls when `DEV_BYPASS_AUTH=true`:

| Mock Object | Lines | Description |
|-------------|-------|-------------|
| `MOCK_DASHBOARD_DATA` | ~50 lines | Dashboard metrics, billing, health, activity |
| `MOCK_API_KEYS` | ~10 lines | 3 fake API keys |
| `MOCK_PLANS` | ~20 lines | 4 billing plans (Free, Starter, Pro, Enterprise) |
| `MOCK_INVOICES` | ~10 lines | 2 fake invoices |
| `MOCK_TEAM_ROLES` | ~5 lines | 4 roles (owner, admin, developer, viewer) |
| `MOCK_TEAM_MEMBERS` | ~10 lines | 3 fake team members |
| `MOCK_PROFILE` | ~10 lines | Organization profile |
| `MOCK_NOTIFICATIONS` | ~5 lines | Notification preferences |
| `MOCK_WEBHOOK_EVENTS` | ~10 lines | 9 webhook event types |
| `MOCK_WEBHOOKS` | ~10 lines | 1 fake webhook |

**Impact:** UI works in dev mode but doesn't connect to real backend APIs.

### 1.2 Portal Frontend Auth Mock

**Location:** `portal-frontend/src/contexts/AuthContext.tsx`

```typescript
const DEV_MOCK_USER: User = {
  id: 'dev-user-001',
  tenantId: '00000000-0000-0000-0000-000000000001',
  // ... all permissions granted
}
```

**Impact:** Bypasses Keycloak authentication entirely in dev mode.

### 1.3 Test Sample Data (ACCEPTABLE)

**Locations:**
- `tests/load/locustfile.py` - `SAMPLE_AUDIO_WAV`
- `tests/integration/test_worker_pipeline.py` - `SAMPLE_AUDIO_WAV`
- `tests/integration/test_e2e_speech_pipeline.py` - `SAMPLE_AUDIO_WAV`

**Status:** These are test fixtures, acceptable for testing purposes.

---

## 2. DUPLICATE/OVERLAPPING CODE

### 2.1 Service Singletons Pattern (GOOD)

Multiple services use the same singleton pattern:
- `get_lago_service()` - Lago billing
- `get_keycloak_service()` - Keycloak auth
- `get_payment_service()` - Payment processing
- `get_audit_service()` - Audit logging
- `get_degradation_service()` - Graceful degradation

**Status:** Consistent pattern, no duplication issue.

### 2.2 Redis Stream Constants (MINOR DUPLICATION)

**Locations:**
- `app/services/redis_streams.py` - Defines `GROUP_STT_WORKERS`, `GROUP_TTS_WORKERS`
- `workers/stt_worker.py` - Redefines `GROUP_STT_WORKERS`
- `workers/tts_worker.py` - Redefines `GROUP_TTS_WORKERS`
- `workers/llm_worker.py` - Defines `GROUP_LLM_WORKERS`

**Recommendation:** Centralize stream constants in a shared module.

### 2.3 Sample Audio Generation (MINOR DUPLICATION)

**Locations:**
- `tests/integration/test_user_flows.py` - `generate_test_audio_pcm16()`, `generate_test_audio_wav()`
- `tests/integration/test_complete_flows.py` - `generate_pcm16_audio()`, `generate_speech_like_audio()`

**Recommendation:** Create shared test utilities module.

---

## 3. LEGACY/REMOVED COMPONENTS

### 3.1 Admin UI (REMOVED - GOOD)

**Location:** `docker-compose.yml` comments

```yaml
# ADMIN UI - REMOVED (Replaced by portal-frontend SaaS Portal)
# The legacy static HTML admin-ui has been replaced by the full-featured
# portal-frontend Next.js application at port 25007.
```

**Status:** Properly documented removal.

### 3.2 Port 25011 (REMOVED)

Previously used for legacy admin-ui, now freed up.

---

## 4. OPTIONAL DEPENDENCIES (GRACEFUL DEGRADATION)

The codebase handles missing dependencies gracefully:

| Module | Dependency | Fallback |
|--------|------------|----------|
| `stt_worker.py` | `faster_whisper` | `FASTER_WHISPER_AVAILABLE = False` |
| `tts_worker.py` | `kokoro_onnx` | `KOKORO_AVAILABLE = False` |
| `llm_worker.py` | `httpx` | `HTTPX_AVAILABLE = False` |
| `api_key_service.py` | `argon2-cffi` | Fallback hashing |
| `jwt_validator.py` | `PyJWT` | `JWT_AVAILABLE = False` |
| `async_database.py` | `asyncpg` | `ASYNCPG_AVAILABLE = False` |
| `logging.py` | `python-json-logger` | `JSON_LOGGER_AVAILABLE = False` |

**Status:** Good defensive programming pattern.

---

## 5. TECHNICAL DEBT SUMMARY

### 5.1 HIGH PRIORITY - Frontend Mock Data

**Problem:** Portal frontend uses mock data in dev mode, not connected to real backend.

**Files Affected:**
- `portal-frontend/src/lib/api.ts` (all API functions)
- `portal-frontend/src/contexts/AuthContext.tsx`

**Solution:** 
1. Remove `DEV_BYPASS_AUTH` mode or make it test-only
2. Connect all API functions to real Portal API endpoints
3. Ensure Portal API is running for development

### 5.2 MEDIUM PRIORITY - Missing Portal Pages

**Problem:** Some pages are placeholders:
- `portal-frontend/src/app/admin/plans/page.tsx` - "Placeholder for subscription plan management"
- `portal-frontend/src/app/usage/page.tsx` - Falls back to mock data on error

**Solution:** Implement real functionality connected to backend.

### 5.3 MEDIUM PRIORITY - Stream Constants Duplication

**Problem:** Redis stream constants defined in multiple places.

**Solution:** Create `app/constants/streams.py` and import everywhere.

### 5.4 LOW PRIORITY - Test Utilities Duplication

**Problem:** Audio generation functions duplicated across test files.

**Solution:** Create `tests/utils/audio.py` with shared functions.

---

## 6. ARCHITECTURE HEALTH SCORE

| Category | Score | Notes |
|----------|-------|-------|
| Backend Services | 9/10 | Well-structured, proper patterns |
| Worker Services | 9/10 | Good graceful degradation |
| Portal API | 8/10 | Complete routes, needs more integration |
| Portal Frontend | 5/10 | Heavy mock data usage |
| Test Coverage | 7/10 | Good integration tests, some duplication |
| Documentation | 8/10 | Good README, architecture docs |

**Overall: 7.7/10**

---

## 7. RECOMMENDATIONS

### Immediate Actions (Before Production)

1. **Remove DEV_BYPASS_AUTH mode** or restrict to test environment only
2. **Connect frontend to real APIs** - Remove all mock data fallbacks
3. **Test full stack integration** - Ensure Keycloak → Portal API → Frontend flow works

### Short-term Improvements

4. **Centralize constants** - Create shared constants module for Redis streams
5. **Create test utilities** - Shared audio generation, mock factories
6. **Add missing admin pages** - Plans management, user management

### Long-term Improvements

7. **Add E2E tests** - Full user journey tests with real backend
8. **Implement WebSocket updates** - Real-time dashboard updates
9. **Add monitoring dashboards** - Grafana dashboards for portal metrics

---

## 8. FILES TO MODIFY

### Critical (Mock Data Removal)

```
portal-frontend/src/lib/api.ts
portal-frontend/src/contexts/AuthContext.tsx
portal-frontend/src/app/usage/page.tsx
```

### Medium (Placeholder Pages)

```
portal-frontend/src/app/admin/plans/page.tsx
portal-frontend/src/app/projects/page.tsx
portal-frontend/src/app/sessions/page.tsx
```

### Low (Code Cleanup)

```
workers/stt_worker.py (import from shared)
workers/tts_worker.py (import from shared)
workers/llm_worker.py (import from shared)
tests/integration/test_user_flows.py (use shared utils)
tests/integration/test_complete_flows.py (use shared utils)
```

---

## 9. CONCLUSION

The AgentVoiceBox backend is well-architected with proper service patterns, graceful degradation, and good test coverage. The main technical debt is in the **portal frontend**, which relies heavily on mock data and bypasses real authentication in development mode.

**Priority for the new requirements spec:**
1. Replace all mock data with real API calls
2. Implement the three-portal architecture (SaaS Admin, Customer, User)
3. Connect to real Keycloak, Lago, and PostgreSQL services
4. Add proper role-based navigation and permissions
