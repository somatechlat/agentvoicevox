# Implementation Plan: Django SaaS Backend - AgentVoiceBox Platform

## Overview

This implementation plan converts the Django SaaS Backend design into actionable coding tasks. All backend code uses Django 5.1+ with Django ORM exclusively - no other Python frameworks. The plan follows incremental development with property-based testing for correctness validation.

**Technology Stack:**
- Django 5.1+ (ASGI with Uvicorn)
- Django Ninja (REST API)
- Django Channels (WebSocket)
- Django ORM (PostgreSQL 16+)
- Temporal (Workflow orchestration)
- HashiCorp Vault (Secrets management)
- Keycloak (Authentication)
- SpiceDB (Authorization)

---

## Tasks

- [x] 1. Django Project Foundation
  - [x] 1.1 Create Django project structure with split settings
    - Create `backend/` directory with `manage.py`
    - Create `config/settings/` with `__init__.py`, `base.py`, `development.py`, `staging.py`, `production.py`, `testing.py`
    - Configure pydantic-settings for environment variable validation
    - Set up PostgreSQL connection with Django ORM connection pooling
    - Set up Redis for caching and sessions
    - _Requirements: 1.1, 1.2, 1.3, 1.5, 1.6, 1.7_

  - [x] 1.2 Create Django apps structure
    - Create apps: `core`, `tenants`, `users`, `projects`, `api_keys`, `sessions`, `billing`, `voice`, `themes`, `audit`, `notifications`, `workflows`
    - Configure `INSTALLED_APPS` in base settings
    - Set up app-specific `apps.py` configurations
    - _Requirements: 1.4_

  - [x] 1.3 Configure ASGI application with Django Channels
    - Create `config/asgi.py` with HTTP and WebSocket routing
    - Configure Uvicorn worker settings
    - Set up channel layers with Redis backend
    - _Requirements: 1.1, 6.1, 6.11_

  - [x] 1.4 Create health check endpoints
    - Implement `/health/` endpoint for liveness probe
    - Implement `/health/ready/` endpoint for readiness probe (checks DB, Redis, Temporal)
    - _Requirements: 1.8_

  - [ ]* 1.5 Write property test for environment validation
    - **Property 1: Environment Variable Validation**
    - Test that missing required env vars cause startup failure with clear error
    - **Validates: Requirements 1.3, 1.7**

- [-] 2. Checkpoint - Project Foundation
  - Ensure Django project starts successfully
  - Verify health endpoints respond
  - Ask the user if questions arise

---

- [x] 3. Multi-Tenancy Architecture
  - [x] 3.1 Create Tenant and TenantSettings models with Django ORM
    - Define `Tenant` model with UUID pk, name, slug, tier, status, billing_id, settings JSONField
    - Define tier choices: free, starter, pro, enterprise
    - Define status choices: active, suspended, pending, deleted
    - Add limit fields: max_users, max_projects, max_api_keys, max_sessions_per_month
    - Create `TenantSettings` model with branding, voice defaults, security settings
    - Create Django migrations
    - _Requirements: 2.1, 2.2, 2.3, 2.10_

  - [x] 3.2 Implement TenantMiddleware
    - Create thread-local storage for tenant context
    - Implement `get_current_tenant()`, `set_current_tenant()`, `clear_current_tenant()`
    - Extract tenant from JWT claims, X-Tenant-ID header, or subdomain
    - Reject requests without valid tenant context (400)
    - Return 403 for suspended tenants
    - _Requirements: 2.4, 2.5, 2.6, 2.7_

  - [x] 3.3 Create TenantScopedModel base class
    - Implement custom manager that filters by current tenant
    - Override `save()` to auto-set tenant if not provided
    - Override `get_queryset()` for automatic tenant filtering
    - _Requirements: 2.8, 2.9_

  - [ ]* 3.4 Write property tests for tenant isolation
    - **Property 2: Tenant Context Extraction**
    - Test tenant extraction from JWT, header, subdomain
    - **Validates: Requirements 2.4**

  - [ ]* 3.5 Write property tests for tenant access control
    - **Property 3: Tenant Access Control**
    - Test missing tenant returns 400, suspended tenant returns 403
    - **Validates: Requirements 2.6, 2.7**

  - [ ]* 3.6 Write property tests for tenant-scoped model isolation
    - **Property 4: Tenant-Scoped Model Isolation**
    - Test queries only return current tenant's records
    - Test auto-set tenant on save
    - **Validates: Requirements 2.8, 2.9**

