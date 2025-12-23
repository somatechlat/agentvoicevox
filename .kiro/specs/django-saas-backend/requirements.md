# Requirements Document

## Django SaaS Backend Architecture - AgentVoiceBox Platform

**Document Identifier:** AVB-REQ-BACKEND-001  
**Version:** 1.0.0  
**Date:** 2025-12-23  
**Status:** Draft  

---

## Introduction

This document specifies the requirements for implementing a production-grade Django SaaS backend for the AgentVoiceBox platform. The system provides multi-tenant voice agent infrastructure with real-time communication, fine-grained authorization, and enterprise-grade observability.

## Glossary

- **Tenant**: An organization using the platform with isolated data and configuration
- **ASGI**: Asynchronous Server Gateway Interface for async Django
- **SpiceDB**: Google Zanzibar-inspired authorization system for fine-grained permissions
- **Django_Ninja**: Fast Django REST framework with automatic OpenAPI documentation
- **Celery**: Distributed task queue for background job processing
- **Keycloak**: Open-source identity and access management solution
- **JWT**: JSON Web Token for stateless authentication
- **WebSocket**: Full-duplex communication protocol for real-time features

---

## Requirements

### Requirement 1: Django Project Foundation

**User Story:** As a developer, I want a well-structured Django project with split settings and proper configuration, so that I can develop and deploy the application across different environments.

#### Acceptance Criteria

1. THE Django_Project SHALL use Django 5.1+ with ASGI support via Uvicorn
2. THE Django_Project SHALL implement split settings for base, development, staging, production, and testing environments
3. THE Django_Project SHALL use environment variables for all sensitive configuration via pydantic-settings
4. THE Django_Project SHALL organize code into separate Django apps: core, tenants, users, projects, api_keys, sessions, billing, voice, themes, audit, notifications
5. THE Django_Project SHALL use PostgreSQL 16+ as the primary database with connection pooling
6. THE Django_Project SHALL use Redis 7+ for caching, sessions, and Celery broker
7. WHEN the application starts THEN the Django_Project SHALL validate all required environment variables
8. THE Django_Project SHALL include health check endpoints at `/health/` for liveness and readiness probes

---

### Requirement 2: Multi-Tenancy Architecture

**User Story:** As a platform operator, I want complete tenant isolation, so that each organization's data is secure and separate from others.

#### Acceptance Criteria

1. THE Tenant_Model SHALL store id (UUID), name, slug (unique), tier, status, billing_id, settings (JSON), and limit fields
2. THE Tenant_Model SHALL support status values: active, suspended, pending, deleted
3. THE Tenant_Model SHALL support tier values: free, starter, pro, enterprise with corresponding limits
4. THE TenantMiddleware SHALL extract tenant context from JWT claims, X-Tenant-ID header, or subdomain
5. THE TenantMiddleware SHALL set tenant in thread-local storage accessible via `get_current_tenant()`
6. THE TenantMiddleware SHALL reject requests to tenant-scoped endpoints without valid tenant context
7. WHEN a tenant is suspended THEN the TenantMiddleware SHALL return 403 Forbidden for all requests
8. THE TenantScopedModel SHALL automatically filter querysets by current tenant
9. THE TenantScopedModel SHALL automatically set tenant on save if not provided
10. THE TenantSettings_Model SHALL store extended settings: branding, voice defaults, notification preferences, security settings

---

### Requirement 3: Keycloak Authentication

**User Story:** As a user, I want to authenticate via Keycloak with Google OAuth support, so that I can securely access the platform.

#### Acceptance Criteria

1. THE KeycloakMiddleware SHALL validate JWT tokens from the Authorization header
2. THE KeycloakMiddleware SHALL extract user_id (sub), tenant_id, and roles from JWT claims
3. THE KeycloakMiddleware SHALL fetch and cache Keycloak's public key for token verification
4. THE KeycloakMiddleware SHALL support token refresh via refresh_token
5. WHEN a token is expired THEN the KeycloakMiddleware SHALL return 401 Unauthorized with error code "token_expired"
6. WHEN a token is invalid THEN the KeycloakMiddleware SHALL return 401 Unauthorized with error code "invalid_token"
7. THE KeycloakMiddleware SHALL create or update User records from JWT claims on first authentication
8. THE User_Model SHALL store id (UUID), keycloak_id, email, first_name, last_name, tenant (FK), is_active, preferences (JSON)
9. THE KeycloakMiddleware SHALL support API key authentication via X-API-Key header as alternative to JWT

