# Design Document

## Django SaaS Backend Architecture - AgentVoiceBox Platform

**Document Identifier:** AVB-DESIGN-BACKEND-001  
**Version:** 1.0.0  
**Date:** 2025-12-23  
**Status:** Draft  
**Related Requirements:** AVB-REQ-BACKEND-001  

---

## 1. Overview

This design document specifies the technical architecture for implementing a production-grade Django SaaS backend for the AgentVoiceBox platform. The system provides multi-tenant voice agent infrastructure with real-time WebSocket communication, fine-grained SpiceDB authorization, and enterprise-grade observability.

### 1.1 Design Goals

1. **Multi-Tenant Isolation**: Complete data and configuration isolation between tenants
2. **Real-Time Communication**: WebSocket-based streaming for voice sessions
3. **Fine-Grained Authorization**: SpiceDB-based permission system with 6 roles
4. **Horizontal Scalability**: Stateless design supporting container orchestration
5. **Observability**: Structured logging, Prometheus metrics, distributed tracing
6. **Security**: Defense-in-depth with multiple security layers

### 1.2 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | Django | 5.1+ | Core web framework |
| API | Django Ninja | 1.3+ | REST API with OpenAPI |
| WebSocket | Django Channels | 4.0+ | Real-time communication |
| Database | PostgreSQL | 16+ | Primary data store |
| Cache | Redis | 7+ | Caching, sessions, pub/sub |
| Auth | Keycloak | 24+ | Identity provider |
| AuthZ | SpiceDB | 1.30+ | Fine-grained permissions |
| Workflows | Temporal | 1.24+ | Durable workflow orchestration |
| Secrets | HashiCorp Vault | 1.15+ | Secrets management, PKI |
| Billing | Lago | Latest | Usage-based billing |
| Monitoring | Prometheus + Grafana | Latest | Metrics and dashboards |
| Logging | Structlog | 24.1+ | Structured logging |

---

## 2. Architecture