---

- [x] 4. Keycloak Authentication
  - [x] 4.1 Create User model with Django ORM
    - Extend `AbstractBaseUser` and `PermissionsMixin`
    - Add fields: keycloak_id, email, first_name, last_name, tenant FK, is_active, preferences JSONField
    - Create custom user manager
    - Create Django migrations
    - _Requirements: 3.8_

  - [x] 4.2 Implement KeycloakMiddleware
    - Validate JWT tokens from Authorization header
    - Extract user_id (sub), tenant_id, roles from JWT claims
    - Fetch and cache Keycloak public key for verification
    - Create/update User records on first authentication
    - Return 401 with "token_expired" for expired tokens
    - Return 401 with "invalid_token" for malformed tokens
    - _Requirements: 3.1, 3.2, 3.3, 3.5, 3.6, 3.7_

  - [x] 4.3 Implement API key authentication
    - Support X-API-Key header as alternative to JWT
    - Validate API key and set user/tenant context
    - _Requirements: 3.9_

  - [ ]* 4.4 Write property tests for JWT authentication
    - **Property 5: JWT Authentication Validation**
    - Test valid tokens accepted, expired returns 401 "token_expired", invalid returns 401 "invalid_token"
    - **Validates: Requirements 3.1, 3.5, 3.6**

  - [ ]* 4.5 Write property tests for API key authentication
    - **Property 6: API Key Authentication**
    - Test valid keys authenticate, expired returns 401 "api_key_expired", revoked returns 401 "api_key_revoked"
    - **Validates: Requirements 3.9, 7.9, 7.10**

- [-] 5. Checkpoint - Authentication
  - Ensure JWT authentication works end-to-end
  - Verify tenant context is set correctly
  - Ask the user if questions arise

---

- [x] 6. SpiceDB Authorization
  - [x] 6.1 Create SpiceDB client integration
    - Implement gRPC client connection with configurable endpoint and token
    - Implement `check_permission(resource_type, resource_id, relation, subject_type, subject_id)`
    - Implement `write_relationship()` for creating permissions
    - Implement `delete_relationship()` for removing permissions
    - Implement `lookup_subjects()` for finding subjects with relation
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 6.2 Create SpiceDB schema
    - Define tenant relations: sysadmin, admin, developer, operator, viewer, billing
    - Define computed permissions: manage, administrate, develop, operate, view, billing_access
    - Define resource types: tenant, project, api_key, session, voice_config, theme, persona
    - Create schema.zed file
    - _Requirements: 4.6, 4.7, 4.8_

  - [x] 6.3 Implement permission decorators
    - Create `@require_permission` decorator for SpiceDB checks
    - Create `@require_role` decorator for JWT role checks
    - Return 403 with "permission_denied" on failure
    - _Requirements: 4.9, 4.10, 4.11_

  - [ ]* 6.4 Write property tests for SpiceDB permission enforcement
    - **Property 8: SpiceDB Permission Enforcement**
    - Test check_permission returns accurate results
    - Test denied permissions return 403 "permission_denied"
    - **Validates: Requirements 4.2, 4.11**

---

- [x] 7. Django Ninja API Layer
  - [x] 7.1 Configure Django Ninja API
    - Mount NinjaAPI at `/api/v2/`
    - Configure OpenAPI documentation at `/api/v2/docs`
    - Set up Pydantic schemas for request/response validation
    - _Requirements: 5.1, 5.2_

  - [x] 7.2 Create API routers
    - Create routers: tenants, users, projects, api_keys, sessions, billing, voice, themes, audit, notifications
    - Create admin routers at `/api/v2/admin/*` restricted to SYSADMIN
    - _Requirements: 5.3, 5.4_

  - [x] 7.3 Implement error handling and pagination
    - Create consistent error response format with error code, message, details
    - Implement PageNumberPagination with configurable page size
    - Implement filtering and sorting via Query parameters
    - Return 400 with field-level errors on validation failure
    - _Requirements: 5.5, 5.6, 5.7, 5.8_

  - [x] 7.4 Create service and repository layers
    - Create service classes for business logic (separate from API endpoints)
    - Create repository classes for Django ORM queries with QuerySet optimization
    - _Requirements: 5.9, 5.10_

  - [ ]* 7.5 Write property tests for Pydantic validation
    - **Property 9: Pydantic Schema Validation**
    - Test invalid requests return 400 with field-level error details
    - **Validates: Requirements 5.2, 5.8**