---

### Requirement 4: SpiceDB Authorization

**User Story:** As a platform operator, I want fine-grained permission control, so that I can enforce complex access policies across tenants and resources.

#### Acceptance Criteria

1. THE SpiceDBClient SHALL connect to SpiceDB via gRPC with configurable endpoint and token
2. THE SpiceDBClient SHALL implement check_permission(resource_type, resource_id, relation, subject_type, subject_id)
3. THE SpiceDBClient SHALL implement write_relationship for creating permission relationships
4. THE SpiceDBClient SHALL implement delete_relationship for removing permission relationships
5. THE SpiceDBClient SHALL implement lookup_subjects for finding all subjects with a relation
6. THE SpiceDB_Schema SHALL define tenant relations: sysadmin, admin, developer, operator, viewer, billing
7. THE SpiceDB_Schema SHALL define computed permissions: manage, administrate, develop, operate, view, billing_access
8. THE SpiceDB_Schema SHALL define resource types: tenant, project, api_key, session, voice_config, theme, persona
9. THE @require_permission decorator SHALL check SpiceDB before allowing endpoint access
10. THE @require_role decorator SHALL check JWT roles before allowing endpoint access
11. WHEN permission is denied THEN the System SHALL return 403 Forbidden with error code "permission_denied"

---

### Requirement 5: Django Ninja API Layer

**User Story:** As a developer, I want a fast, type-safe REST API with automatic documentation, so that I can build and consume APIs efficiently.

#### Acceptance Criteria

1. THE NinjaAPI SHALL be mounted at `/api/v2/` with OpenAPI documentation at `/api/v2/docs`
2. THE NinjaAPI SHALL use Pydantic schemas for request/response validation
3. THE NinjaAPI SHALL organize endpoints into routers: tenants, users, projects, api_keys, sessions, billing, voice, themes, audit, notifications
4. THE NinjaAPI SHALL include admin routers at `/api/v2/admin/*` restricted to SYSADMIN role
5. THE NinjaAPI SHALL implement consistent error responses with error code, message, and optional details
6. THE NinjaAPI SHALL support pagination via PageNumberPagination with configurable page size
7. THE NinjaAPI SHALL support filtering and sorting via Query parameters
8. WHEN validation fails THEN the NinjaAPI SHALL return 400 Bad Request with field-level error details
9. THE Service_Layer SHALL contain all business logic separate from API endpoints
10. THE Repository_Layer SHALL handle database queries with QuerySet optimization

---

### Requirement 6: Django Channels WebSocket

**User Story:** As a user, I want real-time updates and voice streaming, so that I can have interactive voice sessions.

#### Acceptance Criteria

1. THE ASGI_Application SHALL route HTTP to Django and WebSocket to Channels
2. THE WebSocketMiddleware SHALL authenticate connections via token or api_key query parameter
3. THE WebSocketMiddleware SHALL set user and tenant context on the connection scope
4. THE BaseConsumer SHALL validate authentication and tenant before accepting connections
5. THE BaseConsumer SHALL handle ping/pong heartbeat messages
6. THE EventConsumer SHALL stream tenant-wide and user-specific notifications at `/ws/v2/events`
7. THE SessionConsumer SHALL handle voice session communication at `/ws/v2/sessions/{session_id}`
8. THE TranscriptionConsumer SHALL stream STT results at `/ws/v2/stt/transcription`
9. THE TTSConsumer SHALL stream TTS audio at `/ws/v2/tts/stream`
10. WHEN a WebSocket connection fails authentication THEN the Consumer SHALL close with code 4001
11. THE Channel_Layer SHALL use Redis for cross-process message passing

---

### Requirement 7: API Key Management

**User Story:** As a developer, I want to create and manage API keys, so that I can integrate with the platform programmatically.

#### Acceptance Criteria

1. THE APIKey_Model SHALL store id (UUID), name, description, key_prefix, key_hash, scopes, rate_limit_tier, expires_at, revoked_at
2. THE APIKey_Service SHALL generate secure random keys with format `avb_{random_32_bytes}`
3. THE APIKey_Service SHALL hash keys using SHA-256 before storage
4. THE APIKey_Service SHALL only return the full key once at creation time
5. THE APIKey_Model SHALL support scopes: realtime, billing, admin
6. THE APIKey_Model SHALL support rate_limit_tiers: standard, elevated, unlimited
7. THE APIKey_Service SHALL validate keys by comparing hashes
8. THE APIKey_Service SHALL record usage (last_used_at, last_used_ip, usage_count) on each use
9. WHEN an API key is expired THEN the System SHALL reject requests with error code "api_key_expired"
10. WHEN an API key is revoked THEN the System SHALL reject requests with error code "api_key_revoked"
11. THE APIKey_Service SHALL support key rotation with optional grace period