### 2.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                                   LOAD BALANCER                                      │
│                              (HAProxy / AWS ALB)                                     │
│                                   Port: 443                                          │
└─────────────────────────────────────┬───────────────────────────────────────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
┌───────────────────────────────────┐   ┌───────────────────────────────────────────┐
│      FRONTEND (Lit 3.x)           │   │         DJANGO BACKEND (ASGI)             │
│      Vite + Web Components        │   │         Uvicorn + Gunicorn                │
│      Port: 3000                   │   │         Port: 8000                        │
│                                   │   │                                           │
│  ┌─────────────────────────────┐  │   │  ┌─────────────────────────────────────┐ │
│  │  eog-* Web Components       │  │   │  │  Django Ninja API Router            │ │
│  │  AgentSkin Theme System     │  │   │  │  /api/v2/*                          │ │
│  │  Vaadin Router              │  │   │  └─────────────────────────────────────┘ │
│  │  Lit Context Stores         │  │   │                                           │
│  └─────────────────────────────┘  │   │  ┌─────────────────────────────────────┐ │
│                                   │   │  │  Django Channels                     │ │
│  ┌─────────────────────────────┐  │   │  │  /ws/v2/*                           │ │
│  │  WebSocket Client           │──┼───┼──│  ASGI Consumer Groups               │ │
│  │  REST API Client            │──┼───┼──│                                     │ │
│  └─────────────────────────────┘  │   │  └─────────────────────────────────────┘ │
└───────────────────────────────────┘   └───────────────────────────────────────────┘
                                                          │
          ┌───────────────────────────────────────────────┼───────────────────────────┐
          │                                               │                           │
          ▼                                               ▼                           ▼
┌─────────────────────┐              ┌─────────────────────────────┐    ┌─────────────────────┐
│    PostgreSQL 16    │              │         Redis 7             │    │     Keycloak 24     │
│    Port: 5432       │              │       Port: 6379            │    │     Port: 8080      │
│                     │              │                             │    │                     │
│  • Tenants          │              │  • Session Store            │    │  • OIDC Provider    │
│  • Users            │              │  • Cache Backend            │    │  • Google OAuth     │
│  • Projects         │              │  • Channel Layers           │    │  • JWT Tokens       │
│  • API Keys         │              │  • Rate Limit Counters      │    │  • User Federation  │
│  • Sessions         │              │  • Pub/Sub Events           │    │                     │
│  • Audit Logs       │              │                             │    │                     │
│  • Temporal Data    │              │                             │    │                     │
└─────────────────────┘              └─────────────────────────────┘    └─────────────────────┘
          │                                               │
          ▼                                               ▼
┌─────────────────────┐              ┌─────────────────────────────┐
│     SpiceDB         │              │      Temporal Server        │
│   Port: 50051       │              │      Port: 7233             │
│                     │              │                             │
│  • Permission       │              │  • Workflow Orchestration   │
│    Relationships    │              │  • Durable Execution        │
│  • RBAC Policies    │              │  • Activity Scheduling      │
│  • Tenant Isolation │              │  • Workflow History         │
└─────────────────────┘              │  • Task Queue Routing       │
                                     └─────────────────────────────┘
          │                                               │
          ▼                                               ▼
┌─────────────────────┐              ┌─────────────────────────────┐
│  HashiCorp Vault    │              │     Temporal Workers        │
│   Port: 8200        │              │                             │
│                     │              │  • STT Activity Worker      │
│  • Dynamic Secrets  │              │  • TTS Activity Worker      │
│  • Database Creds   │              │  • LLM Activity Worker      │
│  • API Key Encrypt  │              │  • Billing Activity Worker  │
│  • PKI Certificates │              │  • Notification Worker      │
│  • Audit Logging    │              │  • Cleanup Worker           │
└─────────────────────┘              └─────────────────────────────┘
```

### 2.2 Request Flow Diagram

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Client  │────▶│  Nginx   │────▶│   Uvicorn    │────▶│   Django     │
│ (Browser)│     │ (Proxy)  │     │   (ASGI)     │     │   App        │
└──────────┘     └──────────┘     └──────────────┘     └──────────────┘
                                                              │
                                                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MIDDLEWARE PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  1. SecurityMiddleware          - HTTPS redirect, security headers          │
│  2. CorsMiddleware              - CORS handling                             │
│  3. RequestLoggingMiddleware    - Request/response logging, X-Request-ID    │
│  4. TenantMiddleware            - Tenant context extraction                 │
│  5. AuthenticationMiddleware    - JWT validation, user context              │
│  6. RateLimitMiddleware         - Rate limiting per tenant/user             │
│  7. AuditMiddleware             - Audit trail logging                       │
│  8. ExceptionMiddleware         - Global exception handling                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              URL ROUTING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│  /api/v2/admin/*      → AdminRouter (Django Ninja) - SYSADMIN only          │
│  /api/v2/tenants/*    → TenantRouter (Django Ninja)                         │
│  /api/v2/projects/*   → ProjectRouter (Django Ninja)                        │
│  /api/v2/sessions/*   → SessionRouter (Django Ninja)                        │
│  /api/v2/voice/*      → VoiceRouter (Django Ninja)                          │
│  /api/v2/billing/*    → BillingRouter (Django Ninja)                        │
│  /ws/v2/*             → Django Channels Consumers                           │
│  /health              → Health Check Endpoint                               │
│  /metrics             → Prometheus Metrics                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Components and Interfaces

### 3.1 Django Project Structure

```
backend/
├── manage.py
├── pyproject.toml
├── Makefile
├── Dockerfile
├── docker-compose.yml
│
├── config/                             # Django configuration
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py                 # Settings loader
│   │   ├── base.py                     # Base settings
│   │   ├── development.py              # Dev overrides
│   │   ├── staging.py                  # Staging overrides
│   │   ├── production.py               # Production overrides
│   │   └── testing.py                  # Test overrides
│   ├── urls.py                         # Root URL configuration
│   ├── asgi.py                         # ASGI application
│   └── temporal.py                     # Temporal client configuration
│
├── apps/                               # Django applications
│   ├── core/                           # Core shared functionality
│   │   ├── middleware/                 # Custom middleware
│   │   │   ├── tenant.py               # Tenant context
│   │   │   ├── authentication.py       # JWT auth
│   │   │   ├── audit.py                # Audit logging
│   │   │   ├── rate_limit.py           # Rate limiting
│   │   │   ├── request_logging.py      # Request logging
│   │   │   └── exception_handler.py    # Exception handling
│   │   ├── permissions/                # SpiceDB integration
│   │   │   ├── spicedb_client.py       # gRPC client
│   │   │   ├── decorators.py           # @require_permission
│   │   │   └── schema.zed              # SpiceDB schema
│   │   ├── exceptions/                 # Custom exceptions
│   │   └── models.py                   # Base models
│   │
│   ├── tenants/                        # Multi-tenancy
│   │   ├── models.py                   # Tenant, TenantSettings
│   │   ├── api.py                      # Django Ninja router
│   │   ├── schemas.py                  # Pydantic schemas
│   │   ├── services.py                 # Business logic
│   │   └── workflows.py                # Temporal workflows
│   │
│   ├── users/                          # User management
│   ├── projects/                       # Project management
│   ├── api_keys/                       # API key management
│   ├── sessions/                       # Voice sessions
│   ├── billing/                        # Billing integration
│   ├── voice/                          # Voice configuration
│   ├── themes/                         # Theme management
│   ├── audit/                          # Audit logging
│   └── notifications/                  # Notifications
│
├── realtime/                           # Django Channels
│   ├── routing.py                      # WebSocket URL routing
│   ├── middleware.py                   # Channel middleware
│   └── consumers/                      # WebSocket consumers
│       ├── base.py                     # Base consumer
│       ├── events.py                   # Event consumer
│       ├── session.py                  # Session consumer
│       ├── transcription.py            # STT streaming
│       └── tts.py                      # TTS streaming
│
├── integrations/                       # External integrations (Django apps)
│   ├── keycloak/                       # Keycloak client
│   ├── spicedb/                        # SpiceDB client
│   ├── lago/                           # Lago billing
│   ├── vault/                          # HashiCorp Vault client
│   │   ├── __init__.py
│   │   ├── client.py                   # Vault client wrapper
│   │   ├── secrets.py                  # Secret retrieval
│   │   ├── transit.py                  # Encryption/decryption
│   │   └── pki.py                      # Certificate management
│   ├── temporal/                       # Temporal integration
│   │   ├── __init__.py
│   │   ├── client.py                   # Temporal client singleton
│   │   ├── decorators.py               # @workflow, @activity decorators
│   │   └── utils.py                    # Tenant context helpers
│   └── prometheus/                     # Metrics
│
├── apps/workflows/                     # Temporal workflows Django app
│   ├── __init__.py
│   ├── apps.py                         # Django app config
│   ├── activities/                     # Activity definitions
│   │   ├── __init__.py
│   │   ├── stt.py                      # STT activities
│   │   ├── tts.py                      # TTS activities
│   │   ├── llm.py                      # LLM activities
│   │   ├── billing.py                  # Billing activities
│   │   └── notifications.py            # Notification activities
│   ├── definitions/                    # Workflow definitions
│   │   ├── __init__.py
│   │   ├── voice_session.py            # Voice session workflow
│   │   ├── billing_sync.py             # Billing sync workflow
│   │   ├── cleanup.py                  # Cleanup workflow
│   │   └── onboarding.py               # Tenant onboarding workflow
│   ├── schedules/                      # Scheduled workflows
│   │   ├── __init__.py
│   │   └── periodic.py                 # Periodic workflow schedules
│   └── management/
│       └── commands/
│           └── run_temporal_worker.py  # Django management command
│
└── tests/                              # Integration tests
    ├── conftest.py                     # Pytest fixtures
    ├── integration/
    └── workflows/                      # Workflow tests
```

### 3.2 Core Interfaces

#### 3.2.1 Tenant Context Interface

```python
# Thread-local tenant context
def get_current_tenant() -> Optional[Tenant]:
    """Get the current tenant from thread-local storage."""

def set_current_tenant(tenant: Optional[Tenant]) -> None:
    """Set the current tenant in thread-local storage."""

def clear_current_tenant() -> None:
    """Clear the current tenant from thread-local storage."""
```

#### 3.2.2 SpiceDB Client Interface

```python
class SpiceDBClient:
    def check_permission(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        """Check if subject has permission on resource."""

    def write_relationship(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        """Write a relationship to SpiceDB."""

    def delete_relationship(...) -> bool:
        """Delete a relationship from SpiceDB."""

    def lookup_subjects(...) -> List[str]:
        """Look up all subjects with a relation to a resource."""
```

#### 3.2.3 API Key Service Interface

```python
class APIKeyService:
    @staticmethod
    def generate_key() -> Tuple[str, str, str]:
        """Generate new API key. Returns (full_key, prefix, hash)."""

    @staticmethod
    def validate_key(api_key: str) -> Dict[str, Any]:
        """Validate API key and return key data."""

    @staticmethod
    def revoke_key(key_id: UUID, user: User) -> None:
        """Revoke an API key."""

    @staticmethod
    def rotate_key(key_id: UUID, grace_period_hours: int = 0) -> str:
        """Rotate API key with optional grace period."""
```

#### 3.2.4 WebSocket Consumer Interface

```python
class BaseConsumer(AsyncJsonWebsocketConsumer):
    requires_auth: bool = True
    requires_tenant: bool = True
    allowed_roles: List[str] = []

    async def connect(self) -> None:
        """Handle WebSocket connection with auth validation."""

    async def disconnect(self, code: int) -> None:
        """Handle WebSocket disconnection."""

    async def receive_json(self, content: Dict[str, Any]) -> None:
        """Handle incoming JSON message."""

    async def send_error(self, code: str, message: str) -> None:
        """Send error message."""

    async def send_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Send event message."""
```

#### 3.2.5 Temporal Client Interface

```python
from temporalio.client import Client
from temporalio.worker import Worker

class TemporalClientManager:
    """Singleton manager for Temporal client connection."""
    
    _client: Optional[Client] = None
    
    @classmethod
    async def get_client(cls) -> Client:
        """Get or create Temporal client connection."""
        if cls._client is None:
            cls._client = await Client.connect(
                settings.TEMPORAL_HOST,
                namespace=settings.TEMPORAL_NAMESPACE,
            )
        return cls._client
    
    @classmethod
    async def start_workflow(
        cls,
        workflow: Type,
        args: Any,
        id: str,
        task_queue: str,
        **kwargs
    ) -> WorkflowHandle:
        """Start a workflow execution."""
        client = await cls.get_client()
        return await client.start_workflow(
            workflow.run,
            args,
            id=id,
            task_queue=task_queue,
            **kwargs
        )


class TenantAwareWorkflow:
    """Base class for tenant-aware workflows."""
    
    @workflow.defn
    class BaseWorkflow:
        tenant_id: str
        
        @workflow.run
        async def run(self, tenant_id: str, *args) -> Any:
            self.tenant_id = tenant_id
            # Workflow implementation
```

#### 3.2.6 Vault Client Interface

```python
import hvac

class VaultClient:
    """HashiCorp Vault client for secrets management."""
    
    def __init__(self):
        self.client = hvac.Client(
            url=settings.VAULT_ADDR,
            token=settings.VAULT_TOKEN,
        )
    
    def get_secret(self, path: str, mount_point: str = "secret") -> Dict[str, Any]:
        """Retrieve secret from KV v2 engine."""
        response = self.client.secrets.kv.v2.read_secret_version(
            path=path,
            mount_point=mount_point,
        )
        return response["data"]["data"]
    
    def get_database_credentials(self, role: str) -> Dict[str, str]:
        """Get dynamic database credentials."""
        response = self.client.secrets.database.generate_credentials(role)
        return {
            "username": response["data"]["username"],
            "password": response["data"]["password"],
            "lease_id": response["lease_id"],
            "lease_duration": response["lease_duration"],
        }
    
    def encrypt(self, plaintext: str, key_name: str) -> str:
        """Encrypt data using Transit engine."""
        response = self.client.secrets.transit.encrypt_data(
            name=key_name,
            plaintext=base64.b64encode(plaintext.encode()).decode(),
        )
        return response["data"]["ciphertext"]
    
    def decrypt(self, ciphertext: str, key_name: str) -> str:
        """Decrypt data using Transit engine."""
        response = self.client.secrets.transit.decrypt_data(
            name=key_name,
            ciphertext=ciphertext,
        )
        return base64.b64decode(response["data"]["plaintext"]).decode()
    
    def renew_lease(self, lease_id: str) -> Dict[str, Any]:
        """Renew a secret lease."""
        return self.client.sys.renew_lease(lease_id=lease_id)
```

---

## 4. Data Models

### 4.1 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                              ENTITY RELATIONSHIP DIAGRAM                             │
└─────────────────────────────────────────────────────────────────────────────────────┘

┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│     Tenant      │       │      User       │       │     Project     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (UUID) PK    │──┐    │ id (UUID) PK    │       │ id (UUID) PK    │
│ name            │  │    │ keycloak_id     │       │ tenant_id FK    │──┐
│ slug (unique)   │  │    │ email           │       │ name            │  │
│ tier            │  │    │ first_name      │       │ slug            │  │
│ status          │  │    │ last_name       │       │ description     │  │
│ billing_id      │  │    │ tenant_id FK    │──┐    │ settings (JSON) │  │
│ settings (JSON) │  │    │ is_active       │  │    │ created_by FK   │  │
│ max_users       │  │    │ preferences     │  │    │ created_at      │  │
│ max_projects    │  │    │ created_at      │  │    │ updated_at      │  │
│ max_api_keys    │  │    │ updated_at      │  │    └─────────────────┘  │
│ created_at      │  │    └─────────────────┘  │              │          │
│ updated_at      │  │              │          │              │          │
└─────────────────┘  │              │          │              │          │
         │           │              │          │              │          │
         │           └──────────────┼──────────┘              │          │
         │                          │                         │          │
         ▼                          ▼                         ▼          │
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐  │
│ TenantSettings  │       │     APIKey      │       │    Session      │  │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤  │
│ tenant_id FK PK │       │ id (UUID) PK    │       │ id (UUID) PK    │  │
│ logo_url        │       │ tenant_id FK    │──┐    │ tenant_id FK    │──┘
│ primary_color   │       │ name            │  │    │ project_id FK   │
│ default_voice   │       │ key_prefix      │  │    │ api_key_id FK   │
│ default_stt     │       │ key_hash        │  │    │ status          │
│ default_tts     │       │ scopes (array)  │  │    │ config (JSON)   │
│ default_llm     │       │ rate_limit_tier │  │    │ duration_sec    │
│ webhook_url     │       │ expires_at      │  │    │ input_tokens    │
│ require_mfa     │       │ revoked_at      │  │    │ output_tokens   │
│ session_timeout │       │ last_used_at    │  │    │ audio_duration  │
└─────────────────┘       │ usage_count     │  │    │ created_at      │
                          │ created_by FK   │  │    │ terminated_at   │
                          │ created_at      │  │    └─────────────────┘
                          └─────────────────┘  │              │
                                    │          │              │
                                    │          │              ▼
                                    │          │    ┌─────────────────┐
                                    │          │    │  SessionEvent   │
                                    │          │    ├─────────────────┤
                                    │          │    │ id (UUID) PK    │
                                    │          │    │ session_id FK   │
                                    │          │    │ event_type      │
                                    │          │    │ data (JSON)     │
                                    │          │    │ created_at      │
                                    │          │    └─────────────────┘
                                    │          │
                                    ▼          │
                          ┌─────────────────┐  │
                          │    AuditLog     │  │
                          ├─────────────────┤  │
                          │ id (UUID) PK    │  │
                          │ tenant_id FK    │──┘
                          │ actor_id        │
                          │ actor_email     │
                          │ actor_type      │
                          │ ip_address      │
                          │ action          │
                          │ resource_type   │
                          │ resource_id     │
                          │ description     │
                          │ old_values      │
                          │ new_values      │
                          │ created_at      │
                          └─────────────────┘
```

### 4.2 Tenant Model

```python
class Tenant(models.Model):
    """Multi-tenant organization model."""
    
    class Tier(models.TextChoices):
        FREE = "free", "Free"
        STARTER = "starter", "Starter"
        PRO = "pro", "Professional"
        ENTERPRISE = "enterprise", "Enterprise"
    
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        PENDING = "pending", "Pending Activation"
        DELETED = "deleted", "Deleted"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.FREE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    billing_id = models.CharField(max_length=255, blank=True)
    keycloak_group_id = models.CharField(max_length=255, blank=True)
    settings = models.JSONField(default=dict)
    
    # Tier-based limits
    max_users = models.PositiveIntegerField(default=5)
    max_projects = models.PositiveIntegerField(default=3)
    max_api_keys = models.PositiveIntegerField(default=10)
    max_sessions_per_month = models.PositiveIntegerField(default=1000)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "tenants"
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["tier"]),
        ]
```

### 4.3 User Model

```python
class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with Keycloak integration."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    keycloak_id = models.CharField(max_length=255, unique=True)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="users")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    preferences = models.JSONField(default=dict)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_at = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["keycloak_id"]
    
    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["keycloak_id"]),
            models.Index(fields=["email"]),
            models.Index(fields=["tenant", "is_active"]),
        ]
```

### 4.4 APIKey Model

```python
class APIKey(TenantScopedModel):
    """API key for programmatic access."""
    
    class Scope(models.TextChoices):
        REALTIME = "realtime", "Realtime API"
        BILLING = "billing", "Billing API"
        ADMIN = "admin", "Admin API"
    
    class RateLimitTier(models.TextChoices):
        STANDARD = "standard", "Standard (60/min)"
        ELEVATED = "elevated", "Elevated (120/min)"
        UNLIMITED = "unlimited", "Unlimited"
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    key_prefix = models.CharField(max_length=10)  # First 8 chars for identification
    key_hash = models.CharField(max_length=64)    # SHA-256 hash
    scopes = ArrayField(models.CharField(max_length=20), default=list)
    rate_limit_tier = models.CharField(
        max_length=20, 
        choices=RateLimitTier.choices, 
        default=RateLimitTier.STANDARD
    )
    
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = "api_keys"
        indexes = [
            models.Index(fields=["key_prefix"]),
            models.Index(fields=["tenant", "revoked_at"]),
        ]
```

### 4.5 Session Model

```python
class Session(TenantScopedModel):
    """Voice session model."""
    
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ERROR = "error", "Error"
        TERMINATED = "terminated", "Terminated"
    
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE, related_name="sessions")
    api_key = models.ForeignKey(APIKey, on_delete=models.SET_NULL, null=True, related_name="sessions")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CREATED)
    config = models.JSONField(default=dict)  # Voice, model, turn detection settings
    
    # Metrics
    duration_seconds = models.FloatField(default=0)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    audio_duration_seconds = models.FloatField(default=0)
    
    # Timestamps
    started_at = models.DateTimeField(null=True, blank=True)
    terminated_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "sessions"
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["project", "created_at"]),
            models.Index(fields=["api_key"]),
        ]
```

### 4.6 AuditLog Model

```python
class AuditLog(models.Model):
    """Immutable audit log for compliance."""
    
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
        API_CALL = "api_call", "API Call"
        PERMISSION_CHANGE = "permission_change", "Permission Change"
        SETTINGS_CHANGE = "settings_change", "Settings Change"
        BILLING_EVENT = "billing_event", "Billing Event"
    
    class ActorType(models.TextChoices):
        USER = "user", "User"
        API_KEY = "api_key", "API Key"
        SYSTEM = "system", "System"
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="audit_logs")
    
    # Actor information
    actor_id = models.CharField(max_length=255)
    actor_email = models.EmailField(blank=True)
    actor_type = models.CharField(max_length=20, choices=ActorType.choices)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Action details
    action = models.CharField(max_length=30, choices=Action.choices)
    resource_type = models.CharField(max_length=50)
    resource_id = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Change tracking
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["actor_id"]),
            models.Index(fields=["action"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]
    
    def save(self, *args, **kwargs):
        """Prevent updates to audit logs."""
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise ValueError("Audit logs are immutable and cannot be updated")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of audit logs."""
        raise ValueError("Audit logs are immutable and cannot be deleted")
```


### 4.7 Granular Permission Models

```python
class PlatformRole(models.TextChoices):
    """8 platform roles with hierarchical inheritance."""
    SAAS_ADMIN = "saas_admin", "SaaS Administrator"
    TENANT_ADMIN = "tenant_admin", "Tenant Administrator"
    AGENT_ADMIN = "agent_admin", "Agent Administrator"
    SUPERVISOR = "supervisor", "Supervisor"
    OPERATOR = "operator", "Operator"
    AGENT_USER = "agent_user", "Agent User"
    VIEWER = "viewer", "Viewer"
    BILLING_ADMIN = "billing_admin", "Billing Administrator"


class PermissionMatrix(models.Model):
    """
    Platform-level permission matrix mapping roles to resource:action tuples.
    Defines the default permissions for each role.
    """
    role = models.CharField(max_length=30, choices=PlatformRole.choices)
    resource = models.CharField(max_length=50)  # e.g., "agents", "sessions", "billing"
    action = models.CharField(max_length=30)    # e.g., "create", "read", "delete"
    allowed = models.BooleanField(default=False)
    conditions = models.JSONField(default=dict, blank=True)  # Optional contextual conditions
    
    class Meta:
        db_table = "permission_matrix"
        unique_together = ["role", "resource", "action"]
        indexes = [
            models.Index(fields=["role"]),
            models.Index(fields=["resource", "action"]),
        ]
    
    def __str__(self):
        status = "✓" if self.allowed else "✗"
        return f"{self.role}: {self.resource}:{self.action} [{status}]"


class TenantPermissionOverride(TenantScopedModel):
    """
    Tenant-level permission overrides.
    Allows tenant admins to customize permissions within their tenant.
    """
    role = models.CharField(max_length=30, choices=PlatformRole.choices)
    resource = models.CharField(max_length=50)
    action = models.CharField(max_length=30)
    allowed = models.BooleanField()
    conditions = models.JSONField(default=dict, blank=True)
    
    created_by = models.ForeignKey(
        "users.User", 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="permission_overrides_created"
    )
    
    class Meta:
        db_table = "tenant_permission_overrides"
        unique_together = ["tenant", "role", "resource", "action"]
        indexes = [
            models.Index(fields=["tenant", "role"]),
        ]


class UserRoleAssignment(TenantScopedModel):
    """
    User role assignments within a tenant.
    Supports multiple roles per user.
    """
    user = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        related_name="role_assignments"
    )
    role = models.CharField(max_length=30, choices=PlatformRole.choices)
    assigned_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="role_assignments_made"
    )
    assigned_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = "user_role_assignments"
        unique_together = ["tenant", "user", "role"]
        indexes = [
            models.Index(fields=["user", "role"]),
            models.Index(fields=["tenant", "role"]),
        ]
```

### 4.8 Permission Matrix Definition

The following table defines the 65+ granular resource:action permission tuples mapped to the 8 platform roles:

| Resource | Action | saas_admin | tenant_admin | agent_admin | supervisor | operator | agent_user | viewer | billing_admin |
|----------|--------|------------|--------------|-------------|------------|----------|------------|--------|---------------|
| **tenants** | read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **tenants** | update | ✓ | ✓ | - | - | - | - | - | - |
| **tenants** | delete | ✓ | - | - | - | - | - | - | - |
| **tenants** | manage_users | ✓ | ✓ | - | - | - | - | - | - |
| **tenants** | manage_settings | ✓ | ✓ | - | - | - | - | - | - |
| **tenants** | view_audit | ✓ | ✓ | - | - | - | - | - | - |
| **users** | create | ✓ | ✓ | - | - | - | - | - | - |
| **users** | read | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ | - |
| **users** | update | ✓ | ✓ | - | - | - | - | - | - |
| **users** | delete | ✓ | ✓ | - | - | - | - | - | - |
| **users** | assign_roles | ✓ | ✓ | - | - | - | - | - | - |
| **agents** | create | ✓ | ✓ | ✓ | - | - | - | - | - |
| **agents** | read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| **agents** | update | ✓ | ✓ | ✓ | - | - | - | - | - |
| **agents** | delete | ✓ | ✓ | ✓ | - | - | - | - | - |
| **agents** | deploy | ✓ | ✓ | ✓ | - | - | - | - | - |
| **agents** | configure | ✓ | ✓ | ✓ | - | - | - | - | - |
| **personas** | create | ✓ | ✓ | ✓ | - | - | - | - | - |
| **personas** | read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| **personas** | update | ✓ | ✓ | ✓ | - | - | - | - | - |
| **personas** | delete | ✓ | ✓ | ✓ | - | - | - | - | - |
| **personas** | assign | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| **sessions** | create | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | - |
| **sessions** | read | ✓ | ✓ | ✓ | ✓ | ✓ | own | ✓ | - |
| **sessions** | update | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| **sessions** | terminate | ✓ | ✓ | ✓ | ✓ | ✓ | own | - | - |
| **sessions** | monitor | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | - |
| **sessions** | takeover | ✓ | ✓ | - | ✓ | - | - | - | - |
| **conversations** | read | ✓ | ✓ | ✓ | ✓ | ✓ | own | ✓ | - |
| **conversations** | export | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| **conversations** | delete | ✓ | ✓ | - | - | - | - | - | - |
| **conversations** | annotate | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| **api_keys** | create | ✓ | ✓ | ✓ | - | - | - | - | - |
| **api_keys** | read | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | - |
| **api_keys** | revoke | ✓ | ✓ | ✓ | - | - | - | - | - |
| **api_keys** | rotate | ✓ | ✓ | ✓ | - | - | - | - | - |
| **projects** | create | ✓ | ✓ | ✓ | - | - | - | - | - |
| **projects** | read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| **projects** | update | ✓ | ✓ | ✓ | - | - | - | - | - |
| **projects** | delete | ✓ | ✓ | - | - | - | - | - | - |
| **projects** | manage_members | ✓ | ✓ | ✓ | - | - | - | - | - |
| **voice** | configure | ✓ | ✓ | ✓ | - | - | - | - | - |
| **voice** | read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| **voice** | test | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| **voice** | deploy | ✓ | ✓ | ✓ | - | - | - | - | - |
| **themes** | create | ✓ | ✓ | - | - | - | - | - | - |
| **themes** | read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - |
| **themes** | update | ✓ | ✓ | - | - | - | - | - | - |
| **themes** | delete | ✓ | ✓ | - | - | - | - | - | - |
| **themes** | apply | ✓ | ✓ | - | - | - | - | - | - |
| **billing** | read | ✓ | ✓ | - | - | - | - | - | ✓ |
| **billing** | manage | ✓ | - | - | - | - | - | - | ✓ |
| **billing** | export | ✓ | ✓ | - | - | - | - | - | ✓ |
| **billing** | configure_plans | ✓ | - | - | - | - | - | - | - |
| **analytics** | read | ✓ | ✓ | ✓ | ✓ | - | - | ✓ | ✓ |
| **analytics** | export | ✓ | ✓ | - | ✓ | - | - | - | ✓ |
| **analytics** | configure | ✓ | ✓ | - | - | - | - | - | - |
| **audit** | read | ✓ | ✓ | - | - | - | - | - | - |
| **audit** | export | ✓ | ✓ | - | - | - | - | - | - |
| **notifications** | read | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **notifications** | configure | ✓ | ✓ | - | - | - | - | - | - |
| **notifications** | send | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| **workflows** | create | ✓ | ✓ | ✓ | - | - | - | - | - |
| **workflows** | read | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ | - |
| **workflows** | execute | ✓ | ✓ | ✓ | ✓ | ✓ | - | - | - |
| **workflows** | cancel | ✓ | ✓ | ✓ | ✓ | - | - | - | - |
| **admin** | platform_settings | ✓ | - | - | - | - | - | - | - |
| **admin** | tenant_management | ✓ | - | - | - | - | - | - | - |
| **admin** | user_impersonation | ✓ | - | - | - | - | - | - | - |
| **admin** | system_health | ✓ | - | - | - | - | - | - | - |

*Note: "own" indicates the user can only access their own resources.*

### 4.9 Granular Permission Service

```python
class GranularPermissionService:
    """
    Service for checking granular resource:action permissions.
    Implements hierarchical permission resolution with tenant overrides.
    """
    
    @staticmethod
    def check_permission(
        user: "User",
        resource: str,
        action: str,
        resource_id: Optional[str] = None,
    ) -> bool:
        """
        Check if user has permission for resource:action.
        
        Resolution order:
        1. Check tenant-level overrides
        2. Fall back to platform-level defaults
        3. Optionally check SpiceDB for relationship-based access
        """
        from apps.core.middleware.tenant import get_current_tenant
        
        tenant = get_current_tenant()
        if not tenant:
            return False
        
        # Get user's roles
        user_roles = GranularPermissionService.get_user_roles(user)
        
        for role in user_roles:
            # Check tenant override first
            override = TenantPermissionOverride.objects.filter(
                tenant=tenant,
                role=role,
                resource=resource,
                action=action,
            ).first()
            
            if override is not None:
                if override.allowed:
                    return GranularPermissionService._check_conditions(
                        override.conditions, user, resource_id
                    )
                continue  # Explicitly denied, check next role
            
            # Fall back to platform default
            platform_perm = PermissionMatrix.objects.filter(
                role=role,
                resource=resource,
                action=action,
            ).first()
            
            if platform_perm and platform_perm.allowed:
                return GranularPermissionService._check_conditions(
                    platform_perm.conditions, user, resource_id
                )
        
        return False
    
    @staticmethod
    def get_user_roles(user: "User") -> List[str]:
        """Get all roles assigned to a user."""
        from apps.core.middleware.tenant import get_current_tenant
        
        tenant = get_current_tenant()
        if not tenant:
            return []
        
        # Get roles from UserRoleAssignment
        assignments = UserRoleAssignment.objects.filter(
            tenant=tenant,
            user=user,
            expires_at__isnull=True,  # Not expired
        ).values_list("role", flat=True)
        
        roles = list(assignments)
        
        # Add primary role from user model if exists
        if hasattr(user, "role") and user.role:
            if user.role not in roles:
                roles.append(user.role)
        
        return roles
    
    @staticmethod
    def get_effective_permissions(user: "User") -> List[str]:
        """Get all effective permissions for a user as resource:action strings."""
        from apps.core.middleware.tenant import get_current_tenant
        
        tenant = get_current_tenant()
        if not tenant:
            return []
        
        user_roles = GranularPermissionService.get_user_roles(user)
        permissions = set()
        
        for role in user_roles:
            # Get platform permissions
            platform_perms = PermissionMatrix.objects.filter(
                role=role,
                allowed=True,
            ).values_list("resource", "action")
            
            for resource, action in platform_perms:
                perm_key = f"{resource}:{action}"
                
                # Check if overridden at tenant level
                override = TenantPermissionOverride.objects.filter(
                    tenant=tenant,
                    role=role,
                    resource=resource,
                    action=action,
                ).first()
                
                if override is None or override.allowed:
                    permissions.add(perm_key)
        
        return sorted(permissions)
    
    @staticmethod
    def _check_conditions(
        conditions: Dict,
        user: "User",
        resource_id: Optional[str],
    ) -> bool:
        """Check contextual conditions for permission."""
        if not conditions:
            return True
        
        # Handle "own" condition - user can only access their own resources
        if conditions.get("own_only"):
            if resource_id and str(user.id) != resource_id:
                return False
        
        return True
```

### 4.10 AuthBearer Class for Django Ninja

```python
from ninja.security import HttpBearer
from typing import Optional, Any

class AuthBearer(HttpBearer):
    """
    JWT/API Key authentication for Django Ninja endpoints.
    Validates tokens and attaches user context to request.auth.
    """
    
    def authenticate(self, request, token: str) -> Optional[Any]:
        """
        Authenticate request using JWT token or API key.
        
        Returns user context dict on success, None on failure.
        """
        # Try JWT authentication
        if self._is_jwt_token(token):
            return self._validate_jwt(request, token)
        
        # Try API key authentication
        return self._validate_api_key(request, token)
    
    def _is_jwt_token(self, token: str) -> bool:
        """Check if token looks like a JWT."""
        return token.count(".") == 2
    
    def _validate_jwt(self, request, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token and return user context."""
        import jwt
        from django.conf import settings
        from django.core.cache import cache
        
        try:
            # Get cached public key
            public_key = self._get_keycloak_public_key()
            
            # Decode and validate
            claims = jwt.decode(
                token,
                public_key,
                algorithms=settings.KEYCLOAK["ALGORITHMS"],
                audience=settings.KEYCLOAK["AUDIENCE"],
                options={"verify_exp": True},
            )
            
            # Build user context
            return {
                "user_id": claims.get("sub"),
                "tenant_id": claims.get("tenant_id"),
                "email": claims.get("email"),
                "roles": claims.get("realm_access", {}).get("roles", []),
                "auth_type": "jwt",
                "claims": claims,
            }
        
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def _validate_api_key(self, request, token: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return user context."""
        from apps.api_keys.services import APIKeyService
        
        try:
            key_data = APIKeyService.validate_key(
                token,
                ip_address=self._get_client_ip(request),
            )
            return {
                "user_id": key_data.get("user_id"),
                "tenant_id": key_data.get("tenant_id"),
                "api_key_id": key_data.get("api_key_id"),
                "scopes": key_data.get("scopes", []),
                "auth_type": "api_key",
            }
        except Exception:
            return None
    
    def _get_keycloak_public_key(self) -> str:
        """Fetch and cache Keycloak public key."""
        import requests
        from django.conf import settings
        from django.core.cache import cache
        
        cache_key = "keycloak_public_key"
        public_key = cache.get(cache_key)
        
        if not public_key:
            url = f"{settings.KEYCLOAK['URL']}/realms/{settings.KEYCLOAK['REALM']}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            realm_info = response.json()
            public_key_raw = realm_info["public_key"]
            public_key = f"-----BEGIN PUBLIC KEY-----\n{public_key_raw}\n-----END PUBLIC KEY-----"
            
            cache.set(cache_key, public_key, timeout=3600)
        
        return public_key
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.headers.get("X-Forwarded-For")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
```

### 4.11 @require_permission Decorator (Enhanced)

```python
from functools import wraps
from typing import Callable, Optional
from django.http import JsonResponse

def require_permission(permission: str, resource_id_param: Optional[str] = None):
    """
    Decorator to require granular resource:action permission.
    
    Args:
        permission: Permission string in format "resource:action"
        resource_id_param: Optional parameter name containing resource ID
    
    Usage:
        @require_permission("agents:create")
        def create_agent(request):
            ...
        
        @require_permission("sessions:read", resource_id_param="session_id")
        def get_session(request, session_id: UUID):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            from apps.core.exceptions import PermissionDeniedError
            
            # Get user from request
            user = getattr(request, "user", None)
            if not user or not user.is_authenticated:
                raise PermissionDeniedError("Authentication required")
            
            # Parse permission string
            parts = permission.split(":")
            if len(parts) != 2:
                raise ValueError(f"Invalid permission format: {permission}")
            
            resource, action = parts
            
            # Get resource ID if specified
            resource_id = None
            if resource_id_param and resource_id_param in kwargs:
                resource_id = str(kwargs[resource_id_param])
            
            # Check permission
            if not GranularPermissionService.check_permission(
                user=user,
                resource=resource,
                action=action,
                resource_id=resource_id,
            ):
                raise PermissionDeniedError(
                    f"Permission '{permission}' denied",
                    details={"required_permission": permission}
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator
```

---

## 5. Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Environment Variable Validation

*For any* set of required environment variables, if any are missing or invalid when the application starts, the system SHALL fail fast with a clear error message identifying the missing variables.

**Validates: Requirements 1.3, 1.7**

### Property 2: Tenant Context Extraction

*For any* valid tenant identifier provided via JWT claims, X-Tenant-ID header, or subdomain, the TenantMiddleware SHALL correctly extract and set the tenant context in thread-local storage.

**Validates: Requirements 2.4**

### Property 3: Tenant Access Control

*For any* request to a tenant-scoped endpoint, if the tenant context is missing OR the tenant is suspended/deleted, the system SHALL reject the request with appropriate HTTP status (400 for missing, 403 for suspended).

**Validates: Requirements 2.6, 2.7**

### Property 4: Tenant-Scoped Model Isolation

*For any* query on a TenantScopedModel, the results SHALL only include records belonging to the current tenant. *For any* save operation on a TenantScopedModel without explicit tenant, the current tenant SHALL be automatically set.

**Validates: Requirements 2.8, 2.9**

### Property 5: JWT Authentication Validation

*For any* JWT token in the Authorization header, valid tokens SHALL be accepted and set user context, expired tokens SHALL return 401 with "token_expired", and malformed tokens SHALL return 401 with "invalid_token".

**Validates: Requirements 3.1, 3.5, 3.6**


### Property 6: API Key Authentication

*For any* API key in the X-API-Key header, valid keys SHALL authenticate successfully, expired keys SHALL return 401 with "api_key_expired", and revoked keys SHALL return 401 with "api_key_revoked".

**Validates: Requirements 3.9, 7.9, 7.10**

### Property 7: API Key Lifecycle Round-Trip

*For any* generated API key, the key SHALL match format `avb_{random_32_bytes}`, only the SHA-256 hash SHALL be stored, the full key SHALL only be returned once at creation, and subsequent validation SHALL correctly identify valid keys by hash comparison.

**Validates: Requirements 7.2, 7.3, 7.4, 7.7**

### Property 8: SpiceDB Permission Enforcement

*For any* permission check via SpiceDB, the check_permission result SHALL accurately reflect the permission state, and denied permissions SHALL return 403 with "permission_denied".

**Validates: Requirements 4.2, 4.11**

### Property 8A: Granular Permission Matrix Enforcement

*For any* request to a protected endpoint, the @require_permission("resource:action") decorator SHALL:
1. Extract user roles from JWT claims or user model
2. Check tenant-level overrides first, then platform defaults
3. Return 403 with "permission_denied" if no matching permission found
4. Allow access only if at least one role grants the permission

**Validates: Requirements 4A.3, 4A.4**

### Property 8B: Hierarchical Permission Resolution

*For any* permission check, tenant-level overrides SHALL take precedence over platform-level defaults. The effective permission SHALL be the merged result of platform defaults with tenant overrides applied.

**Validates: Requirements 4A.5**

### Property 9: Pydantic Schema Validation

*For any* API request with invalid body, the system SHALL return 400 Bad Request with field-level error details identifying each validation failure.

**Validates: Requirements 5.2, 5.8**

### Property 10: WebSocket Authentication

*For any* WebSocket connection, authenticated connections SHALL have user and tenant set in scope, and unauthenticated connections SHALL close with code 4001.

**Validates: Requirements 6.3, 6.10**

### Property 11: Session Auto-Termination

*For any* voice session that exceeds 24 hours duration, the system SHALL automatically terminate it and update status to "terminated".

**Validates: Requirements 8.10**

### Property 12: Task Retry with Backoff

*For any* Temporal workflow activity that fails, the system SHALL retry up to 3 times with exponential backoff before marking as permanently failed.

**Validates: Requirements 9.9**


### Property 13: Cache Tenant Isolation

*For any* cache operation, keys SHALL be prefixed with tenant ID ensuring complete isolation between tenants' cached data.

**Validates: Requirements 10.1**

### Property 14: Rate Limiting Enforcement

*For any* request that exceeds the rate limit, the system SHALL return 429 Too Many Requests with X-RateLimit-* headers and retry_after value.

**Validates: Requirements 10.7**

### Property 15: Request ID Generation

*For any* HTTP request, the system SHALL generate a unique request_id and return it in the X-Request-ID response header.

**Validates: Requirements 11.3**

### Property 16: Audit Log Immutability

*For any* attempt to update or delete an AuditLog record, the system SHALL raise an error preventing the operation.

**Validates: Requirements 12.5**

### Property 17: Exception Sanitization

*For any* unexpected exception in production mode, the system SHALL return a generic error message without exposing stack traces or internal details.

**Validates: Requirements 13.6**

### Property 18: Vault Secret Retrieval

*For any* secret request to Vault, valid paths SHALL return decrypted secrets, and expired leases SHALL trigger automatic renewal or re-fetch of credentials.

**Validates: Requirements 15.4, 15.7**

### Property 19: Vault Transit Encryption Round-Trip

*For any* plaintext data encrypted via Vault Transit engine, decrypting the ciphertext SHALL return the original plaintext.

**Validates: Requirements 15.6**

### Property 20: Vault Startup Validation

*For any* application startup, if Vault is unavailable or authentication fails, the system SHALL fail fast with a clear error message.

**Validates: Requirements 15.10**

---

## 6. Error Handling

### 6.1 Exception Hierarchy

```python
# Base exception
APIException(Exception)
├── status_code: int
├── error_code: str
└── default_message: str

# Validation errors (400)
ValidationError(APIException)
└── details: Dict[str, List[str]]  # Field-level errors

# Authentication errors (401)
AuthenticationError(APIException)
├── TokenExpiredError
├── InvalidTokenError
└── APIKeyExpiredError

# Authorization errors (403)
PermissionDeniedError(APIException)
├── InsufficientScopeError
├── TenantSuspendedError
└── TenantLimitExceededError

# Not found errors (404)
NotFoundError(APIException)
├── TenantNotFoundError
├── UserNotFoundError
└── ResourceNotFoundError

# Conflict errors (409)
ConflictError(APIException)
└── DuplicateResourceError

# Rate limit errors (429)
RateLimitError(APIException)
└── retry_after: int
```


### 6.2 Error Response Format

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field_name": ["Validation error 1", "Validation error 2"]
  },
  "request_id": "uuid-request-id"
}
```

### 6.3 HTTP Status Code Mapping

| Status | Error Code | Description |
|--------|------------|-------------|
| 400 | validation_error | Request validation failed |
| 401 | token_expired | JWT token has expired |
| 401 | invalid_token | JWT token is malformed |
| 401 | api_key_expired | API key has expired |
| 401 | api_key_revoked | API key has been revoked |
| 403 | permission_denied | Insufficient permissions |
| 403 | tenant_suspended | Tenant account suspended |
| 403 | tenant_limit_exceeded | Tenant quota exceeded |
| 404 | not_found | Resource not found |
| 409 | conflict | Resource already exists |
| 429 | rate_limit_exceeded | Too many requests |
| 500 | internal_error | Unexpected server error |

### 6.4 WebSocket Error Codes

| Code | Description |
|------|-------------|
| 4001 | Authentication failed |
| 4002 | Tenant context required |
| 4003 | Permission denied |
| 4004 | Resource not found |
| 4008 | Rate limit exceeded |
| 4009 | Session terminated |

---

## 7. Testing Strategy

### 7.1 Testing Framework

- **Unit Tests**: pytest with pytest-django
- **Property Tests**: Hypothesis with `hypothesis.extra.django` extension
- **Integration Tests**: pytest with test containers
- **API Tests**: pytest with Django test client
- **WebSocket Tests**: pytest-asyncio with channels testing

### 7.2 Django-Specific Hypothesis Configuration

The `hypothesis.extra.django` extension provides Django-specific testing capabilities:

1. **`hypothesis.extra.django.TestCase`** - Django test case with per-example transactions
2. **`hypothesis.extra.django.TransactionTestCase`** - For tests needing transaction control
3. **`hypothesis.extra.django.from_model()`** - Strategy for generating Django model instances

```python
# conftest.py - Django-specific Hypothesis configuration
from hypothesis import settings as hypothesis_settings, HealthCheck
from hypothesis.extra.django import TestCase as HypothesisTestCase

# Minimum 100 iterations per property test
hypothesis_settings.register_profile(
    "default",
    max_examples=100,
    deadline=5000,  # 5 seconds
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
hypothesis_settings.register_profile(
    "ci",
    max_examples=200,
    deadline=10000,  # 10 seconds for CI
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
```

### 7.3 Model Generation with from_model()

```python
from hypothesis.extra.django import from_model
from hypothesis import given, strategies as st
from apps.tenants.models import Tenant

# Generate valid Tenant instances automatically
tenant_strategy = from_model(
    Tenant,
    tier=st.sampled_from(["free", "starter", "pro", "enterprise"]),
    status=st.sampled_from(["active", "suspended", "pending"]),
)

# Use in property tests
@given(tenant=tenant_strategy)
def test_tenant_properties(tenant):
    """Hypothesis generates valid Tenant instances respecting field validators."""
    assert tenant.pk is not None
    assert tenant.tier in ["free", "starter", "pro", "enterprise"]
```

### 7.4 Property Test Examples

```python
from hypothesis.extra.django import from_model, TestCase as HypothesisTestCase
from hypothesis import given, strategies as st
import pytest

# Property 4: Tenant-Scoped Model Isolation
class TestTenantScopedModelIsolation(HypothesisTestCase):
    """Uses HypothesisTestCase for per-example transaction isolation."""
    
    @given(tenant=from_model(Tenant, status=st.just("active")))
    def test_tenant_scoped_queryset_isolation(self, tenant):
        """For any tenant, queries only return that tenant's records."""
        set_current_tenant(tenant)
        
        # Create records for this tenant
        record = TenantScopedModel.objects.create(name="test", tenant=tenant)
        
        results = TenantScopedModel.objects.all()
        assert all(r.tenant_id == tenant.id for r in results)

# Property 7: API Key Lifecycle Round-Trip
@pytest.mark.django_db(transaction=True)
@given(key_name=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))
def test_api_key_round_trip(key_name):
    """Generated keys can be validated by hash comparison."""
    full_key, prefix, key_hash = APIKeyService.generate_key()
    
    assert full_key.startswith("avb_")
    assert len(full_key) == 47  # avb_ + 43 chars
    assert APIKeyService.hash_key(full_key) == key_hash
    assert full_key[:12] == prefix

# Property 16: Audit Log Immutability
@pytest.mark.django_db(transaction=True)
@given(audit_log=from_model(
    AuditLog,
    action=st.sampled_from(["create", "update", "delete"]),
    resource_type=st.sampled_from(["tenant", "user", "session"]),
))
def test_audit_log_immutable(audit_log):
    """Audit logs cannot be updated or deleted."""
    # Record is already saved by from_model()
    
    with pytest.raises(ValueError, match="immutable"):
        audit_log.description = "modified"
        audit_log.save()
    
    with pytest.raises(ValueError, match="immutable"):
        audit_log.delete()
```

### 7.4 Test Coverage Requirements

| Component | Minimum Coverage |
|-----------|------------------|
| Models | 90% |
| Services | 85% |
| API Endpoints | 80% |
| Middleware | 90% |
| WebSocket Consumers | 80% |
| Temporal Workflows | 75% |

---

## 8. Deployment Architecture

### 8.1 Local Development Constraints

**CRITICAL: 15GB RAM Total Limit for Docker Cluster**

All containers must be tuned for production-like behavior within localhost resource constraints.

### 8.2 Container Memory Allocation (15GB Total)

| Service | Memory Limit | Memory Reservation | Purpose |
|---------|--------------|-------------------|---------|
| PostgreSQL | 2GB | 1GB | Primary database + Temporal |
| Redis | 512MB | 256MB | Cache, sessions, pub/sub |
| Keycloak | 1.5GB | 1GB | Identity provider |
| SpiceDB | 512MB | 256MB | Authorization |
| Django Backend | 2GB | 1GB | API server (2 workers) |
| Temporal Server | 1GB | 512MB | Workflow orchestration |
| Temporal Worker | 1GB | 512MB | Activity execution |
| Vault | 256MB | 128MB | Secrets management |
| Nginx | 256MB | 128MB | Reverse proxy |
| Prometheus | 512MB | 256MB | Metrics collection |
| Grafana | 512MB | 256MB | Dashboards |
| **Reserved** | 4.5GB | - | OS, buffers, headroom |
| **TOTAL** | 15GB | - | |


### 8.3 Docker Compose - Production-Like Local Development

```yaml
# docker-compose.yml
version: "3.9"

x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

x-healthcheck-defaults: &healthcheck-defaults
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s

services:
  # ==========================================================================
  # REVERSE PROXY
  # ==========================================================================
  nginx:
    image: nginx:1.25-alpine
    container_name: avb_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_cache:/var/cache/nginx
    deploy:
      resources:
        limits:
          memory: 256M
        reservations:
          memory: 128M
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped

  # ==========================================================================
  # APPLICATION SERVICES
  # ==========================================================================
  backend:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: avb_backend
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DB_HOST=postgres
      - DB_NAME=agentvoicebox
      - DB_USER=agentvoicebox
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_CONN_MAX_AGE=60
      - REDIS_URL=redis://redis:6379/0
      - TEMPORAL_HOST=temporal:7233
      - TEMPORAL_NAMESPACE=agentvoicebox
      - VAULT_ADDR=http://vault:8200
      - KEYCLOAK_URL=http://keycloak:8080
      - KEYCLOAK_REALM=agentvoicebox
      - SPICEDB_ENDPOINT=spicedb:50051
      - SPICEDB_TOKEN=${SPICEDB_TOKEN}
      - DJANGO_SECRET_KEY=${DJANGO_SECRET_KEY}
      - ALLOWED_HOSTS=localhost,127.0.0.1,backend
      - GUNICORN_WORKERS=2
      - GUNICORN_THREADS=4
      - GUNICORN_TIMEOUT=120
      - GUNICORN_KEEPALIVE=5
    expose:
      - "8000"
    volumes:
      - backend_static:/app/staticfiles
      - backend_media:/app/media
      - backend_logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "2.0"
        reservations:
          memory: 1G
          cpus: "0.5"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      keycloak:
        condition: service_healthy
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]


  # ==========================================================================
  # TEMPORAL WORKFLOW ORCHESTRATION
  # ==========================================================================
  temporal:
    image: temporalio/auto-setup:1.24
    container_name: avb_temporal
    environment:
      - DB=postgresql
      - DB_PORT=5432
      - POSTGRES_USER=agentvoicebox
      - POSTGRES_PWD=${DB_PASSWORD}
      - POSTGRES_SEEDS=postgres
      - DYNAMIC_CONFIG_FILE_PATH=/etc/temporal/config/dynamicconfig/development.yaml
      - ENABLE_ES=false
      - TEMPORAL_ADDRESS=temporal:7233
      - TEMPORAL_CLI_ADDRESS=temporal:7233
    ports:
      - "7233:7233"
    volumes:
      - ./temporal/dynamicconfig:/etc/temporal/config/dynamicconfig:ro
      - temporal_data:/var/lib/temporal
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "1.0"
        reservations:
          memory: 512M
          cpus: "0.25"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "temporal", "workflow", "list", "--namespace", "default"]
      start_period: 120s

  temporal-ui:
    image: temporalio/ui:2.26.2
    container_name: avb_temporal_ui
    environment:
      - TEMPORAL_ADDRESS=temporal:7233
      - TEMPORAL_CORS_ORIGINS=http://localhost:3000
    ports:
      - "8088:8080"
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.5"
        reservations:
          memory: 128M
          cpus: "0.1"
    depends_on:
      - temporal
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped

  temporal-worker:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: avb_temporal_worker
    command: python manage.py run_temporal_worker
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.production
      - DB_HOST=postgres
      - DB_NAME=agentvoicebox
      - DB_USER=agentvoicebox
      - DB_PASSWORD=${DB_PASSWORD}
      - REDIS_URL=redis://redis:6379/0
      - TEMPORAL_HOST=temporal:7233
      - TEMPORAL_NAMESPACE=agentvoicebox
      - VAULT_ADDR=http://vault:8200
      - VAULT_TOKEN=${VAULT_TOKEN}
    volumes:
      - backend_logs:/app/logs
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "2.0"
        reservations:
          memory: 512M
          cpus: "0.25"
    depends_on:
      - temporal
      - redis
      - vault
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped

  # ==========================================================================
  # SECRETS MANAGEMENT
  # ==========================================================================
  vault:
    image: hashicorp/vault:1.15
    container_name: avb_vault
    cap_add:
      - IPC_LOCK
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: ${VAULT_TOKEN}
      VAULT_DEV_LISTEN_ADDRESS: 0.0.0.0:8200
      VAULT_ADDR: http://127.0.0.1:8200
    ports:
      - "8200:8200"
    volumes:
      - vault_data:/vault/data
      - ./vault/config:/vault/config:ro
      - ./vault/policies:/vault/policies:ro
    deploy:
      resources:
        limits:
          memory: 256M
          cpus: "0.5"
        reservations:
          memory: 128M
          cpus: "0.1"
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "vault", "status"]


  # ==========================================================================
  # DATABASE
  # ==========================================================================
  postgres:
    image: postgres:16-alpine
    container_name: avb_postgres
    environment:
      POSTGRES_DB: agentvoicebox
      POSTGRES_USER: agentvoicebox
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.UTF-8"
      # Production-tuned settings
      POSTGRES_HOST_AUTH_METHOD: scram-sha-256
    command:
      - "postgres"
      - "-c" 
      - "max_connections=200"
      - "-c"
      - "shared_buffers=512MB"
      - "-c"
      - "effective_cache_size=1536MB"
      - "-c"
      - "maintenance_work_mem=128MB"
      - "-c"
      - "checkpoint_completion_target=0.9"
      - "-c"
      - "wal_buffers=16MB"
      - "-c"
      - "default_statistics_target=100"
      - "-c"
      - "random_page_cost=1.1"
      - "-c"
      - "effective_io_concurrency=200"
      - "-c"
      - "work_mem=2621kB"
      - "-c"
      - "min_wal_size=1GB"
      - "-c"
      - "max_wal_size=4GB"
      - "-c"
      - "max_worker_processes=4"
      - "-c"
      - "max_parallel_workers_per_gather=2"
      - "-c"
      - "max_parallel_workers=4"
      - "-c"
      - "max_parallel_maintenance_workers=2"
      - "-c"
      - "log_statement=mod"
      - "-c"
      - "log_duration=on"
      - "-c"
      - "log_min_duration_statement=1000"
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - postgres_backups:/backups
      - ./postgres/init:/docker-entrypoint-initdb.d:ro
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: "2.0"
        reservations:
          memory: 1G
          cpus: "0.5"
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD-SHELL", "pg_isready -U agentvoicebox -d agentvoicebox"]


  # ==========================================================================
  # CACHE & MESSAGE BROKER
  # ==========================================================================
  redis:
    image: redis:7-alpine
    container_name: avb_redis
    command:
      - "redis-server"
      - "--appendonly"
      - "yes"
      - "--appendfsync"
      - "everysec"
      - "--maxmemory"
      - "400mb"
      - "--maxmemory-policy"
      - "allkeys-lru"
      - "--tcp-keepalive"
      - "300"
      - "--timeout"
      - "0"
      - "--tcp-backlog"
      - "511"
      - "--databases"
      - "16"
      - "--save"
      - "900 1"
      - "--save"
      - "300 10"
      - "--save"
      - "60 10000"
      - "--loglevel"
      - "notice"
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
        reservations:
          memory: 256M
          cpus: "0.25"
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s

  # ==========================================================================
  # AUTHENTICATION
  # ==========================================================================
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: avb_keycloak
    command:
      - "start"
      - "--optimized"
      - "--http-enabled=true"
      - "--http-port=8080"
      - "--hostname-strict=false"
      - "--proxy=edge"
      - "--cache=local"
    environment:
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: agentvoicebox
      KC_DB_PASSWORD: ${DB_PASSWORD}
      KC_HEALTH_ENABLED: "true"
      KC_METRICS_ENABLED: "true"
      KEYCLOAK_ADMIN: ${KEYCLOAK_ADMIN}
      KEYCLOAK_ADMIN_PASSWORD: ${KEYCLOAK_ADMIN_PASSWORD}
      KC_LOG_LEVEL: INFO
      JAVA_OPTS_APPEND: "-Xms512m -Xmx1024m -XX:MetaspaceSize=96M -XX:MaxMetaspaceSize=256m"
    ports:
      - "8080:8080"
    volumes:
      - keycloak_data:/opt/keycloak/data
      - ./keycloak/themes:/opt/keycloak/themes:ro
      - ./keycloak/realm-export.json:/opt/keycloak/data/import/realm-export.json:ro
    deploy:
      resources:
        limits:
          memory: 1536M
          cpus: "1.5"
        reservations:
          memory: 1G
          cpus: "0.5"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD-SHELL", "exec 3<>/dev/tcp/127.0.0.1/8080"]
      start_period: 120s


  # ==========================================================================
  # AUTHORIZATION
  # ==========================================================================
  spicedb:
    image: authzed/spicedb:v1.30.0
    container_name: avb_spicedb
    command:
      - "serve"
      - "--grpc-preshared-key=${SPICEDB_TOKEN}"
      - "--datastore-engine=postgres"
      - "--datastore-conn-uri=postgres://agentvoicebox:${DB_PASSWORD}@postgres:5432/spicedb?sslmode=disable"
      - "--datastore-gc-window=24h"
      - "--telemetry-endpoint="
      - "--log-level=info"
    ports:
      - "50051:50051"
      - "8443:8443"
    volumes:
      - spicedb_data:/var/lib/spicedb
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "1.0"
        reservations:
          memory: 256M
          cpus: "0.25"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "grpc_health_probe", "-addr=:50051"]

  # ==========================================================================
  # OBSERVABILITY
  # ==========================================================================
  prometheus:
    image: prom/prometheus:v2.48.0
    container_name: avb_prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--storage.tsdb.retention.time=15d"
      - "--storage.tsdb.retention.size=1GB"
      - "--web.enable-lifecycle"
      - "--web.enable-admin-api"
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/alerts:/etc/prometheus/alerts:ro
      - prometheus_data:/prometheus
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
        reservations:
          memory: 256M
          cpus: "0.1"
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD", "wget", "-q", "--spider", "http://localhost:9090/-/healthy"]

  grafana:
    image: grafana/grafana:10.2.0
    container_name: avb_grafana
    environment:
      GF_SECURITY_ADMIN_USER: ${GRAFANA_ADMIN_USER:-admin}
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
      GF_USERS_ALLOW_SIGN_UP: "false"
      GF_SERVER_ROOT_URL: "http://localhost:3001"
      GF_INSTALL_PLUGINS: "grafana-clock-panel,grafana-piechart-panel"
      GF_DATABASE_TYPE: sqlite3
      GF_LOG_LEVEL: warn
    ports:
      - "3001:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
        reservations:
          memory: 256M
          cpus: "0.1"
    depends_on:
      - prometheus
    networks:
      - avb-network
    logging: *default-logging
    restart: unless-stopped
    healthcheck:
      <<: *healthcheck-defaults
      test: ["CMD-SHELL", "wget -q --spider http://localhost:3000/api/health"]


# ==========================================================================
# PERSISTENT VOLUMES
# ==========================================================================
volumes:
  # Database volumes
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/postgres
  postgres_backups:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/backups

  # Cache volumes
  redis_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/redis

  # Auth volumes
  keycloak_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/keycloak

  # Authorization volumes
  spicedb_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/spicedb

  # Application volumes
  backend_static:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/static
  backend_media:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/media
  backend_logs:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/logs

  # Temporal volumes
  temporal_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/temporal

  # Vault volumes
  vault_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/vault

  # Proxy volumes
  nginx_cache:
    driver: local

  # Observability volumes
  prometheus_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/prometheus
  grafana_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: ${PWD}/data/grafana

# ==========================================================================
# NETWORKS
# ==========================================================================
networks:
  avb-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```


### 8.4 Dockerfile (Multi-Stage Production Build)

```dockerfile
# Dockerfile
# ==========================================================================
# BASE STAGE
# ==========================================================================
FROM python:3.12-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# ==========================================================================
# BUILDER STAGE
# ==========================================================================
FROM base as builder

# Install Python dependencies
COPY requirements/production.txt requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ==========================================================================
# PRODUCTION STAGE
# ==========================================================================
FROM base as production

# Create non-root user
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Install wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appgroup . .

# Create required directories
RUN mkdir -p /app/staticfiles /app/media /app/logs \
    && chown -R appuser:appgroup /app

# Collect static files
RUN python manage.py collectstatic --noinput

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command (Gunicorn with Uvicorn workers)
CMD ["gunicorn", "config.asgi:application", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", \
     "--workers", "2", \
     "--threads", "4", \
     "--worker-connections", "1000", \
     "--max-requests", "10000", \
     "--max-requests-jitter", "1000", \
     "--timeout", "120", \
     "--graceful-timeout", "30", \
     "--keep-alive", "5", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--capture-output", \
     "--enable-stdio-inheritance"]
```


### 8.5 Kubernetes Deployment (Production)

```yaml
# k8s/backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: avb-backend
  labels:
    app: avb-backend
    tier: backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: avb-backend
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  template:
    metadata:
      labels:
        app: avb-backend
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8000"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: avb-backend
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
        - name: backend
          image: agentvoicebox/backend:latest
          imagePullPolicy: Always
          ports:
            - containerPort: 8000
              protocol: TCP
          envFrom:
            - configMapRef:
                name: avb-backend-config
            - secretRef:
                name: avb-backend-secrets
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health/live/
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
            timeoutSeconds: 5
            failureThreshold: 3
          readinessProbe:
            httpGet:
              path: /health/ready/
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 3
          volumeMounts:
            - name: static-files
              mountPath: /app/staticfiles
            - name: media-files
              mountPath: /app/media
      volumes:
        - name: static-files
          persistentVolumeClaim:
            claimName: avb-static-pvc
        - name: media-files
          persistentVolumeClaim:
            claimName: avb-media-pvc
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: avb-backend
                topologyKey: kubernetes.io/hostname
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: avb-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: avb-backend
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
        - type: Pods
          value: 4
          periodSeconds: 15
      selectPolicy: Max
```


### 8.6 Environment Variables (.env.example)

```bash
# ==========================================================================
# DATABASE
# ==========================================================================
DB_PASSWORD=secure_password_here
DB_HOST=postgres
DB_NAME=agentvoicebox
DB_USER=agentvoicebox
DB_PORT=5432

# ==========================================================================
# DJANGO
# ==========================================================================
DJANGO_SECRET_KEY=your-secret-key-min-50-chars-here
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=localhost,127.0.0.1

# ==========================================================================
# REDIS
# ==========================================================================
REDIS_URL=redis://redis:6379/0

# ==========================================================================
# TEMPORAL
# ==========================================================================
TEMPORAL_HOST=temporal:7233
TEMPORAL_NAMESPACE=agentvoicebox

# ==========================================================================
# VAULT
# ==========================================================================
VAULT_ADDR=http://vault:8200
VAULT_TOKEN=your-vault-root-token

# ==========================================================================
# KEYCLOAK
# ==========================================================================
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=agentvoicebox
KEYCLOAK_CLIENT_ID=agentvoicebox-backend
KEYCLOAK_CLIENT_SECRET=your-client-secret
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=secure_admin_password

# ==========================================================================
# SPICEDB
# ==========================================================================
SPICEDB_ENDPOINT=spicedb:50051
SPICEDB_TOKEN=your-preshared-key

# ==========================================================================
# LAGO BILLING
# ==========================================================================
LAGO_API_URL=http://lago:3000
LAGO_API_KEY=your-lago-api-key
LAGO_WEBHOOK_SECRET=your-webhook-secret

# ==========================================================================
# OBSERVABILITY
# ==========================================================================
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_grafana_password
SENTRY_DSN=https://your-sentry-dsn

# ==========================================================================
# FEATURE FLAGS
# ==========================================================================
FF_VOICE_CLONING=false
FF_CUSTOM_THEMES=true
FF_BILLING=true
```

---

## 9. Summary

This design document provides a complete technical specification for the Django SaaS backend with:

1. **Multi-Tenancy**: Thread-local context, tenant-scoped models, automatic filtering
2. **Authentication**: Keycloak JWT + API key support with automatic user sync
3. **Authorization**: SpiceDB fine-grained permissions with 6 roles (SYSADMIN, ADMIN, DEVELOPER, OPERATOR, VIEWER, BILLING)
4. **API Layer**: Django Ninja with Pydantic schemas, service layer pattern
5. **Real-Time**: Django Channels WebSocket consumers for voice sessions
6. **Workflow Orchestration**: Temporal workflows with durable execution, tenant-aware activities, scheduled workflows
7. **Secrets Management**: HashiCorp Vault for dynamic credentials, encryption, and PKI
8. **Observability**: Structlog, Prometheus metrics, audit logging
9. **Security**: Exception handling, rate limiting, security headers
10. **Deployment**: Production-tuned Docker Compose (15GB RAM limit), Kubernetes manifests

All 20 correctness properties are testable via property-based testing with Hypothesis.