- [-] 8. Checkpoint - API Layer
  - Ensure all API endpoints respond correctly
  - Verify OpenAPI documentation is generated
  - Ask the user if questions arise

---

- [x] 9. API Key Management
  - [x] 9.1 Create APIKey model with Django ORM
    - Extend TenantScopedModel
    - Add fields: name, description, key_prefix, key_hash, scopes ArrayField, rate_limit_tier
    - Add fields: expires_at, revoked_at, last_used_at, last_used_ip, usage_count, created_by FK
    - Define scope choices: realtime, billing, admin
    - Define rate_limit_tier choices: standard, elevated, unlimited
    - Create Django migrations
    - _Requirements: 7.1, 7.5, 7.6_

  - [x] 9.2 Implement APIKeyService
    - Generate secure random keys with format `avb_{random_32_bytes}`
    - Hash keys using SHA-256 before storage
    - Return full key only once at creation
    - Validate keys by comparing hashes
    - Record usage on each use (last_used_at, last_used_ip, usage_count)
    - Implement key rotation with optional grace period
    - _Requirements: 7.2, 7.3, 7.4, 7.7, 7.8, 7.11_

  - [x] 9.3 Create API key endpoints
    - POST `/api/v2/api-keys/` - Create new key
    - GET `/api/v2/api-keys/` - List keys (without full key)
    - DELETE `/api/v2/api-keys/{id}/` - Revoke key
    - POST `/api/v2/api-keys/{id}/rotate/` - Rotate key
    - _Requirements: 7.1-7.11_

  - [ ]* 9.4 Write property tests for API key lifecycle
    - **Property 7: API Key Lifecycle Round-Trip**
    - Test key format `avb_{random_32_bytes}`, hash storage, single return, validation
    - **Validates: Requirements 7.2, 7.3, 7.4, 7.7**

---

- [x] 10. Django Channels WebSocket
  - [x] 10.1 Configure WebSocket routing
    - Create `realtime/routing.py` with URL patterns
    - Configure channel middleware for authentication
    - Set up Redis channel layer
    - _Requirements: 6.1, 6.11_

  - [x] 10.2 Implement BaseConsumer
    - Create `AsyncJsonWebsocketConsumer` base class
    - Validate authentication and tenant before accepting connections
    - Handle ping/pong heartbeat messages
    - Close with code 4001 on auth failure
    - _Requirements: 6.2, 6.3, 6.4, 6.5, 6.10_

  - [x] 10.3 Implement EventConsumer
    - Stream tenant-wide notifications at `/ws/v2/events`
    - Stream user-specific notifications
    - Join appropriate channel groups on connect
    - _Requirements: 6.6_

  - [x] 10.4 Implement SessionConsumer
    - Handle voice session communication at `/ws/v2/sessions/{session_id}`
    - Forward audio chunks to Temporal STT workflow
    - Receive transcription results and broadcast to client
    - Trigger LLM response generation
    - Stream TTS audio back to client
    - _Requirements: 6.7, 8.6, 8.7, 8.8, 8.9_

  - [x] 10.5 Implement TranscriptionConsumer and TTSConsumer
    - Stream STT results at `/ws/v2/stt/transcription`
    - Stream TTS audio at `/ws/v2/tts/stream`
    - _Requirements: 6.8, 6.9_

  - [ ]* 10.6 Write property tests for WebSocket authentication
    - **Property 10: WebSocket Authentication**
    - Test authenticated connections have user/tenant in scope
    - Test unauthenticated connections close with code 4001
    - **Validates: Requirements 6.3, 6.10**