---

### Requirement 8: Voice Session Management

**User Story:** As a user, I want to create and manage voice sessions, so that I can interact with voice agents.

#### Acceptance Criteria

1. THE Session_Model SHALL store id (UUID), tenant (FK), project (FK), api_key (FK), status, config (JSON), timing fields, metrics
2. THE Session_Model SHALL support status values: created, active, completed, error, terminated
3. THE Session_Service SHALL create sessions with configuration for voice, model, and turn detection
4. THE Session_Service SHALL track metrics: duration_seconds, input_tokens, output_tokens, audio_duration_seconds
5. THE SessionEvent_Model SHALL store transcript, response, tool_call, tool_result, error, and system events
6. THE SessionConsumer SHALL forward audio chunks to STT worker via Celery
7. THE SessionConsumer SHALL receive transcription results and broadcast to client
8. THE SessionConsumer SHALL trigger LLM response generation on user input
9. THE SessionConsumer SHALL stream TTS audio back to client
10. WHEN a session exceeds 24 hours THEN the System SHALL automatically terminate it

---

### Requirement 9: Background Task Processing

**User Story:** As a platform operator, I want reliable background task processing, so that long-running operations don't block API requests.

#### Acceptance Criteria

1. THE Celery_App SHALL use Redis as message broker with separate queues: default, stt, tts, llm, billing, notifications, scheduled
2. THE Celery_App SHALL use Django database as result backend
3. THE TenantAwareTask SHALL maintain tenant context during task execution
4. THE RetryableTask SHALL implement automatic retry with exponential backoff
5. THE Celery_Beat SHALL schedule periodic tasks: cleanup_expired_sessions (hourly), sync_billing_usage (15min), aggregate_metrics (5min)
6. THE STT_Worker SHALL process audio chunks and publish transcription results
7. THE TTS_Worker SHALL generate audio from text and stream results
8. THE LLM_Worker SHALL generate responses and stream tokens
9. WHEN a task fails THEN the System SHALL log the error and retry up to 3 times
10. THE Task_Routing SHALL direct tasks to appropriate queues based on task name

---

### Requirement 10: Caching and Rate Limiting

**User Story:** As a platform operator, I want efficient caching and rate limiting, so that the system performs well under load.

#### Acceptance Criteria

1. THE CacheService SHALL use Redis with tenant-prefixed keys for isolation
2. THE CacheService SHALL support get, set, delete, and get_or_set operations
3. THE @cached decorator SHALL cache function results with configurable TTL
4. THE RateLimitMiddleware SHALL implement token bucket rate limiting
5. THE RateLimitMiddleware SHALL apply limits per IP (unauthenticated), user (authenticated), or API key
6. THE RateLimitMiddleware SHALL return rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
7. WHEN rate limit is exceeded THEN the System SHALL return 429 Too Many Requests with retry_after
8. THE Rate_Limits SHALL be configurable per tier: DEFAULT (60/min), API_KEY (120/min), ADMIN (300/min)

---

### Requirement 11: Logging and Observability

**User Story:** As a platform operator, I want comprehensive logging and metrics, so that I can monitor and debug the system.

#### Acceptance Criteria

1. THE Logging_System SHALL use structlog for structured JSON logging in production
2. THE RequestLoggingMiddleware SHALL log all requests with: request_id, method, path, status_code, duration_ms, client_ip
3. THE RequestLoggingMiddleware SHALL generate unique request_id and return in X-Request-ID header
4. THE Logging_System SHALL bind user_id and tenant_id to log context when available
5. THE Prometheus_Metrics SHALL track: http_requests_total, http_request_duration_seconds, websocket_connections, websocket_messages_total
6. THE Prometheus_Metrics SHALL track business metrics: tenants_total, sessions_total, session_duration_seconds, active_sessions
7. THE Prometheus_Metrics SHALL track worker metrics: stt_requests_total, tts_requests_total, llm_requests_total, llm_tokens_total
8. THE Prometheus_Metrics SHALL track infrastructure metrics: db_query_duration_seconds, cache_hits_total, celery_tasks_total
9. THE Metrics_Endpoint SHALL expose Prometheus metrics at `/metrics`