- [-] 11. Checkpoint - WebSocket Layer
  - Ensure WebSocket connections authenticate correctly
  - Verify event streaming works
  - Ask the user if questions arise

---

- [x] 12. Voice Session Management
  - [x] 12.1 Create Session and SessionEvent models with Django ORM
    - Create `Session` model extending TenantScopedModel
    - Add fields: project FK, api_key FK, status, config JSONField
    - Add metrics: duration_seconds, input_tokens, output_tokens, audio_duration_seconds
    - Add timestamps: started_at, terminated_at
    - Define status choices: created, active, completed, error, terminated
    - Create `SessionEvent` model with session FK, event_type, data JSONField
    - Create Django migrations
    - _Requirements: 8.1, 8.2, 8.5_

  - [x] 12.2 Implement SessionService
    - Create sessions with voice, model, turn detection configuration
    - Track session metrics
    - Implement auto-termination for sessions exceeding 24 hours
    - _Requirements: 8.3, 8.4, 8.10_

  - [x] 12.3 Create session endpoints
    - POST `/api/v2/sessions/` - Create session
    - GET `/api/v2/sessions/{id}/` - Get session details
    - POST `/api/v2/sessions/{id}/terminate/` - Terminate session
    - GET `/api/v2/sessions/{id}/events/` - Get session events
    - _Requirements: 8.1-8.10_

  - [ ]* 12.4 Write property tests for session auto-termination
    - **Property 11: Session Auto-Termination**
    - Test sessions exceeding 24 hours are automatically terminated
    - **Validates: Requirements 8.10**

---

- [x] 13. Temporal Workflow Orchestration
  - [x] 13.1 Configure Temporal client
    - Create `config/temporal.py` with client configuration
    - Connect to Temporal server with namespace isolation
    - Create Django management command for running workers
    - _Requirements: 9.1, 9.2_

  - [x] 13.2 Implement TenantAwareWorkflow base
    - Maintain tenant context throughout workflow execution
    - Pass tenant_id as workflow input
    - _Requirements: 9.3_

  - [x] 13.3 Create voice processing workflows
    - Implement STT workflow with activities for audio processing
    - Implement TTS workflow with activities for synthesis
    - Implement LLM workflow with activities for response generation
    - Configure retry policies (max 3 attempts, exponential backoff)
    - _Requirements: 9.6, 9.7, 9.8, 9.4, 9.9_

  - [x] 13.4 Create scheduled workflows
    - Implement cleanup_expired_sessions (hourly)
    - Implement sync_billing_usage (15 minutes)
    - Implement aggregate_metrics (5 minutes)
    - Configure Temporal schedules
    - _Requirements: 9.5_

  - [x] 13.5 Configure task queue routing
    - Set up queues: default, voice-processing, billing, notifications
    - Route workflows to appropriate queues
    - _Requirements: 9.10_

  - [ ]* 13.6 Write property tests for workflow retry
    - **Property 12: Task Retry with Backoff**
    - Test failed activities retry up to 3 times with exponential backoff
    - **Validates: Requirements 9.9**

- [-] 14. Checkpoint - Workflow Orchestration
  - Ensure Temporal workflows execute correctly
  - Verify scheduled workflows run on time
  - Ask the user if questions arise

---

- [x] 15. Caching and Rate Limiting
  - [x] 15.1 Implement CacheService
    - Use Redis with tenant-prefixed keys for isolation
    - Implement get, set, delete, get_or_set operations
    - Create `@cached` decorator with configurable TTL
    - _Requirements: 10.1, 10.2, 10.3_

  - [x] 15.2 Implement RateLimitMiddleware
    - Implement token bucket rate limiting
    - Apply limits per IP (unauthenticated), user (authenticated), or API key
    - Return rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
    - Return 429 with retry_after when exceeded
    - Configure per-tier limits: DEFAULT (60/min), API_KEY (120/min), ADMIN (300/min)
    - _Requirements: 10.4, 10.5, 10.6, 10.7, 10.8_

  - [ ]* 15.3 Write property tests for cache tenant isolation
    - **Property 13: Cache Tenant Isolation**
    - Test cache keys are prefixed with tenant ID
    - **Validates: Requirements 10.1**

  - [ ]* 15.4 Write property tests for rate limiting
    - **Property 14: Rate Limiting Enforcement**
    - Test exceeded limits return 429 with headers and retry_after
    - **Validates: Requirements 10.7**

---

- [x] 16. Logging and Observability
  - [x] 16.1 Configure structlog
    - Set up structured JSON logging for production
    - Bind user_id and tenant_id to log context
    - _Requirements: 11.1, 11.4_

  - [x] 16.2 Implement RequestLoggingMiddleware
    - Log all requests with: request_id, method, path, status_code, duration_ms, client_ip
    - Generate unique request_id and return in X-Request-ID header
    - _Requirements: 11.2, 11.3_

  - [x] 16.3 Configure Prometheus metrics
    - Track HTTP metrics: http_requests_total, http_request_duration_seconds
    - Track WebSocket metrics: websocket_connections, websocket_messages_total
    - Track business metrics: tenants_total, sessions_total, session_duration_seconds, active_sessions
    - Track worker metrics: stt_requests_total, tts_requests_total, llm_requests_total, llm_tokens_total
    - Track infrastructure metrics: db_query_duration_seconds, cache_hits_total, temporal_workflows_total
    - Expose metrics at `/metrics`
    - _Requirements: 11.5, 11.6, 11.7, 11.8, 11.9_

  - [ ]* 16.4 Write property tests for request ID generation
    - **Property 15: Request ID Generation**
    - Test every request gets unique request_id in X-Request-ID header
    - **Validates: Requirements 11.3**

---

- [x] 17. Audit Logging
  - [x] 17.1 Create AuditLog model with Django ORM
    - Add fields: timestamp, actor_id, actor_email, actor_type, tenant FK, ip_address
    - Add fields: action, resource_type, resource_id, description, old_values JSONField, new_values JSONField
    - Define action choices: create, update, delete, login, logout, api_call, permission_change, settings_change, billing_event
    - Define actor_type choices: user, api_key, system
    - Override save() to prevent updates
    - Override delete() to prevent deletion
    - Create Django migrations
    - _Requirements: 12.1, 12.2, 12.5_

  - [x] 17.2 Implement AuditMiddleware
    - Automatically log all write operations (POST, PUT, PATCH, DELETE)
    - Create `AuditLog.log()` class method for manual logging
    - _Requirements: 12.3, 12.4_

  - [x] 17.3 Create audit API endpoints
    - GET `/api/v2/audit/` - List audit logs with filtering
    - Support filtering by tenant, actor, action, resource_type, date range
    - Support CSV export
    - Configure 90-day retention
    - _Requirements: 12.6, 12.7, 12.8_

  - [ ]* 17.4 Write property tests for audit log immutability
    - **Property 16: Audit Log Immutability**
    - Test update attempts raise error
    - Test delete attempts raise error
    - **Validates: Requirements 12.5**

---

- [x] 18. Exception Handling
  - [x] 18.1 Create exception hierarchy
    - Create `APIException` base class with status_code, error_code, default_message
    - Create validation errors: ValidationError (400)
    - Create auth errors: AuthenticationError (401), TokenExpiredError (401), PermissionDeniedError (403)
    - Create tenant errors: TenantNotFoundError (404), TenantSuspendedError (403), TenantLimitExceededError (403)
    - Create other errors: NotFoundError (404), ConflictError (409), RateLimitError (429)
    - _Requirements: 13.2, 13.3, 13.4, 13.5_

  - [x] 18.2 Implement ExceptionMiddleware
    - Catch all exceptions and return JSON responses
    - Return generic error without stack trace in production
    - Include stack trace in development
    - Log all exceptions with full context
    - _Requirements: 13.1, 13.6, 13.7, 13.8_

  - [ ]* 18.3 Write property tests for exception sanitization
    - **Property 17: Exception Sanitization**
    - Test production mode returns generic error without stack traces
    - **Validates: Requirements 13.6**

- [-] 19. Checkpoint - Observability
  - Ensure logging, metrics, and audit work correctly
  - Verify exception handling returns proper responses
  - Ask the user if questions arise