---

### Requirement 12: Audit Logging

**User Story:** As a compliance officer, I want immutable audit logs, so that I can track all significant actions for security and compliance.

#### Acceptance Criteria

1. THE AuditLog_Model SHALL store timestamp, actor_id, actor_email, actor_type, tenant_id, ip_address, action, resource_type, resource_id, description, old_values, new_values
2. THE AuditLog_Model SHALL support actions: create, update, delete, login, logout, api_call, permission_change, settings_change, billing_event
3. THE AuditMiddleware SHALL automatically log all write operations (POST, PUT, PATCH, DELETE) to auditable paths
4. THE AuditLog.log() method SHALL create audit entries with full context
5. THE AuditLog SHALL be immutable (no update or delete operations)
6. THE Audit_API SHALL support filtering by tenant, actor, action, resource_type, and date range
7. THE Audit_API SHALL support CSV export of audit logs
8. THE System SHALL retain audit logs for minimum 90 days

---

### Requirement 13: Exception Handling

**User Story:** As a developer, I want consistent error handling, so that API consumers receive predictable error responses.

#### Acceptance Criteria

1. THE ExceptionMiddleware SHALL catch all exceptions and return JSON responses
2. THE APIException base class SHALL define status_code, error_code, and default_message
3. THE System SHALL define exceptions: ValidationError (400), NotFoundError (404), ConflictError (409), RateLimitError (429)
4. THE System SHALL define auth exceptions: AuthenticationError (401), TokenExpiredError (401), PermissionDeniedError (403)
5. THE System SHALL define tenant exceptions: TenantNotFoundError (404), TenantSuspendedError (403), TenantLimitExceededError (403)
6. WHEN an unexpected exception occurs in production THEN the System SHALL return generic error without stack trace
7. WHEN an unexpected exception occurs in development THEN the System SHALL include stack trace in response
8. THE ExceptionMiddleware SHALL log all exceptions with full context

---

### Requirement 14: Security

**User Story:** As a security officer, I want comprehensive security controls, so that the platform is protected against common attacks.

#### Acceptance Criteria

1. THE SecurityMiddleware SHALL enforce HTTPS redirect in production
2. THE SecurityMiddleware SHALL set HSTS header with 1 year max-age
3. THE SecurityMiddleware SHALL set Content-Security-Policy header
4. THE SecurityMiddleware SHALL set X-Content-Type-Options: nosniff
5. THE SecurityMiddleware SHALL set X-Frame-Options: DENY
6. THE SecurityMiddleware SHALL set Referrer-Policy: strict-origin-when-cross-origin
7. THE SecurityMiddleware SHALL set Permissions-Policy restricting sensitive APIs
8. THE CORS_Configuration SHALL allow only configured origins with credentials
9. THE Session_Cookies SHALL be secure, httpOnly, and sameSite=Lax
10. THE CSRF_Protection SHALL be enabled for all state-changing operations

---

### Requirement 15: Billing Integration

**User Story:** As a platform operator, I want usage-based billing integration, so that I can charge tenants based on their usage.

#### Acceptance Criteria

1. THE Lago_Client SHALL sync tenants as customers with external_id, name, and metadata
2. THE Lago_Client SHALL assign subscriptions based on tenant tier
3. THE Billing_Service SHALL track usage events: sessions, api_calls, audio_minutes, tokens
4. THE Billing_Sync_Task SHALL sync usage to Lago every 15 minutes
5. THE Lago_Webhooks SHALL handle subscription and invoice events
6. THE Billing_API SHALL return current usage, projected costs, and invoice history
7. WHEN a tenant exceeds their plan limits THEN the System SHALL emit billing.alert event

---

### Requirement 16: Deployment

**User Story:** As a DevOps engineer, I want containerized deployment with horizontal scaling, so that I can deploy and scale the platform reliably.

#### Acceptance Criteria

1. THE Dockerfile SHALL build a production-ready image with Python 3.12
2. THE Dockerfile SHALL run as non-root user for security
3. THE Dockerfile SHALL include health check for container orchestration
4. THE Docker_Compose SHALL define services: backend, celery-worker, celery-beat, postgres, redis, keycloak, spicedb
5. THE Kubernetes_Deployment SHALL support horizontal pod autoscaling based on CPU and memory
6. THE Kubernetes_Deployment SHALL include liveness and readiness probes
7. THE Gunicorn_Config SHALL use Uvicorn workers for ASGI support
8. THE System SHALL support graceful shutdown with connection draining