---

- [x] 20. Security Middleware
  - [x] 20.1 Configure SecurityMiddleware
    - Enforce HTTPS redirect in production
    - Set HSTS header with 1 year max-age
    - Set Content-Security-Policy header
    - Set X-Content-Type-Options: nosniff
    - Set X-Frame-Options: DENY
    - Set Referrer-Policy: strict-origin-when-cross-origin
    - Set Permissions-Policy restricting sensitive APIs
    - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 14.6, 14.7_

  - [x] 20.2 Configure CORS and session security
    - Configure CORS to allow only configured origins with credentials
    - Set session cookies: secure, httpOnly, sameSite=Lax
    - Enable CSRF protection for state-changing operations
    - _Requirements: 14.8, 14.9, 14.10_

---

- [x] 21. HashiCorp Vault Integration
  - [x] 21.1 Create Vault client
    - Connect to Vault server with AppRole authentication
    - Retrieve database credentials dynamically
    - Retrieve API keys and tokens from KV secrets engine v2
    - Cache secrets with configurable TTL and automatic refresh
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 21.2 Configure Vault policies and encryption
    - Define access policies per service: backend, temporal-worker, keycloak
    - Use Transit engine to encrypt sensitive tenant data (API keys, webhook secrets)
    - Configure PKI for internal TLS certificates
    - Implement automatic lease renewal
    - Fail fast if Vault unavailable during startup
    - _Requirements: 15.5, 15.6, 15.7, 15.8, 15.9, 15.10_

---

- [x] 22. Billing Integration
  - [x] 22.1 Create Lago client
    - Sync tenants as customers with external_id, name, metadata
    - Assign subscriptions based on tenant tier
    - _Requirements: 16.1, 16.2_

  - [x] 22.2 Implement BillingService
    - Track usage events: sessions, api_calls, audio_minutes, tokens
    - Create Temporal workflow for billing sync (every 15 minutes)
    - Handle Lago webhooks for subscription and invoice events
    - Emit billing.alert event when tenant exceeds limits
    - _Requirements: 16.3, 16.4, 16.5, 16.7_

  - [x] 22.3 Create billing API endpoints
    - GET `/api/v2/billing/usage/` - Current usage
    - GET `/api/v2/billing/projected/` - Projected costs
    - GET `/api/v2/billing/invoices/` - Invoice history
    - _Requirements: 16.6_

---

- [ ] 23. Docker and Deployment
  - [x] 23.1 Create Dockerfile
    - Multi-stage build with Python 3.12
    - Run as non-root user
    - Include health check
    - Configure Gunicorn with Uvicorn workers
    - _Requirements: 17.1, 17.2, 17.3, 17.7_

  - [x] 23.2 Create Docker Compose configuration
    - Define services: backend, temporal, temporal-ui, temporal-worker, vault, postgres, redis, keycloak, spicedb, nginx, prometheus, grafana
    - Configure memory limits and reservations (15GB total)
    - Configure persistent volumes for all stateful services
    - Configure health checks for all services
    - Configure production-tuned PostgreSQL settings
    - _Requirements: 17.4_

  - [x] 23.3 Create Kubernetes manifests
    - Create Deployment with liveness and readiness probes
    - Create HorizontalPodAutoscaler based on CPU and memory
    - Configure graceful shutdown with connection draining
    - _Requirements: 17.5, 17.6, 17.8_

  - [x] 23.4 Create configuration files
    - Create `.env.example` with all required environment variables
    - Create Temporal dynamic config
    - Create Vault policies
    - Create Prometheus configuration
    - Create Grafana dashboards
    - _Requirements: 17.1-17.8_

- [ ] 24. Final Checkpoint - Full System
  - Ensure all services start correctly with Docker Compose
  - Verify end-to-end flow: auth → API → WebSocket → Temporal
  - Run all property tests
  - Ask the user if questions arise

---

## Notes

- Tasks marked with `*` are optional property-based tests and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- All code uses Django ORM exclusively - no other Python frameworks
- Property tests validate universal correctness properties using Hypothesis
- Unit tests validate specific examples and edge cases
