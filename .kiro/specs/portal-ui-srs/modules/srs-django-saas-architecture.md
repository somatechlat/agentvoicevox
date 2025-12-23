# Software Requirements Specification (SRS)

## Django SaaS Architecture - AgentVoiceBox Platform

**Document Identifier:** AVB-SRS-ARCH-DJANGO-001  
**Version:** 1.0.0  
**Date:** 2025-12-23  
**Status:** Draft  
**Classification:** Internal  
**Parent Document:** AVB-SRS-UI-001  

---

## Document Control

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2025-12-23 | Engineering | Initial draft - Complete Django SaaS Architecture |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Architecture Overview](#2-architecture-overview)
3. [Django Project Structure](#3-django-project-structure)
4. [Django Settings Architecture](#4-django-settings-architecture)
5. [Multi-Tenancy Architecture](#5-multi-tenancy-architecture)
6. [Authentication & Authorization](#6-authentication--authorization)
7. [Django Ninja API Layer](#7-django-ninja-api-layer)
8. [Django Channels WebSocket](#8-django-channels-websocket)
9. [Database Layer](#9-database-layer)
10. [Caching & Session Management](#10-caching--session-management)
11. [Background Tasks & Workers](#11-background-tasks--workers)
12. [Logging & Observability](#12-logging--observability)
13. [Security Architecture](#13-security-architecture)
14. [Deployment Architecture](#14-deployment-architecture)

---

## 1. Introduction

### 1.1 Purpose

This document specifies the complete Django SaaS architecture for the AgentVoiceBox platform, including all Django patterns, middleware, logging classes, service layers, and enterprise-grade components required for a production multi-tenant SaaS application.

### 1.2 Scope

- Django 5.x with ASGI (Daphne/Uvicorn)
- Django Ninja for REST API
- Django Channels for WebSocket
- Multi-tenant architecture with tenant isolation
- Keycloak integration for authentication
- SpiceDB for fine-grained authorization
- PostgreSQL with connection pooling
- Redis for caching and sessions
- Celery for background tasks
- Comprehensive logging and observability

### 1.3 Technology Stack

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | Django | 5.1+ | Core web framework |
| API | Django Ninja | 1.3+ | REST API with OpenAPI |
| WebSocket | Django Channels | 4.0+ | Real-time communication |
| Database | PostgreSQL | 16+ | Primary data store |
| Cache | Redis | 7+ | Caching, sessions, pub/sub |
| Auth | Keycloak | 24+ | Identity provider |
| AuthZ | SpiceDB | 1.30+ | Fine-grained permissions |
| Tasks | Celery | 5.4+ | Background job processing |
| Broker | Redis | 7+ | Celery message broker |
| Billing | Lago | Latest | Usage-based billing |
| Secrets | HashiCorp Vault | 1.15+ | Secrets management |
| Monitoring | Prometheus + Grafana | Latest | Metrics and dashboards |
| Logging | Structlog | 24.1+ | Structured logging |
| Tracing | OpenTelemetry | 1.25+ | Distributed tracing |

### 1.4 Design Principles

1. **Separation of Concerns**: Clear boundaries between layers
2. **Dependency Injection**: Loose coupling via interfaces
3. **Domain-Driven Design**: Business logic in service layer
4. **CQRS Pattern**: Separate read/write operations where beneficial
5. **Event-Driven**: Async communication via events
6. **Fail-Fast**: Early validation and error detection
7. **Defense in Depth**: Multiple security layers

---

## 2. Architecture Overview

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
└───────────────────────────────────┘   │                                           │
                                        │  ┌─────────────────────────────────────┐ │
                                        │  │  Middleware Stack                    │ │
                                        │  │  • TenantMiddleware                  │ │
                                        │  │  • AuthenticationMiddleware          │ │
                                        │  │  • AuditMiddleware                   │ │
                                        │  │  • RateLimitMiddleware               │ │
                                        │  │  • RequestLoggingMiddleware          │ │
                                        │  └─────────────────────────────────────┘ │
                                        │                                           │
                                        │  ┌─────────────────────────────────────┐ │
                                        │  │  Service Layer                       │ │
                                        │  │  • TenantService                     │ │
                                        │  │  • UserService                       │ │
                                        │  │  • SessionService                    │ │
                                        │  │  • BillingService                    │ │
                                        │  │  • VoiceService                      │ │
                                        │  └─────────────────────────────────────┘ │
                                        └───────────────────────────────────────────┘
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
│  • Projects         │              │  • Celery Broker            │    │  • JWT Tokens       │
│  • API Keys         │              │  • Channel Layers           │    │  • User Federation  │
│  • Sessions         │              │  • Rate Limit Counters      │    │                     │
│  • Audit Logs       │              │  • Pub/Sub Events           │    │                     │
└─────────────────────┘              └─────────────────────────────┘    └─────────────────────┘
          │                                               │
          │                                               │
          ▼                                               ▼
┌─────────────────────┐              ┌─────────────────────────────┐
│     SpiceDB         │              │      Celery Workers         │
│   Port: 50051       │              │                             │
│                     │              │  • STT Worker               │
│  • Permission       │              │  • TTS Worker               │
│    Relationships    │              │  • LLM Worker               │
│  • RBAC Policies    │              │  • Email Worker             │
│  • Tenant Isolation │              │  • Billing Worker           │
└─────────────────────┘              │  • Cleanup Worker           │
                                     └─────────────────────────────┘
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
│                                                                             │
│  1. SecurityMiddleware          - HTTPS redirect, security headers          │
│  2. CorsMiddleware              - CORS handling                             │
│  3. RequestLoggingMiddleware    - Request/response logging                  │
│  4. TenantMiddleware            - Tenant context extraction                 │
│  5. AuthenticationMiddleware    - JWT validation, user context              │
│  6. RateLimitMiddleware         - Rate limiting per tenant/user             │
│  7. AuditMiddleware             - Audit trail logging                       │
│  8. ExceptionMiddleware         - Global exception handling                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              URL ROUTING                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  /api/v2/admin/*      → AdminRouter (Django Ninja)                          │
│  /api/v2/tenants/*    → TenantRouter (Django Ninja)                         │
│  /api/v2/projects/*   → ProjectRouter (Django Ninja)                        │
│  /api/v2/sessions/*   → SessionRouter (Django Ninja)                        │
│  /api/v2/voice/*      → VoiceRouter (Django Ninja)                          │
│  /api/v2/billing/*    → BillingRouter (Django Ninja)                        │
│  /api/v2/themes/*     → ThemeRouter (Django Ninja)                          │
│  /ws/v2/*             → Django Channels Consumers                           │
│  /health              → Health Check Endpoint                               │
│  /metrics             → Prometheus Metrics                                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SERVICE LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  TenantService  │  │   UserService   │  │ SessionService  │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ BillingService  │  │  VoiceService   │  │  ThemeService   │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │  AuditService   │  │ PermissionSvc   │  │ NotificationSvc │             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          REPOSITORY LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │ TenantRepository│  │ UserRepository  │  │SessionRepository│             │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  Django ORM with QuerySet optimization, select_related, prefetch_related    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Django Project Structure

### 3.1 Directory Layout

```
ovos-voice-agent/AgentVoiceBoxEngine/backend/
├── manage.py                           # Django management script
├── pyproject.toml                      # Project dependencies (Poetry/PDM)
├── Makefile                            # Development commands
├── Dockerfile                          # Production container
├── docker-compose.yml                  # Local development stack
│
├── config/                             # Django configuration package
│   ├── __init__.py
│   ├── settings/                       # Split settings
│   │   ├── __init__.py                 # Settings loader
│   │   ├── base.py                     # Base settings (all environments)
│   │   ├── development.py              # Development overrides
│   │   ├── staging.py                  # Staging overrides
│   │   ├── production.py               # Production overrides
│   │   └── testing.py                  # Test overrides
│   ├── urls.py                         # Root URL configuration
│   ├── asgi.py                         # ASGI application
│   ├── wsgi.py                         # WSGI application (fallback)
│   └── celery.py                       # Celery configuration
│
├── apps/                               # Django applications
│   ├── __init__.py
│   │
│   ├── core/                           # Core shared functionality
│   │   ├── __init__.py
│   │   ├── apps.py                     # App configuration
│   │   ├── middleware/                 # Custom middleware
│   │   │   ├── __init__.py
│   │   │   ├── tenant.py               # Tenant context middleware
│   │   │   ├── authentication.py       # JWT authentication
│   │   │   ├── audit.py                # Audit logging
│   │   │   ├── rate_limit.py           # Rate limiting
│   │   │   ├── request_logging.py      # Request/response logging
│   │   │   └── exception_handler.py    # Global exception handling
│   │   ├── permissions/                # Permission system
│   │   │   ├── __init__.py
│   │   │   ├── spicedb_client.py       # SpiceDB gRPC client
│   │   │   ├── decorators.py           # @require_permission
│   │   │   ├── mixins.py               # Permission mixins
│   │   │   └── schema.zed              # SpiceDB schema
│   │   ├── exceptions/                 # Custom exceptions
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # Base exception classes
│   │   │   ├── auth.py                 # Authentication exceptions
│   │   │   ├── tenant.py               # Tenant exceptions
│   │   │   └── validation.py           # Validation exceptions
│   │   ├── logging/                    # Logging configuration
│   │   │   ├── __init__.py
│   │   │   ├── config.py               # Structlog configuration
│   │   │   ├── processors.py           # Custom log processors
│   │   │   └── formatters.py           # Log formatters
│   │   ├── utils/                      # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── crypto.py               # Encryption utilities
│   │   │   ├── validators.py           # Custom validators
│   │   │   ├── pagination.py           # Pagination helpers
│   │   │   └── datetime.py             # DateTime utilities
│   │   └── management/                 # Management commands
│   │       └── commands/
│   │           ├── seed_data.py        # Seed initial data
│   │           ├── sync_permissions.py # Sync SpiceDB schema
│   │           └── cleanup_sessions.py # Cleanup old sessions
│   │
│   ├── tenants/                        # Multi-tenancy
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # Tenant, TenantSettings
│   │   ├── api.py                      # Django Ninja router
│   │   ├── schemas.py                  # Pydantic schemas
│   │   ├── services.py                 # Business logic
│   │   ├── repositories.py             # Data access
│   │   ├── signals.py                  # Django signals
│   │   ├── tasks.py                    # Celery tasks
│   │   └── tests/
│   │       ├── __init__.py
│   │       ├── test_models.py
│   │       ├── test_api.py
│   │       └── test_services.py
│   │
│   ├── users/                          # User management
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # User, UserProfile
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── repositories.py
│   │   └── tests/
│   │
│   ├── projects/                       # Project management
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # Project, ProjectSettings
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── tests/
│   │
│   ├── api_keys/                       # API key management
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # APIKey, APIKeyScope
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── hashers.py                  # Secure key hashing
│   │   └── tests/
│   │
│   ├── sessions/                       # Voice sessions
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # Session, SessionEvent
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── consumers.py                # WebSocket consumers
│   │   └── tests/
│   │
│   ├── billing/                        # Billing integration
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # Subscription, Invoice, Usage
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── lago_client.py              # Lago API client
│   │   ├── webhooks.py                 # Lago webhook handlers
│   │   └── tests/
│   │
│   ├── voice/                          # Voice configuration
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # VoiceConfig, Persona, WakeWord
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── providers/                  # Voice providers
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # Abstract provider
│   │   │   ├── local.py                # Local STT/TTS
│   │   │   └── agentvoicebox.py        # AgentVoiceBox API
│   │   └── tests/
│   │
│   ├── themes/                         # Theme management
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # Theme, ThemeVariable
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   ├── validators.py               # XSS, contrast validation
│   │   └── tests/
│   │
│   ├── audit/                          # Audit logging
│   │   ├── __init__.py
│   │   ├── apps.py
│   │   ├── models.py                   # AuditLog
│   │   ├── api.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── tests/
│   │
│   └── notifications/                  # Notifications
│       ├── __init__.py
│       ├── apps.py
│       ├── models.py                   # Notification, NotificationPreference
│       ├── api.py
│       ├── schemas.py
│       ├── services.py
│       ├── channels/                   # Notification channels
│       │   ├── __init__.py
│       │   ├── email.py
│       │   ├── websocket.py
│       │   └── webhook.py
│       └── tests/
│
├── realtime/                           # Django Channels
│   ├── __init__.py
│   ├── routing.py                      # WebSocket URL routing
│   ├── consumers/                      # WebSocket consumers
│   │   ├── __init__.py
│   │   ├── base.py                     # Base consumer class
│   │   ├── events.py                   # Event consumer
│   │   ├── session.py                  # Session consumer
│   │   ├── transcription.py            # STT streaming
│   │   └── tts.py                      # TTS streaming
│   ├── middleware.py                   # Channel middleware
│   └── events.py                       # Event type definitions
│
├── integrations/                       # External integrations
│   ├── __init__.py
│   ├── keycloak/                       # Keycloak integration
│   │   ├── __init__.py
│   │   ├── client.py                   # Keycloak admin client
│   │   ├── auth.py                     # JWT validation
│   │   └── sync.py                     # User sync
│   ├── spicedb/                        # SpiceDB integration
│   │   ├── __init__.py
│   │   ├── client.py                   # gRPC client
│   │   └── schema.zed                  # Permission schema
│   ├── lago/                           # Lago billing
│   │   ├── __init__.py
│   │   ├── client.py                   # API client
│   │   └── webhooks.py                 # Webhook handlers
│   ├── vault/                          # HashiCorp Vault
│   │   ├── __init__.py
│   │   └── client.py                   # Secrets client
│   └── prometheus/                     # Prometheus metrics
│       ├── __init__.py
│       └── metrics.py                  # Custom metrics
│
├── workers/                            # Celery workers
│   ├── __init__.py
│   ├── stt/                            # STT worker
│   │   ├── __init__.py
│   │   ├── tasks.py
│   │   └── processor.py
│   ├── tts/                            # TTS worker
│   │   ├── __init__.py
│   │   ├── tasks.py
│   │   └── processor.py
│   ├── llm/                            # LLM worker
│   │   ├── __init__.py
│   │   ├── tasks.py
│   │   └── processor.py
│   └── scheduled/                      # Scheduled tasks
│       ├── __init__.py
│       ├── cleanup.py
│       ├── billing_sync.py
│       └── metrics_aggregation.py
│
├── migrations/                         # Database migrations
│   └── versions/
│
├── static/                             # Static files
│   └── admin/
│
├── templates/                          # Django templates
│   ├── emails/
│   └── admin/
│
└── tests/                              # Integration tests
    ├── __init__.py
    ├── conftest.py                     # Pytest fixtures
    ├── factories.py                    # Factory Boy factories
    └── integration/
        ├── test_auth_flow.py
        ├── test_tenant_isolation.py
        └── test_billing_flow.py
```

---

## 4. Django Settings Architecture

### 4.1 Base Settings (config/settings/base.py)

```python
"""
Base Django settings for AgentVoiceBox.
All environment-specific settings inherit from this.
"""
from pathlib import Path
from datetime import timedelta
import os

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# CORE DJANGO SETTINGS
# =============================================================================

DEBUG = False
ALLOWED_HOSTS: list[str] = []

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # PostgreSQL-specific features
]

THIRD_PARTY_APPS = [
    "ninja",                    # Django Ninja API
    "channels",                 # Django Channels WebSocket
    "corsheaders",              # CORS handling
    "django_celery_beat",       # Celery periodic tasks
    "django_celery_results",    # Celery result backend
    "health_check",             # Health checks
    "health_check.db",
    "health_check.cache",
    "health_check.storage",
    "django_prometheus",        # Prometheus metrics
    "django_structlog",         # Structured logging
]

LOCAL_APPS = [
    "apps.core",
    "apps.tenants",
    "apps.users",
    "apps.projects",
    "apps.api_keys",
    "apps.sessions",
    "apps.billing",
    "apps.voice",
    "apps.themes",
    "apps.audit",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# =============================================================================
# MIDDLEWARE CONFIGURATION
# =============================================================================

MIDDLEWARE = [
    # Security (first)
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    
    # Prometheus metrics
    "django_prometheus.middleware.PrometheusBeforeMiddleware",
    
    # Request logging (early for timing)
    "apps.core.middleware.request_logging.RequestLoggingMiddleware",
    
    # Standard Django
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    
    # Custom authentication (replaces Django's)
    "apps.core.middleware.authentication.KeycloakAuthenticationMiddleware",
    
    # Tenant context (after auth)
    "apps.core.middleware.tenant.TenantMiddleware",
    
    # Rate limiting
    "apps.core.middleware.rate_limit.RateLimitMiddleware",
    
    # Audit logging
    "apps.core.middleware.audit.AuditMiddleware",
    
    # Standard Django (continued)
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    
    # Exception handling (last)
    "apps.core.middleware.exception_handler.ExceptionHandlerMiddleware",
    
    # Prometheus metrics (last)
    "django_prometheus.middleware.PrometheusAfterMiddleware",
]

# =============================================================================
# URL CONFIGURATION
# =============================================================================

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# =============================================================================
# TEMPLATES
# =============================================================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "agentvoicebox"),
        "USER": os.environ.get("DB_USER", "agentvoicebox"),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 10,
            "options": "-c statement_timeout=30000",  # 30s query timeout
        },
    }
}

# Database connection pooling (via pgbouncer or django-db-connection-pool)
DATABASE_POOL_ARGS = {
    "max_overflow": 10,
    "pool_size": 5,
    "recycle": 300,
}

# =============================================================================
# CACHE CONFIGURATION
# =============================================================================

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
            "RETRY_ON_TIMEOUT": True,
            "MAX_CONNECTIONS": 50,
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
            "SERIALIZER": "django_redis.serializers.json.JSONSerializer",
        },
        "KEY_PREFIX": "avb",
    },
    "sessions": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "avb_session",
    },
    "rate_limit": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_URL", "redis://localhost:6379/2"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
        "KEY_PREFIX": "avb_rl",
    },
}

# =============================================================================
# SESSION CONFIGURATION
# =============================================================================

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "sessions"
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_NAME = "avb_session"

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = [
    "apps.core.middleware.authentication.KeycloakBackend",
]

# Keycloak configuration
KEYCLOAK_CONFIG = {
    "SERVER_URL": os.environ.get("KEYCLOAK_URL", "http://localhost:8080"),
    "REALM": os.environ.get("KEYCLOAK_REALM", "agentvoicebox"),
    "CLIENT_ID": os.environ.get("KEYCLOAK_CLIENT_ID", "agentvoicebox-backend"),
    "CLIENT_SECRET": os.environ.get("KEYCLOAK_CLIENT_SECRET", ""),
    "VERIFY_SSL": os.environ.get("KEYCLOAK_VERIFY_SSL", "true").lower() == "true",
    "ALGORITHMS": ["RS256"],
    "AUDIENCE": "agentvoicebox",
    "LEEWAY": 10,  # seconds
}

# =============================================================================
# AUTHORIZATION (SpiceDB)
# =============================================================================

SPICEDB_CONFIG = {
    "ENDPOINT": os.environ.get("SPICEDB_ENDPOINT", "localhost:50051"),
    "TOKEN": os.environ.get("SPICEDB_TOKEN", ""),
    "INSECURE": os.environ.get("SPICEDB_INSECURE", "false").lower() == "true",
    "TIMEOUT": 5,  # seconds
}

# =============================================================================
# DJANGO CHANNELS (WebSocket)
# =============================================================================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://localhost:6379/3")],
            "capacity": 1500,
            "expiry": 10,
        },
    },
}

# =============================================================================
# CELERY CONFIGURATION
# =============================================================================

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/4")
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "default"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 240  # 4 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_WORKER_CONCURRENCY = 4

CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

CELERY_TASK_ROUTES = {
    "workers.stt.*": {"queue": "stt"},
    "workers.tts.*": {"queue": "tts"},
    "workers.llm.*": {"queue": "llm"},
    "workers.scheduled.*": {"queue": "scheduled"},
    "apps.billing.tasks.*": {"queue": "billing"},
    "apps.notifications.tasks.*": {"queue": "notifications"},
}

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")

# HTTPS settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookie security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

# Content security
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# =============================================================================
# CORS CONFIGURATION
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:25007",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-tenant-id",
    "x-request-id",
]

# =============================================================================
# RATE LIMITING
# =============================================================================

RATE_LIMIT_CONFIG = {
    "DEFAULT": {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
    },
    "API_KEY": {
        "requests_per_minute": 120,
        "requests_per_hour": 5000,
    },
    "ADMIN": {
        "requests_per_minute": 300,
        "requests_per_hour": 10000,
    },
}

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "apps.core.logging.formatters.JSONFormatter",
        },
        "console": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "json_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": BASE_DIR / "logs" / "app.json",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console", "json_file"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

# Structlog configuration
DJANGO_STRUCTLOG_CELERY_ENABLED = True

# =============================================================================
# EXTERNAL SERVICES
# =============================================================================

# Lago billing
LAGO_CONFIG = {
    "API_URL": os.environ.get("LAGO_API_URL", "http://localhost:3000"),
    "API_KEY": os.environ.get("LAGO_API_KEY", ""),
    "WEBHOOK_SECRET": os.environ.get("LAGO_WEBHOOK_SECRET", ""),
}

# Vault secrets
VAULT_CONFIG = {
    "URL": os.environ.get("VAULT_URL", "http://localhost:8200"),
    "TOKEN": os.environ.get("VAULT_TOKEN", ""),
    "MOUNT_POINT": "secret",
}

# =============================================================================
# FEATURE FLAGS
# =============================================================================

FEATURE_FLAGS = {
    "VOICE_CLONING_ENABLED": os.environ.get("FF_VOICE_CLONING", "false").lower() == "true",
    "CUSTOM_THEMES_ENABLED": os.environ.get("FF_CUSTOM_THEMES", "true").lower() == "true",
    "BILLING_ENABLED": os.environ.get("FF_BILLING", "true").lower() == "true",
}

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

### 4.2 Environment-Specific Settings

#### Development Settings (config/settings/development.py)

```python
"""Development environment settings."""
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

# Disable SSL in development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Debug toolbar
INSTALLED_APPS += ["debug_toolbar"]
MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
INTERNAL_IPS = ["127.0.0.1"]

# Email backend
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Logging
LOGGING["root"]["level"] = "DEBUG"
LOGGING["loggers"]["apps"]["level"] = "DEBUG"
LOGGING["loggers"]["django.db.backends"]["level"] = "DEBUG"
```

#### Production Settings (config/settings/production.py)

```python
"""Production environment settings."""
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.redis import RedisIntegration

DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# Security
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000

# Sentry error tracking
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN"),
    integrations=[
        DjangoIntegration(),
        CeleryIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    environment="production",
)

# Static files (WhiteNoise)
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
```

---

## 5. Multi-Tenancy Architecture

### 5.1 Tenant Model

```python
# apps/tenants/models.py
"""Multi-tenant models for AgentVoiceBox."""
from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone
import uuid


class TenantManager(models.Manager):
    """Custom manager for tenant queries."""
    
    def active(self):
        """Return only active tenants."""
        return self.filter(status=Tenant.Status.ACTIVE)
    
    def with_usage(self):
        """Return tenants with usage statistics."""
        return self.annotate(
            session_count=models.Count("sessions"),
            api_key_count=models.Count("api_keys"),
            user_count=models.Count("users"),
        )


class Tenant(models.Model):
    """
    Represents a tenant organization in the multi-tenant system.
    All tenant-scoped data references this model.
    """
    
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
    
    # Primary key
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # Basic info
    name = models.CharField(
        max_length=255,
        help_text="Display name of the organization",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        help_text="URL-safe identifier (e.g., 'acme-corp')",
    )
    
    # Subscription
    tier = models.CharField(
        max_length=20,
        choices=Tier.choices,
        default=Tier.FREE,
    )
    
    # External IDs
    billing_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Lago customer ID",
    )
    keycloak_group_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="Keycloak group ID for this tenant",
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    
    # Settings (JSON)
    settings = models.JSONField(
        default=dict,
        help_text="Tenant-specific settings",
    )
    
    # Limits (based on tier)
    max_users = models.PositiveIntegerField(default=5)
    max_projects = models.PositiveIntegerField(default=3)
    max_api_keys = models.PositiveIntegerField(default=10)
    max_sessions_per_month = models.PositiveIntegerField(default=1000)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Custom manager
    objects = TenantManager()
    
    class Meta:
        db_table = "tenants"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["slug"]),
            models.Index(fields=["status"]),
            models.Index(fields=["tier"]),
            models.Index(fields=["billing_id"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.slug})"
    
    def activate(self):
        """Activate the tenant."""
        self.status = self.Status.ACTIVE
        self.activated_at = timezone.now()
        self.save(update_fields=["status", "activated_at", "updated_at"])
    
    def suspend(self, reason: str = ""):
        """Suspend the tenant."""
        self.status = self.Status.SUSPENDED
        self.suspended_at = timezone.now()
        self.settings["suspension_reason"] = reason
        self.save(update_fields=["status", "suspended_at", "settings", "updated_at"])
    
    def soft_delete(self):
        """Soft delete the tenant."""
        self.status = self.Status.DELETED
        self.deleted_at = timezone.now()
        self.save(update_fields=["status", "deleted_at", "updated_at"])


class TenantSettings(models.Model):
    """
    Extended settings for a tenant.
    Separated from main model for cleaner organization.
    """
    
    tenant = models.OneToOneField(
        Tenant,
        on_delete=models.CASCADE,
        related_name="extended_settings",
    )
    
    # Branding
    logo_url = models.URLField(blank=True)
    primary_color = models.CharField(max_length=7, default="#6366f1")
    
    # Voice defaults
    default_voice_provider = models.CharField(
        max_length=50,
        default="local",
        choices=[
            ("disabled", "Disabled"),
            ("local", "Local"),
            ("agentvoicebox", "AgentVoiceBox"),
        ],
    )
    default_stt_model = models.CharField(max_length=50, default="base")
    default_tts_voice = models.CharField(max_length=50, default="am_onyx")
    default_llm_provider = models.CharField(max_length=50, default="groq")
    default_llm_model = models.CharField(max_length=100, default="llama-3.1-8b-instant")
    
    # Notifications
    email_notifications_enabled = models.BooleanField(default=True)
    webhook_url = models.URLField(blank=True)
    
    # Security
    allowed_ip_ranges = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True,
    )
    require_mfa = models.BooleanField(default=False)
    session_timeout_minutes = models.PositiveIntegerField(default=60)
    
    class Meta:
        db_table = "tenant_settings"
```

### 5.2 Tenant Middleware

```python
# apps/core/middleware/tenant.py
"""Tenant context middleware for multi-tenancy."""
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from typing import Callable, Optional
import threading

from apps.tenants.models import Tenant
from apps.core.exceptions.tenant import (
    TenantNotFoundError,
    TenantSuspendedError,
    TenantRequiredError,
)

# Thread-local storage for tenant context
_tenant_context = threading.local()


def get_current_tenant() -> Optional[Tenant]:
    """Get the current tenant from thread-local storage."""
    return getattr(_tenant_context, "tenant", None)


def set_current_tenant(tenant: Optional[Tenant]) -> None:
    """Set the current tenant in thread-local storage."""
    _tenant_context.tenant = tenant


def clear_current_tenant() -> None:
    """Clear the current tenant from thread-local storage."""
    if hasattr(_tenant_context, "tenant"):
        del _tenant_context.tenant


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to extract and validate tenant context from requests.
    
    Tenant can be identified via:
    1. JWT claim (tenant_id)
    2. X-Tenant-ID header
    3. Subdomain (tenant.example.com)
    4. URL path (/api/v2/tenants/{tenant_id}/...)
    """
    
    # Paths that don't require tenant context
    EXEMPT_PATHS = [
        "/health",
        "/metrics",
        "/api/v2/auth/",
        "/api/v2/admin/",  # Admin routes use different auth
        "/ws/v2/admin/",
    ]
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Extract tenant context from request."""
        # Clear any existing tenant context
        clear_current_tenant()
        
        # Check if path is exempt
        if self._is_exempt_path(request.path):
            return None
        
        # Try to extract tenant ID
        tenant_id = self._extract_tenant_id(request)
        
        if not tenant_id:
            # For authenticated requests, tenant is required
            if hasattr(request, "user") and request.user.is_authenticated:
                raise TenantRequiredError("Tenant context is required")
            return None
        
        # Load and validate tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        
        # Check tenant status
        if tenant.status == Tenant.Status.SUSPENDED:
            raise TenantSuspendedError(f"Tenant {tenant.name} is suspended")
        
        if tenant.status == Tenant.Status.DELETED:
            raise TenantNotFoundError(f"Tenant {tenant_id} not found")
        
        # Set tenant context
        set_current_tenant(tenant)
        request.tenant = tenant
        
        return None
    
    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Clean up tenant context after request."""
        clear_current_tenant()
        return response
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from tenant requirement."""
        return any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)
    
    def _extract_tenant_id(self, request: HttpRequest) -> Optional[str]:
        """Extract tenant ID from various sources."""
        # 1. From JWT claims (set by auth middleware)
        if hasattr(request, "auth") and request.auth:
            tenant_id = request.auth.get("tenant_id")
            if tenant_id:
                return tenant_id
        
        # 2. From header
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # 3. From subdomain
        host = request.get_host().split(":")[0]
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain not in ["www", "api", "admin"]:
                # Look up tenant by slug
                try:
                    tenant = Tenant.objects.get(slug=subdomain)
                    return str(tenant.id)
                except Tenant.DoesNotExist:
                    pass
        
        return None


class TenantQuerySetMixin:
    """
    Mixin for models that belong to a tenant.
    Automatically filters querysets by current tenant.
    """
    
    def get_queryset(self):
        """Filter queryset by current tenant."""
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs
```

### 5.3 Tenant-Scoped Base Model

```python
# apps/core/models.py
"""Base models for tenant-scoped data."""
from django.db import models
from django.conf import settings
import uuid

from apps.tenants.models import Tenant
from apps.core.middleware.tenant import get_current_tenant


class TenantScopedManager(models.Manager):
    """Manager that automatically filters by current tenant."""
    
    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs
    
    def for_tenant(self, tenant: Tenant):
        """Explicitly filter by tenant."""
        return super().get_queryset().filter(tenant=tenant)


class TenantScopedModel(models.Model):
    """
    Abstract base model for all tenant-scoped data.
    Automatically sets tenant on save if not provided.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use tenant-scoped manager
    objects = TenantScopedManager()
    all_objects = models.Manager()  # Bypass tenant filtering
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        """Auto-set tenant from context if not provided."""
        if not self.tenant_id:
            tenant = get_current_tenant()
            if tenant:
                self.tenant = tenant
            else:
                raise ValueError("Tenant context is required")
        super().save(*args, **kwargs)


class AuditableModel(TenantScopedModel):
    """
    Abstract model with audit fields.
    Tracks who created/modified the record.
    """
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created",
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updated",
    )
    
    class Meta:
        abstract = True
```

---

## 6. Authentication & Authorization

### 6.1 Keycloak Authentication Middleware

```python
# apps/core/middleware/authentication.py
"""Keycloak JWT authentication middleware."""
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.conf import settings
from typing import Optional, Dict, Any
import jwt
import requests
from functools import lru_cache
import structlog

logger = structlog.get_logger(__name__)
User = get_user_model()


class KeycloakAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to authenticate requests using Keycloak JWT tokens.
    
    Supports:
    - Bearer token in Authorization header
    - API key in X-API-Key header
    """
    
    EXEMPT_PATHS = [
        "/health",
        "/metrics",
        "/api/v2/auth/callback",
        "/api/v2/webhooks/",
    ]
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.keycloak_config = settings.KEYCLOAK_CONFIG
        self._public_key = None
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Authenticate the request."""
        # Skip exempt paths
        if self._is_exempt_path(request.path):
            return None
        
        # Try Bearer token first
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            return self._authenticate_jwt(request, token)
        
        # Try API key
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return self._authenticate_api_key(request, api_key)
        
        # No authentication provided
        request.user = None
        request.auth = None
        return None
    
    def _authenticate_jwt(
        self, request: HttpRequest, token: str
    ) -> Optional[HttpResponse]:
        """Authenticate using JWT token."""
        try:
            # Get public key for verification
            public_key = self._get_public_key()
            
            # Decode and verify token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=self.keycloak_config["ALGORITHMS"],
                audience=self.keycloak_config["AUDIENCE"],
                leeway=self.keycloak_config["LEEWAY"],
            )
            
            # Extract claims
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            roles = payload.get("realm_access", {}).get("roles", [])
            
            # Get or create user
            user = self._get_or_create_user(payload)
            
            # Set request attributes
            request.user = user
            request.auth = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "roles": roles,
                "token_payload": payload,
            }
            
            logger.info(
                "jwt_authenticated",
                user_id=user_id,
                tenant_id=tenant_id,
            )
            
        except jwt.ExpiredSignatureError:
            logger.warning("jwt_expired")
            request.user = None
            request.auth = {"error": "token_expired"}
            
        except jwt.InvalidTokenError as e:
            logger.warning("jwt_invalid", error=str(e))
            request.user = None
            request.auth = {"error": "invalid_token"}
        
        return None
    
    def _authenticate_api_key(
        self, request: HttpRequest, api_key: str
    ) -> Optional[HttpResponse]:
        """Authenticate using API key."""
        from apps.api_keys.services import APIKeyService
        
        try:
            key_data = APIKeyService.validate_key(api_key)
            
            request.user = key_data["user"]
            request.auth = {
                "api_key_id": str(key_data["api_key"].id),
                "tenant_id": str(key_data["tenant"].id),
                "scopes": key_data["scopes"],
                "rate_limit_tier": key_data["rate_limit_tier"],
            }
            
            logger.info(
                "api_key_authenticated",
                api_key_id=str(key_data["api_key"].id),
                tenant_id=str(key_data["tenant"].id),
            )
            
        except Exception as e:
            logger.warning("api_key_invalid", error=str(e))
            request.user = None
            request.auth = {"error": "invalid_api_key"}
        
        return None
    
    @lru_cache(maxsize=1)
    def _get_public_key(self) -> str:
        """Fetch and cache Keycloak public key."""
        url = (
            f"{self.keycloak_config['SERVER_URL']}"
            f"/realms/{self.keycloak_config['REALM']}"
        )
        
        response = requests.get(
            url,
            verify=self.keycloak_config["VERIFY_SSL"],
            timeout=10,
        )
        response.raise_for_status()
        
        public_key = response.json()["public_key"]
        return f"-----BEGIN PUBLIC KEY-----\n{public_key}\n-----END PUBLIC KEY-----"
    
    def _get_or_create_user(self, payload: Dict[str, Any]) -> User:
        """Get or create user from JWT payload."""
        user_id = payload["sub"]
        email = payload.get("email", "")
        
        user, created = User.objects.update_or_create(
            keycloak_id=user_id,
            defaults={
                "email": email,
                "first_name": payload.get("given_name", ""),
                "last_name": payload.get("family_name", ""),
                "is_active": True,
            },
        )
        
        if created:
            logger.info("user_created_from_jwt", user_id=user_id, email=email)
        
        return user
    
    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from authentication."""
        return any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS)


class KeycloakBackend:
    """Django authentication backend for Keycloak."""
    
    def authenticate(self, request, token=None):
        """Authenticate user from Keycloak token."""
        if token is None:
            return None
        
        # Token validation is handled by middleware
        # This backend just returns the user from request
        return getattr(request, "user", None)
    
    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

### 6.2 SpiceDB Permission System

```python
# apps/core/permissions/spicedb_client.py
"""SpiceDB client for fine-grained authorization."""
from django.conf import settings
from typing import List, Optional, Tuple
from dataclasses import dataclass
import grpc
from authzed.api.v1 import (
    permission_service_pb2,
    permission_service_pb2_grpc,
    core_pb2,
)
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class Permission:
    """Represents a permission check."""
    resource_type: str
    resource_id: str
    relation: str
    subject_type: str
    subject_id: str


class SpiceDBClient:
    """
    Client for SpiceDB permission checks.
    
    Usage:
        client = SpiceDBClient()
        
        # Check permission
        allowed = client.check_permission(
            resource_type="tenant",
            resource_id="tenant-123",
            relation="admin",
            subject_type="user",
            subject_id="user-456",
        )
        
        # Write relationship
        client.write_relationship(
            resource_type="tenant",
            resource_id="tenant-123",
            relation="member",
            subject_type="user",
            subject_id="user-456",
        )
    """
    
    def __init__(self):
        self.config = settings.SPICEDB_CONFIG
        self._channel = None
        self._stub = None
    
    @property
    def stub(self):
        """Lazy-load gRPC stub."""
        if self._stub is None:
            if self.config["INSECURE"]:
                self._channel = grpc.insecure_channel(self.config["ENDPOINT"])
            else:
                credentials = grpc.ssl_channel_credentials()
                self._channel = grpc.secure_channel(
                    self.config["ENDPOINT"],
                    credentials,
                )
            
            self._stub = permission_service_pb2_grpc.PermissionsServiceStub(
                self._channel
            )
        
        return self._stub
    
    def check_permission(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        """
        Check if subject has permission on resource.
        
        Returns True if permission is granted, False otherwise.
        """
        request = permission_service_pb2.CheckPermissionRequest(
            resource=core_pb2.ObjectReference(
                object_type=resource_type,
                object_id=resource_id,
            ),
            permission=relation,
            subject=core_pb2.SubjectReference(
                object=core_pb2.ObjectReference(
                    object_type=subject_type,
                    object_id=subject_id,
                ),
            ),
        )
        
        try:
            response = self.stub.CheckPermission(
                request,
                metadata=[("authorization", f"Bearer {self.config['TOKEN']}")],
                timeout=self.config["TIMEOUT"],
            )
            
            allowed = (
                response.permissionship
                == permission_service_pb2.CheckPermissionResponse.PERMISSIONSHIP_HAS_PERMISSION
            )
            
            logger.debug(
                "permission_check",
                resource=f"{resource_type}:{resource_id}",
                relation=relation,
                subject=f"{subject_type}:{subject_id}",
                allowed=allowed,
            )
            
            return allowed
            
        except grpc.RpcError as e:
            logger.error(
                "permission_check_failed",
                error=str(e),
                resource=f"{resource_type}:{resource_id}",
            )
            return False
    
    def write_relationship(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        """Write a relationship to SpiceDB."""
        request = permission_service_pb2.WriteRelationshipsRequest(
            updates=[
                core_pb2.RelationshipUpdate(
                    operation=core_pb2.RelationshipUpdate.OPERATION_TOUCH,
                    relationship=core_pb2.Relationship(
                        resource=core_pb2.ObjectReference(
                            object_type=resource_type,
                            object_id=resource_id,
                        ),
                        relation=relation,
                        subject=core_pb2.SubjectReference(
                            object=core_pb2.ObjectReference(
                                object_type=subject_type,
                                object_id=subject_id,
                            ),
                        ),
                    ),
                ),
            ],
        )
        
        try:
            self.stub.WriteRelationships(
                request,
                metadata=[("authorization", f"Bearer {self.config['TOKEN']}")],
                timeout=self.config["TIMEOUT"],
            )
            
            logger.info(
                "relationship_written",
                resource=f"{resource_type}:{resource_id}",
                relation=relation,
                subject=f"{subject_type}:{subject_id}",
            )
            
            return True
            
        except grpc.RpcError as e:
            logger.error("relationship_write_failed", error=str(e))
            return False
    
    def delete_relationship(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
        subject_id: str,
    ) -> bool:
        """Delete a relationship from SpiceDB."""
        request = permission_service_pb2.WriteRelationshipsRequest(
            updates=[
                core_pb2.RelationshipUpdate(
                    operation=core_pb2.RelationshipUpdate.OPERATION_DELETE,
                    relationship=core_pb2.Relationship(
                        resource=core_pb2.ObjectReference(
                            object_type=resource_type,
                            object_id=resource_id,
                        ),
                        relation=relation,
                        subject=core_pb2.SubjectReference(
                            object=core_pb2.ObjectReference(
                                object_type=subject_type,
                                object_id=subject_id,
                            ),
                        ),
                    ),
                ),
            ],
        )
        
        try:
            self.stub.WriteRelationships(
                request,
                metadata=[("authorization", f"Bearer {self.config['TOKEN']}")],
                timeout=self.config["TIMEOUT"],
            )
            return True
        except grpc.RpcError as e:
            logger.error("relationship_delete_failed", error=str(e))
            return False
    
    def lookup_subjects(
        self,
        resource_type: str,
        resource_id: str,
        relation: str,
        subject_type: str,
    ) -> List[str]:
        """Look up all subjects with a relation to a resource."""
        request = permission_service_pb2.LookupSubjectsRequest(
            resource=core_pb2.ObjectReference(
                object_type=resource_type,
                object_id=resource_id,
            ),
            permission=relation,
            subject_object_type=subject_type,
        )
        
        try:
            subjects = []
            for response in self.stub.LookupSubjects(
                request,
                metadata=[("authorization", f"Bearer {self.config['TOKEN']}")],
                timeout=self.config["TIMEOUT"],
            ):
                subjects.append(response.subject.subject_object_id)
            return subjects
        except grpc.RpcError as e:
            logger.error("lookup_subjects_failed", error=str(e))
            return []


# Singleton instance
spicedb_client = SpiceDBClient()
```

### 6.3 Permission Decorators

```python
# apps/core/permissions/decorators.py
"""Permission decorators for Django Ninja endpoints."""
from functools import wraps
from typing import Callable, List, Optional
from django.http import HttpRequest

from apps.core.permissions.spicedb_client import spicedb_client
from apps.core.exceptions.auth import PermissionDeniedError


def require_permission(
    resource_type: str,
    relation: str,
    resource_id_param: str = "id",
    resource_id_from_tenant: bool = False,
):
    """
    Decorator to require a specific permission.
    
    Usage:
        @router.get("/{tenant_id}/settings")
        @require_permission("tenant", "admin", resource_id_param="tenant_id")
        def get_tenant_settings(request, tenant_id: str):
            ...
        
        @router.post("/projects")
        @require_permission("tenant", "developer", resource_id_from_tenant=True)
        def create_project(request, payload: ProjectCreate):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            # Get user ID from auth
            if not request.auth or "user_id" not in request.auth:
                raise PermissionDeniedError("Authentication required")
            
            user_id = request.auth["user_id"]
            
            # Determine resource ID
            if resource_id_from_tenant:
                if not hasattr(request, "tenant"):
                    raise PermissionDeniedError("Tenant context required")
                resource_id = str(request.tenant.id)
            else:
                resource_id = kwargs.get(resource_id_param)
                if not resource_id:
                    raise PermissionDeniedError(
                        f"Resource ID parameter '{resource_id_param}' not found"
                    )
            
            # Check permission
            allowed = spicedb_client.check_permission(
                resource_type=resource_type,
                resource_id=resource_id,
                relation=relation,
                subject_type="user",
                subject_id=user_id,
            )
            
            if not allowed:
                raise PermissionDeniedError(
                    f"Permission '{relation}' on '{resource_type}:{resource_id}' denied"
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator


def require_any_permission(permissions: List[tuple]):
    """
    Decorator to require any of the specified permissions.
    
    Usage:
        @require_any_permission([
            ("tenant", "admin"),
            ("tenant", "developer"),
        ])
        def some_endpoint(request):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.auth or "user_id" not in request.auth:
                raise PermissionDeniedError("Authentication required")
            
            user_id = request.auth["user_id"]
            tenant_id = str(request.tenant.id) if hasattr(request, "tenant") else None
            
            for resource_type, relation in permissions:
                resource_id = tenant_id if resource_type == "tenant" else None
                if not resource_id:
                    continue
                
                if spicedb_client.check_permission(
                    resource_type=resource_type,
                    resource_id=resource_id,
                    relation=relation,
                    subject_type="user",
                    subject_id=user_id,
                ):
                    return func(request, *args, **kwargs)
            
            raise PermissionDeniedError("Insufficient permissions")
        
        return wrapper
    return decorator


def require_role(roles: List[str]):
    """
    Decorator to require specific roles from JWT.
    
    Usage:
        @require_role(["sysadmin"])
        def admin_only_endpoint(request):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request: HttpRequest, *args, **kwargs):
            if not request.auth:
                raise PermissionDeniedError("Authentication required")
            
            user_roles = request.auth.get("roles", [])
            
            if not any(role in user_roles for role in roles):
                raise PermissionDeniedError(
                    f"Required role(s): {', '.join(roles)}"
                )
            
            return func(request, *args, **kwargs)
        
        return wrapper
    return decorator
```

### 6.4 SpiceDB Schema

```zed
// integrations/spicedb/schema.zed
// SpiceDB permission schema for AgentVoiceBox

definition user {}

definition tenant {
    // Direct relations
    relation sysadmin: user
    relation admin: user
    relation developer: user
    relation operator: user
    relation viewer: user
    relation billing: user
    
    // Computed permissions (hierarchical)
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission develop = sysadmin + admin + developer
    permission operate = sysadmin + admin + developer + operator
    permission view = sysadmin + admin + developer + operator + viewer
    permission billing_access = sysadmin + admin + billing
    
    // Specific permissions
    permission create_project = develop
    permission create_api_key = develop
    permission invite_user = administrate
    permission manage_billing = billing_access
    permission view_audit = administrate
    permission configure_voice = develop
    permission manage_themes = develop
}

definition project {
    relation tenant: tenant
    relation owner: user
    relation developer: user
    relation viewer: user
    
    // Inherit from tenant
    permission admin = tenant->administrate
    permission develop = owner + developer + tenant->develop
    permission view = owner + developer + viewer + tenant->view
    permission delete = owner + tenant->administrate
}

definition api_key {
    relation tenant: tenant
    relation owner: user
    
    permission view = owner + tenant->develop
    permission rotate = owner + tenant->administrate
    permission revoke = owner + tenant->administrate
}

definition session {
    relation tenant: tenant
    relation project: project
    relation api_key: api_key
    
    permission view = tenant->view
    permission terminate = tenant->operate
    permission view_transcript = tenant->view
    permission export = tenant->develop
}

definition voice_config {
    relation tenant: tenant
    
    permission view = tenant->view
    permission edit = tenant->develop
}

definition theme {
    relation tenant: tenant
    relation owner: user
    relation public: user:*
    
    permission view = owner + tenant->view + public
    permission apply = owner + tenant->view
    permission edit = owner + tenant->develop
    permission delete = owner + tenant->administrate
}

definition persona {
    relation tenant: tenant
    relation owner: user
    
    permission view = owner + tenant->view
    permission use = owner + tenant->operate
    permission edit = owner + tenant->develop
    permission delete = owner + tenant->administrate
}
```

---

## 7. Django Ninja API Layer

### 7.1 API Router Configuration

```python
# config/urls.py
"""Root URL configuration."""
from django.contrib import admin
from django.urls import path, include
from ninja import NinjaAPI
from ninja.security import HttpBearer

from apps.core.middleware.authentication import KeycloakAuthenticationMiddleware
from apps.core.exceptions.base import APIException


# Custom exception handler
def api_exception_handler(request, exc):
    """Handle API exceptions."""
    if isinstance(exc, APIException):
        return api.create_response(
            request,
            {"error": exc.error_code, "message": str(exc), "details": exc.details},
            status=exc.status_code,
        )
    return api.create_response(
        request,
        {"error": "internal_error", "message": "An unexpected error occurred"},
        status=500,
    )


# Create API instance
api = NinjaAPI(
    title="AgentVoiceBox API",
    version="2.0.0",
    description="Enterprise Voice Agent Platform API",
    docs_url="/api/v2/docs",
    openapi_url="/api/v2/openapi.json",
)

# Register exception handler
api.exception_handler(APIException)(api_exception_handler)

# Import and register routers
from apps.tenants.api import router as tenants_router
from apps.users.api import router as users_router
from apps.projects.api import router as projects_router
from apps.api_keys.api import router as api_keys_router
from apps.sessions.api import router as sessions_router
from apps.billing.api import router as billing_router
from apps.voice.api import router as voice_router
from apps.themes.api import router as themes_router
from apps.audit.api import router as audit_router
from apps.notifications.api import router as notifications_router

# Admin routes (SYSADMIN only)
from apps.tenants.api import admin_router as admin_tenants_router
from apps.users.api import admin_router as admin_users_router
from apps.billing.api import admin_router as admin_billing_router

# Register routers
api.add_router("/tenants", tenants_router, tags=["Tenants"])
api.add_router("/users", users_router, tags=["Users"])
api.add_router("/projects", projects_router, tags=["Projects"])
api.add_router("/api-keys", api_keys_router, tags=["API Keys"])
api.add_router("/sessions", sessions_router, tags=["Sessions"])
api.add_router("/billing", billing_router, tags=["Billing"])
api.add_router("/voice", voice_router, tags=["Voice"])
api.add_router("/themes", themes_router, tags=["Themes"])
api.add_router("/audit", audit_router, tags=["Audit"])
api.add_router("/notifications", notifications_router, tags=["Notifications"])

# Admin routers
api.add_router("/admin/tenants", admin_tenants_router, tags=["Admin - Tenants"])
api.add_router("/admin/users", admin_users_router, tags=["Admin - Users"])
api.add_router("/admin/billing", admin_billing_router, tags=["Admin - Billing"])

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v2/", api.urls),
    path("health/", include("health_check.urls")),
    path("", include("django_prometheus.urls")),
]
```

### 7.2 Tenant API Router Example

```python
# apps/tenants/api.py
"""Tenant API endpoints."""
from ninja import Router, Query
from ninja.pagination import paginate, PageNumberPagination
from typing import List, Optional
from django.http import HttpRequest
from uuid import UUID

from apps.core.permissions.decorators import require_permission, require_role
from apps.core.exceptions.base import NotFoundError
from .schemas import (
    TenantCreate,
    TenantUpdate,
    TenantResponse,
    TenantListResponse,
    TenantSettingsUpdate,
    TenantSettingsResponse,
)
from .services import TenantService

router = Router()
admin_router = Router()


# =============================================================================
# TENANT ROUTES (Tenant Users)
# =============================================================================

@router.get("/me", response=TenantResponse)
def get_current_tenant(request: HttpRequest):
    """Get the current tenant (from context)."""
    if not hasattr(request, "tenant"):
        raise NotFoundError("Tenant context not found")
    return TenantService.get_tenant_response(request.tenant)


@router.get("/me/settings", response=TenantSettingsResponse)
@require_permission("tenant", "view", resource_id_from_tenant=True)
def get_tenant_settings(request: HttpRequest):
    """Get current tenant settings."""
    return TenantService.get_settings(request.tenant)


@router.patch("/me/settings", response=TenantSettingsResponse)
@require_permission("tenant", "administrate", resource_id_from_tenant=True)
def update_tenant_settings(request: HttpRequest, payload: TenantSettingsUpdate):
    """Update current tenant settings."""
    return TenantService.update_settings(
        tenant=request.tenant,
        data=payload,
        user=request.user,
    )


@router.get("/me/usage")
@require_permission("tenant", "view", resource_id_from_tenant=True)
def get_tenant_usage(request: HttpRequest):
    """Get current tenant usage statistics."""
    return TenantService.get_usage_stats(request.tenant)


@router.get("/me/limits")
@require_permission("tenant", "view", resource_id_from_tenant=True)
def get_tenant_limits(request: HttpRequest):
    """Get current tenant limits based on tier."""
    return TenantService.get_limits(request.tenant)


# =============================================================================
# ADMIN ROUTES (SYSADMIN Only)
# =============================================================================

@admin_router.get("/", response=List[TenantListResponse])
@require_role(["sysadmin"])
@paginate(PageNumberPagination, page_size=20)
def list_tenants(
    request: HttpRequest,
    status: Optional[str] = Query(None),
    tier: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    """List all tenants (admin only)."""
    return TenantService.list_tenants(
        status=status,
        tier=tier,
        search=search,
    )


@admin_router.post("/", response=TenantResponse)
@require_role(["sysadmin"])
def create_tenant(request: HttpRequest, payload: TenantCreate):
    """Create a new tenant (admin only)."""
    return TenantService.create_tenant(
        data=payload,
        created_by=request.user,
    )


@admin_router.get("/{tenant_id}", response=TenantResponse)
@require_role(["sysadmin"])
def get_tenant(request: HttpRequest, tenant_id: UUID):
    """Get tenant by ID (admin only)."""
    return TenantService.get_tenant(tenant_id)


@admin_router.patch("/{tenant_id}", response=TenantResponse)
@require_role(["sysadmin"])
def update_tenant(request: HttpRequest, tenant_id: UUID, payload: TenantUpdate):
    """Update tenant (admin only)."""
    return TenantService.update_tenant(
        tenant_id=tenant_id,
        data=payload,
        updated_by=request.user,
    )


@admin_router.post("/{tenant_id}/suspend")
@require_role(["sysadmin"])
def suspend_tenant(request: HttpRequest, tenant_id: UUID, reason: str = ""):
    """Suspend a tenant (admin only)."""
    return TenantService.suspend_tenant(
        tenant_id=tenant_id,
        reason=reason,
        suspended_by=request.user,
    )


@admin_router.post("/{tenant_id}/activate")
@require_role(["sysadmin"])
def activate_tenant(request: HttpRequest, tenant_id: UUID):
    """Activate a tenant (admin only)."""
    return TenantService.activate_tenant(
        tenant_id=tenant_id,
        activated_by=request.user,
    )


@admin_router.delete("/{tenant_id}")
@require_role(["sysadmin"])
def delete_tenant(request: HttpRequest, tenant_id: UUID):
    """Soft delete a tenant (admin only)."""
    return TenantService.delete_tenant(
        tenant_id=tenant_id,
        deleted_by=request.user,
    )
```

### 7.3 Pydantic Schemas

```python
# apps/tenants/schemas.py
"""Pydantic schemas for tenant API."""
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
import re


class TenantCreate(BaseModel):
    """Schema for creating a tenant."""
    
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=3, max_length=100)
    tier: str = Field(default="free")
    admin_email: EmailStr
    admin_name: str = Field(..., min_length=2, max_length=255)
    send_welcome_email: bool = True
    
    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$", v):
            raise ValueError(
                "Slug must be lowercase alphanumeric with hyphens, "
                "starting and ending with alphanumeric"
            )
        return v
    
    @field_validator("tier")
    @classmethod
    def validate_tier(cls, v: str) -> str:
        valid_tiers = ["free", "starter", "pro", "enterprise"]
        if v not in valid_tiers:
            raise ValueError(f"Tier must be one of: {', '.join(valid_tiers)}")
        return v


class TenantUpdate(BaseModel):
    """Schema for updating a tenant."""
    
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    tier: Optional[str] = None
    max_users: Optional[int] = Field(None, ge=1)
    max_projects: Optional[int] = Field(None, ge=1)
    max_api_keys: Optional[int] = Field(None, ge=1)
    max_sessions_per_month: Optional[int] = Field(None, ge=0)
    settings: Optional[Dict[str, Any]] = None


class TenantResponse(BaseModel):
    """Schema for tenant response."""
    
    id: UUID
    name: str
    slug: str
    tier: str
    status: str
    max_users: int
    max_projects: int
    max_api_keys: int
    max_sessions_per_month: int
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class TenantListResponse(BaseModel):
    """Schema for tenant list item."""
    
    id: UUID
    name: str
    slug: str
    tier: str
    status: str
    user_count: int = 0
    project_count: int = 0
    session_count: int = 0
    created_at: datetime
    
    class Config:
        from_attributes = True


class TenantSettingsUpdate(BaseModel):
    """Schema for updating tenant settings."""
    
    logo_url: Optional[str] = None
    primary_color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    default_voice_provider: Optional[str] = None
    default_stt_model: Optional[str] = None
    default_tts_voice: Optional[str] = None
    default_llm_provider: Optional[str] = None
    default_llm_model: Optional[str] = None
    email_notifications_enabled: Optional[bool] = None
    webhook_url: Optional[str] = None
    allowed_ip_ranges: Optional[List[str]] = None
    require_mfa: Optional[bool] = None
    session_timeout_minutes: Optional[int] = Field(None, ge=5, le=1440)


class TenantSettingsResponse(BaseModel):
    """Schema for tenant settings response."""
    
    logo_url: str
    primary_color: str
    default_voice_provider: str
    default_stt_model: str
    default_tts_voice: str
    default_llm_provider: str
    default_llm_model: str
    email_notifications_enabled: bool
    webhook_url: str
    allowed_ip_ranges: List[str]
    require_mfa: bool
    session_timeout_minutes: int
    
    class Config:
        from_attributes = True
```

### 7.4 Service Layer

```python
# apps/tenants/services.py
"""Business logic for tenant operations."""
from typing import Optional, List, Dict, Any
from uuid import UUID
from django.db import transaction
from django.db.models import Count, Q
import structlog

from apps.core.exceptions.base import NotFoundError, ValidationError
from apps.core.permissions.spicedb_client import spicedb_client
from apps.users.models import User
from .models import Tenant, TenantSettings
from .schemas import TenantCreate, TenantUpdate, TenantSettingsUpdate
from .tasks import send_welcome_email, sync_tenant_to_billing

logger = structlog.get_logger(__name__)


class TenantService:
    """Service class for tenant operations."""
    
    @staticmethod
    def list_tenants(
        status: Optional[str] = None,
        tier: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Tenant]:
        """List tenants with optional filters."""
        qs = Tenant.all_objects.annotate(
            user_count=Count("users"),
            project_count=Count("projects"),
            session_count=Count("sessions"),
        )
        
        if status:
            qs = qs.filter(status=status)
        
        if tier:
            qs = qs.filter(tier=tier)
        
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | Q(slug__icontains=search)
            )
        
        return qs.order_by("-created_at")
    
    @staticmethod
    def get_tenant(tenant_id: UUID) -> Tenant:
        """Get tenant by ID."""
        try:
            return Tenant.all_objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            raise NotFoundError(f"Tenant {tenant_id} not found")
    
    @staticmethod
    @transaction.atomic
    def create_tenant(data: TenantCreate, created_by: User) -> Tenant:
        """Create a new tenant with initial setup."""
        # Check slug uniqueness
        if Tenant.all_objects.filter(slug=data.slug).exists():
            raise ValidationError(f"Slug '{data.slug}' is already taken")
        
        # Get tier limits
        limits = TenantService._get_tier_limits(data.tier)
        
        # Create tenant
        tenant = Tenant.objects.create(
            name=data.name,
            slug=data.slug,
            tier=data.tier,
            status=Tenant.Status.PENDING,
            **limits,
        )
        
        # Create settings
        TenantSettings.objects.create(tenant=tenant)
        
        # Create admin user
        admin_user = User.objects.create(
            email=data.admin_email,
            first_name=data.admin_name.split()[0] if data.admin_name else "",
            last_name=" ".join(data.admin_name.split()[1:]) if data.admin_name else "",
            tenant=tenant,
        )
        
        # Set up permissions in SpiceDB
        spicedb_client.write_relationship(
            resource_type="tenant",
            resource_id=str(tenant.id),
            relation="admin",
            subject_type="user",
            subject_id=str(admin_user.id),
        )
        
        # Sync to billing system
        sync_tenant_to_billing.delay(str(tenant.id))
        
        # Send welcome email
        if data.send_welcome_email:
            send_welcome_email.delay(str(admin_user.id))
        
        logger.info(
            "tenant_created",
            tenant_id=str(tenant.id),
            slug=tenant.slug,
            tier=tenant.tier,
            created_by=str(created_by.id),
        )
        
        return tenant
    
    @staticmethod
    @transaction.atomic
    def update_tenant(
        tenant_id: UUID,
        data: TenantUpdate,
        updated_by: User,
    ) -> Tenant:
        """Update tenant details."""
        tenant = TenantService.get_tenant(tenant_id)
        
        update_fields = []
        
        if data.name is not None:
            tenant.name = data.name
            update_fields.append("name")
        
        if data.tier is not None:
            tenant.tier = data.tier
            # Update limits based on new tier
            limits = TenantService._get_tier_limits(data.tier)
            for key, value in limits.items():
                setattr(tenant, key, value)
                update_fields.append(key)
        
        if data.max_users is not None:
            tenant.max_users = data.max_users
            update_fields.append("max_users")
        
        if data.max_projects is not None:
            tenant.max_projects = data.max_projects
            update_fields.append("max_projects")
        
        if data.max_api_keys is not None:
            tenant.max_api_keys = data.max_api_keys
            update_fields.append("max_api_keys")
        
        if data.max_sessions_per_month is not None:
            tenant.max_sessions_per_month = data.max_sessions_per_month
            update_fields.append("max_sessions_per_month")
        
        if data.settings is not None:
            tenant.settings.update(data.settings)
            update_fields.append("settings")
        
        if update_fields:
            update_fields.append("updated_at")
            tenant.save(update_fields=update_fields)
        
        logger.info(
            "tenant_updated",
            tenant_id=str(tenant.id),
            updated_fields=update_fields,
            updated_by=str(updated_by.id),
        )
        
        return tenant
    
    @staticmethod
    def suspend_tenant(
        tenant_id: UUID,
        reason: str,
        suspended_by: User,
    ) -> Dict[str, Any]:
        """Suspend a tenant."""
        tenant = TenantService.get_tenant(tenant_id)
        tenant.suspend(reason)
        
        logger.info(
            "tenant_suspended",
            tenant_id=str(tenant.id),
            reason=reason,
            suspended_by=str(suspended_by.id),
        )
        
        return {"status": "suspended", "tenant_id": str(tenant.id)}
    
    @staticmethod
    def activate_tenant(
        tenant_id: UUID,
        activated_by: User,
    ) -> Dict[str, Any]:
        """Activate a tenant."""
        tenant = TenantService.get_tenant(tenant_id)
        tenant.activate()
        
        logger.info(
            "tenant_activated",
            tenant_id=str(tenant.id),
            activated_by=str(activated_by.id),
        )
        
        return {"status": "active", "tenant_id": str(tenant.id)}
    
    @staticmethod
    def delete_tenant(
        tenant_id: UUID,
        deleted_by: User,
    ) -> Dict[str, Any]:
        """Soft delete a tenant."""
        tenant = TenantService.get_tenant(tenant_id)
        tenant.soft_delete()
        
        logger.info(
            "tenant_deleted",
            tenant_id=str(tenant.id),
            deleted_by=str(deleted_by.id),
        )
        
        return {"status": "deleted", "tenant_id": str(tenant.id)}
    
    @staticmethod
    def get_settings(tenant: Tenant) -> TenantSettings:
        """Get tenant settings."""
        settings, _ = TenantSettings.objects.get_or_create(tenant=tenant)
        return settings
    
    @staticmethod
    def update_settings(
        tenant: Tenant,
        data: TenantSettingsUpdate,
        user: User,
    ) -> TenantSettings:
        """Update tenant settings."""
        settings = TenantService.get_settings(tenant)
        
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(settings, field, value)
        
        settings.save()
        
        logger.info(
            "tenant_settings_updated",
            tenant_id=str(tenant.id),
            updated_by=str(user.id),
        )
        
        return settings
    
    @staticmethod
    def get_usage_stats(tenant: Tenant) -> Dict[str, Any]:
        """Get tenant usage statistics."""
        from apps.sessions.models import Session
        from apps.api_keys.models import APIKey
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return {
            "users": {
                "current": tenant.users.count(),
                "limit": tenant.max_users,
            },
            "projects": {
                "current": tenant.projects.count(),
                "limit": tenant.max_projects,
            },
            "api_keys": {
                "current": tenant.api_keys.filter(revoked_at__isnull=True).count(),
                "limit": tenant.max_api_keys,
            },
            "sessions_this_month": {
                "current": Session.objects.filter(
                    tenant=tenant,
                    created_at__gte=month_start,
                ).count(),
                "limit": tenant.max_sessions_per_month,
            },
        }
    
    @staticmethod
    def get_limits(tenant: Tenant) -> Dict[str, int]:
        """Get tenant limits."""
        return {
            "max_users": tenant.max_users,
            "max_projects": tenant.max_projects,
            "max_api_keys": tenant.max_api_keys,
            "max_sessions_per_month": tenant.max_sessions_per_month,
        }
    
    @staticmethod
    def _get_tier_limits(tier: str) -> Dict[str, int]:
        """Get default limits for a tier."""
        limits = {
            "free": {
                "max_users": 3,
                "max_projects": 1,
                "max_api_keys": 5,
                "max_sessions_per_month": 100,
            },
            "starter": {
                "max_users": 10,
                "max_projects": 5,
                "max_api_keys": 20,
                "max_sessions_per_month": 1000,
            },
            "pro": {
                "max_users": 50,
                "max_projects": 20,
                "max_api_keys": 100,
                "max_sessions_per_month": 10000,
            },
            "enterprise": {
                "max_users": 500,
                "max_projects": 100,
                "max_api_keys": 500,
                "max_sessions_per_month": 100000,
            },
        }
        return limits.get(tier, limits["free"])
```

---

## 8. Django Channels WebSocket

### 8.1 ASGI Configuration

```python
# config/asgi.py
"""ASGI configuration for AgentVoiceBox."""
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import after Django setup
from realtime.routing import websocket_urlpatterns
from realtime.middleware import WebSocketAuthMiddleware

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        WebSocketAuthMiddleware(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

### 8.2 WebSocket Routing

```python
# realtime/routing.py
"""WebSocket URL routing."""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Event stream (general notifications)
    re_path(
        r"ws/v2/events/?$",
        consumers.EventConsumer.as_asgi(),
    ),
    
    # Voice session
    re_path(
        r"ws/v2/sessions/(?P<session_id>[0-9a-f-]+)/?$",
        consumers.SessionConsumer.as_asgi(),
    ),
    
    # STT transcription streaming
    re_path(
        r"ws/v2/stt/transcription/?$",
        consumers.TranscriptionConsumer.as_asgi(),
    ),
    
    # TTS audio streaming
    re_path(
        r"ws/v2/tts/stream/?$",
        consumers.TTSConsumer.as_asgi(),
    ),
    
    # Model download progress
    re_path(
        r"ws/v2/models/download/?$",
        consumers.ModelDownloadConsumer.as_asgi(),
    ),
    
    # Admin monitoring (SYSADMIN only)
    re_path(
        r"ws/v2/admin/monitoring/?$",
        consumers.AdminMonitoringConsumer.as_asgi(),
    ),
]
```

### 8.3 WebSocket Authentication Middleware

```python
# realtime/middleware.py
"""WebSocket authentication middleware."""
from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from urllib.parse import parse_qs
import jwt
import structlog

from apps.users.models import User
from apps.tenants.models import Tenant
from apps.api_keys.services import APIKeyService

logger = structlog.get_logger(__name__)


class WebSocketAuthMiddleware(BaseMiddleware):
    """
    Middleware to authenticate WebSocket connections.
    
    Supports:
    - JWT token in query parameter: ?token=xxx
    - API key in query parameter: ?api_key=xxx
    """
    
    async def __call__(self, scope, receive, send):
        # Parse query string
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)
        
        # Try JWT token
        token = query_params.get("token", [None])[0]
        if token:
            scope = await self._authenticate_jwt(scope, token)
        else:
            # Try API key
            api_key = query_params.get("api_key", [None])[0]
            if api_key:
                scope = await self._authenticate_api_key(scope, api_key)
            else:
                scope["user"] = AnonymousUser()
                scope["tenant"] = None
        
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def _authenticate_jwt(self, scope, token: str):
        """Authenticate using JWT token."""
        try:
            # Decode token
            payload = jwt.decode(
                token,
                options={"verify_signature": False},  # Signature verified by Keycloak
                algorithms=settings.KEYCLOAK_CONFIG["ALGORITHMS"],
            )
            
            user_id = payload.get("sub")
            tenant_id = payload.get("tenant_id")
            
            # Get user
            try:
                user = User.objects.get(keycloak_id=user_id)
            except User.DoesNotExist:
                user = AnonymousUser()
            
            # Get tenant
            tenant = None
            if tenant_id:
                try:
                    tenant = Tenant.objects.get(id=tenant_id)
                except Tenant.DoesNotExist:
                    pass
            
            scope["user"] = user
            scope["tenant"] = tenant
            scope["auth"] = {
                "type": "jwt",
                "user_id": user_id,
                "tenant_id": tenant_id,
                "roles": payload.get("realm_access", {}).get("roles", []),
            }
            
        except jwt.InvalidTokenError as e:
            logger.warning("ws_jwt_invalid", error=str(e))
            scope["user"] = AnonymousUser()
            scope["tenant"] = None
        
        return scope
    
    @database_sync_to_async
    def _authenticate_api_key(self, scope, api_key: str):
        """Authenticate using API key."""
        try:
            key_data = APIKeyService.validate_key(api_key)
            
            scope["user"] = key_data["user"]
            scope["tenant"] = key_data["tenant"]
            scope["auth"] = {
                "type": "api_key",
                "api_key_id": str(key_data["api_key"].id),
                "tenant_id": str(key_data["tenant"].id),
                "scopes": key_data["scopes"],
            }
            
        except Exception as e:
            logger.warning("ws_api_key_invalid", error=str(e))
            scope["user"] = AnonymousUser()
            scope["tenant"] = None
        
        return scope
```

### 8.4 Base Consumer Class

```python
# realtime/consumers/base.py
"""Base WebSocket consumer class."""
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from typing import Optional, Dict, Any
import structlog
from datetime import datetime

logger = structlog.get_logger(__name__)


class BaseConsumer(AsyncJsonWebsocketConsumer):
    """
    Base consumer with common functionality.
    
    Features:
    - Authentication validation
    - Tenant context
    - Heartbeat handling
    - Error handling
    - Logging
    """
    
    # Override in subclasses
    requires_auth = True
    requires_tenant = True
    allowed_roles: list = []  # Empty = all authenticated users
    
    async def connect(self):
        """Handle WebSocket connection."""
        # Validate authentication
        if self.requires_auth:
            if not await self._is_authenticated():
                await self.close(code=4001)
                return
        
        # Validate tenant
        if self.requires_tenant:
            if not await self._has_tenant():
                await self.close(code=4002)
                return
        
        # Validate roles
        if self.allowed_roles:
            if not await self._has_required_role():
                await self.close(code=4003)
                return
        
        # Accept connection
        await self.accept()
        
        # Log connection
        logger.info(
            "ws_connected",
            consumer=self.__class__.__name__,
            user_id=self._get_user_id(),
            tenant_id=self._get_tenant_id(),
        )
        
        # Send connection acknowledgment
        await self.send_json({
            "type": "connection.established",
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def disconnect(self, code):
        """Handle WebSocket disconnection."""
        logger.info(
            "ws_disconnected",
            consumer=self.__class__.__name__,
            user_id=self._get_user_id(),
            code=code,
        )
    
    async def receive_json(self, content: Dict[str, Any]):
        """Handle incoming JSON message."""
        message_type = content.get("type", "")
        
        # Handle heartbeat
        if message_type == "ping":
            await self.send_json({"type": "pong"})
            return
        
        # Route to handler
        handler_name = f"handle_{message_type.replace('.', '_')}"
        handler = getattr(self, handler_name, None)
        
        if handler:
            try:
                await handler(content)
            except Exception as e:
                logger.error(
                    "ws_handler_error",
                    handler=handler_name,
                    error=str(e),
                )
                await self.send_error("handler_error", str(e))
        else:
            await self.send_error("unknown_message_type", f"Unknown type: {message_type}")
    
    async def send_error(self, code: str, message: str):
        """Send error message."""
        await self.send_json({
            "type": "error",
            "error": {
                "code": code,
                "message": message,
            },
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    async def send_event(self, event_type: str, data: Dict[str, Any]):
        """Send event message."""
        await self.send_json({
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
        })
    
    # Helper methods
    
    async def _is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        user = self.scope.get("user")
        return user and user.is_authenticated
    
    async def _has_tenant(self) -> bool:
        """Check if tenant context exists."""
        return self.scope.get("tenant") is not None
    
    async def _has_required_role(self) -> bool:
        """Check if user has required role."""
        auth = self.scope.get("auth", {})
        user_roles = auth.get("roles", [])
        return any(role in user_roles for role in self.allowed_roles)
    
    def _get_user_id(self) -> Optional[str]:
        """Get current user ID."""
        auth = self.scope.get("auth", {})
        return auth.get("user_id")
    
    def _get_tenant_id(self) -> Optional[str]:
        """Get current tenant ID."""
        tenant = self.scope.get("tenant")
        return str(tenant.id) if tenant else None
    
    @property
    def user(self):
        """Get current user."""
        return self.scope.get("user")
    
    @property
    def tenant(self):
        """Get current tenant."""
        return self.scope.get("tenant")
```

### 8.5 Event Consumer

```python
# realtime/consumers/events.py
"""Event stream consumer for real-time notifications."""
from channels.db import database_sync_to_async
from typing import Dict, Any

from .base import BaseConsumer


class EventConsumer(BaseConsumer):
    """
    Consumer for general event streaming.
    
    Handles:
    - Tenant-wide notifications
    - User-specific notifications
    - System events
    """
    
    async def connect(self):
        """Connect and join groups."""
        await super().connect()
        
        if self.scope.get("user") and self.scope["user"].is_authenticated:
            # Join user-specific group
            user_id = self._get_user_id()
            await self.channel_layer.group_add(
                f"user_{user_id}",
                self.channel_name,
            )
            
            # Join tenant group
            tenant_id = self._get_tenant_id()
            if tenant_id:
                await self.channel_layer.group_add(
                    f"tenant_{tenant_id}",
                    self.channel_name,
                )
    
    async def disconnect(self, code):
        """Disconnect and leave groups."""
        user_id = self._get_user_id()
        if user_id:
            await self.channel_layer.group_discard(
                f"user_{user_id}",
                self.channel_name,
            )
        
        tenant_id = self._get_tenant_id()
        if tenant_id:
            await self.channel_layer.group_discard(
                f"tenant_{tenant_id}",
                self.channel_name,
            )
        
        await super().disconnect(code)
    
    # Event handlers (called by channel layer)
    
    async def notification_send(self, event: Dict[str, Any]):
        """Handle notification event."""
        await self.send_event("notification", event["data"])
    
    async def session_update(self, event: Dict[str, Any]):
        """Handle session update event."""
        await self.send_event("session.updated", event["data"])
    
    async def settings_changed(self, event: Dict[str, Any]):
        """Handle settings change event."""
        await self.send_event("settings.changed", event["data"])
    
    async def theme_changed(self, event: Dict[str, Any]):
        """Handle theme change event."""
        await self.send_event("theme.changed", event["data"])
    
    async def billing_alert(self, event: Dict[str, Any]):
        """Handle billing alert event."""
        await self.send_event("billing.alert", event["data"])


# Helper function to send events
async def send_tenant_event(tenant_id: str, event_type: str, data: Dict[str, Any]):
    """Send event to all users in a tenant."""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"tenant_{tenant_id}",
        {
            "type": event_type.replace(".", "_"),
            "data": data,
        },
    )


async def send_user_event(user_id: str, event_type: str, data: Dict[str, Any]):
    """Send event to a specific user."""
    from channels.layers import get_channel_layer
    
    channel_layer = get_channel_layer()
    await channel_layer.group_send(
        f"user_{user_id}",
        {
            "type": event_type.replace(".", "_"),
            "data": data,
        },
    )
```

### 8.6 Session Consumer

```python
# realtime/consumers/session.py
"""Voice session WebSocket consumer."""
from channels.db import database_sync_to_async
from typing import Dict, Any
import asyncio

from .base import BaseConsumer
from apps.sessions.models import Session
from apps.sessions.services import SessionService


class SessionConsumer(BaseConsumer):
    """
    Consumer for voice session real-time communication.
    
    Handles:
    - Session lifecycle events
    - Audio streaming
    - Transcription updates
    - Response streaming
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.session = None
    
    async def connect(self):
        """Connect to session."""
        # Get session ID from URL
        self.session_id = self.scope["url_route"]["kwargs"]["session_id"]
        
        # Validate session access
        self.session = await self._get_session()
        if not self.session:
            await self.close(code=4004)
            return
        
        # Check tenant access
        if str(self.session.tenant_id) != self._get_tenant_id():
            await self.close(code=4003)
            return
        
        await super().connect()
        
        # Join session group
        await self.channel_layer.group_add(
            f"session_{self.session_id}",
            self.channel_name,
        )
        
        # Send session state
        await self.send_event("session.state", {
            "session_id": self.session_id,
            "status": self.session.status,
            "created_at": self.session.created_at.isoformat(),
        })
    
    async def disconnect(self, code):
        """Disconnect from session."""
        if self.session_id:
            await self.channel_layer.group_discard(
                f"session_{self.session_id}",
                self.channel_name,
            )
        await super().disconnect(code)
    
    # Client message handlers
    
    async def handle_audio_chunk(self, content: Dict[str, Any]):
        """Handle incoming audio chunk."""
        audio_data = content.get("audio")
        if not audio_data:
            await self.send_error("invalid_audio", "Audio data required")
            return
        
        # Forward to STT worker
        await self._process_audio(audio_data)
    
    async def handle_session_update(self, content: Dict[str, Any]):
        """Handle session configuration update."""
        config = content.get("config", {})
        await self._update_session_config(config)
    
    async def handle_response_create(self, content: Dict[str, Any]):
        """Handle response creation request."""
        # Trigger LLM response
        await self._create_response(content)
    
    async def handle_session_end(self, content: Dict[str, Any]):
        """Handle session end request."""
        await self._end_session()
    
    # Channel layer event handlers
    
    async def transcription_partial(self, event: Dict[str, Any]):
        """Handle partial transcription."""
        await self.send_event("transcription.partial", event["data"])
    
    async def transcription_final(self, event: Dict[str, Any]):
        """Handle final transcription."""
        await self.send_event("transcription.final", event["data"])
    
    async def response_started(self, event: Dict[str, Any]):
        """Handle response started."""
        await self.send_event("response.started", event["data"])
    
    async def response_delta(self, event: Dict[str, Any]):
        """Handle response delta (streaming)."""
        await self.send_event("response.delta", event["data"])
    
    async def response_done(self, event: Dict[str, Any]):
        """Handle response complete."""
        await self.send_event("response.done", event["data"])
    
    async def audio_delta(self, event: Dict[str, Any]):
        """Handle TTS audio delta."""
        await self.send_event("audio.delta", event["data"])
    
    async def session_ended(self, event: Dict[str, Any]):
        """Handle session ended."""
        await self.send_event("session.ended", event["data"])
        await self.close()
    
    # Helper methods
    
    @database_sync_to_async
    def _get_session(self):
        """Get session from database."""
        try:
            return Session.objects.select_related("tenant").get(id=self.session_id)
        except Session.DoesNotExist:
            return None
    
    async def _process_audio(self, audio_data: str):
        """Send audio to STT worker."""
        from workers.stt.tasks import process_audio_chunk
        
        process_audio_chunk.delay(
            session_id=self.session_id,
            audio_data=audio_data,
        )
    
    @database_sync_to_async
    def _update_session_config(self, config: Dict[str, Any]):
        """Update session configuration."""
        SessionService.update_config(self.session_id, config)
    
    async def _create_response(self, content: Dict[str, Any]):
        """Trigger LLM response generation."""
        from workers.llm.tasks import generate_response
        
        generate_response.delay(
            session_id=self.session_id,
            messages=content.get("messages", []),
        )
    
    @database_sync_to_async
    def _end_session(self):
        """End the session."""
        SessionService.end_session(self.session_id)
```

---

## 9. Database Layer

### 9.1 User Model

```python
# apps/users/models.py
"""User models for AgentVoiceBox."""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid

from apps.tenants.models import Tenant


class UserManager(BaseUserManager):
    """Custom user manager."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create a regular user."""
        if not email:
            raise ValueError("Email is required")
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model for AgentVoiceBox.
    Uses email as the username field.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # Keycloak integration
    keycloak_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Keycloak user ID (sub claim)",
    )
    
    # Basic info
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    
    # Tenant association
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="users",
        null=True,
        blank=True,
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    # Timestamps
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Settings
    preferences = models.JSONField(default=dict)
    
    objects = UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = "users"
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["keycloak_id"]),
            models.Index(fields=["tenant"]),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email


class UserProfile(models.Model):
    """Extended user profile."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    
    avatar_url = models.URLField(blank=True)
    timezone = models.CharField(max_length=50, default="UTC")
    locale = models.CharField(max_length=10, default="en")
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    
    # Theme preference
    theme_id = models.UUIDField(null=True, blank=True)
    
    class Meta:
        db_table = "user_profiles"
```

### 9.2 API Key Model

```python
# apps/api_keys/models.py
"""API key models."""
from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid
import secrets
import hashlib

from apps.core.models import TenantScopedModel


class APIKey(TenantScopedModel):
    """
    API key for programmatic access.
    Keys are hashed and cannot be retrieved after creation.
    """
    
    class RateLimitTier(models.TextChoices):
        STANDARD = "standard", "Standard"
        ELEVATED = "elevated", "Elevated"
        UNLIMITED = "unlimited", "Unlimited"
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    # Key storage (hashed)
    key_prefix = models.CharField(max_length=8)  # First 8 chars for identification
    key_hash = models.CharField(max_length=64)  # SHA-256 hash
    
    # Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_api_keys",
    )
    
    # Project association (optional)
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="api_keys",
    )
    
    # Scopes
    scopes = models.JSONField(
        default=list,
        help_text="List of allowed scopes: realtime, billing, admin",
    )
    
    # Rate limiting
    rate_limit_tier = models.CharField(
        max_length=20,
        choices=RateLimitTier.choices,
        default=RateLimitTier.STANDARD,
    )
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Revocation
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="revoked_api_keys",
    )
    
    # Usage tracking
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = "api_keys"
        indexes = [
            models.Index(fields=["key_prefix"]),
            models.Index(fields=["tenant", "revoked_at"]),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"
    
    @classmethod
    def generate_key(cls) -> tuple[str, str, str]:
        """
        Generate a new API key.
        Returns: (full_key, prefix, hash)
        """
        # Generate 32-byte random key
        raw_key = secrets.token_urlsafe(32)
        full_key = f"avb_{raw_key}"
        
        # Extract prefix
        prefix = full_key[:12]
        
        # Hash the key
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        
        return full_key, prefix, key_hash
    
    @classmethod
    def hash_key(cls, key: str) -> str:
        """Hash an API key for comparison."""
        return hashlib.sha256(key.encode()).hexdigest()
    
    @property
    def is_expired(self) -> bool:
        """Check if key is expired."""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_revoked(self) -> bool:
        """Check if key is revoked."""
        return self.revoked_at is not None
    
    @property
    def is_valid(self) -> bool:
        """Check if key is valid for use."""
        return not self.is_expired and not self.is_revoked
    
    def revoke(self, user):
        """Revoke the API key."""
        self.revoked_at = timezone.now()
        self.revoked_by = user
        self.save(update_fields=["revoked_at", "revoked_by", "updated_at"])
    
    def record_usage(self, ip_address: str = None):
        """Record API key usage."""
        self.last_used_at = timezone.now()
        self.last_used_ip = ip_address
        self.usage_count += 1
        self.save(update_fields=["last_used_at", "last_used_ip", "usage_count"])
```

### 9.3 Session Model

```python
# apps/sessions/models.py
"""Voice session models."""
from django.db import models
from django.conf import settings
import uuid

from apps.core.models import TenantScopedModel


class Session(TenantScopedModel):
    """
    Represents a voice session.
    """
    
    class Status(models.TextChoices):
        CREATED = "created", "Created"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        ERROR = "error", "Error"
        TERMINATED = "terminated", "Terminated"
    
    # Associations
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    
    api_key = models.ForeignKey(
        "api_keys.APIKey",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sessions",
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.CREATED,
    )
    
    # Configuration
    config = models.JSONField(
        default=dict,
        help_text="Session configuration (voice, model, etc.)",
    )
    
    # Timing
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    # Metrics
    duration_seconds = models.FloatField(null=True, blank=True)
    input_tokens = models.PositiveIntegerField(default=0)
    output_tokens = models.PositiveIntegerField(default=0)
    audio_duration_seconds = models.FloatField(default=0)
    
    # Error info
    error_code = models.CharField(max_length=50, blank=True)
    error_message = models.TextField(blank=True)
    
    # Client info
    client_ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = "sessions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "created_at"]),
            models.Index(fields=["project"]),
            models.Index(fields=["api_key"]),
        ]
    
    def __str__(self):
        return f"Session {self.id} ({self.status})"


class SessionEvent(models.Model):
    """
    Events within a session (transcript, responses, etc.).
    """
    
    class EventType(models.TextChoices):
        TRANSCRIPT = "transcript", "Transcript"
        RESPONSE = "response", "Response"
        TOOL_CALL = "tool_call", "Tool Call"
        TOOL_RESULT = "tool_result", "Tool Result"
        ERROR = "error", "Error"
        SYSTEM = "system", "System"
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    session = models.ForeignKey(
        Session,
        on_delete=models.CASCADE,
        related_name="events",
    )
    
    event_type = models.CharField(
        max_length=20,
        choices=EventType.choices,
    )
    
    # Content
    content = models.JSONField(default=dict)
    
    # Timing
    timestamp = models.DateTimeField(auto_now_add=True)
    duration_ms = models.PositiveIntegerField(null=True, blank=True)
    
    # Sequence
    sequence = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = "session_events"
        ordering = ["session", "sequence"]
        indexes = [
            models.Index(fields=["session", "event_type"]),
            models.Index(fields=["session", "timestamp"]),
        ]
```

### 9.4 Audit Log Model

```python
# apps/audit/models.py
"""Audit logging models."""
from django.db import models
from django.conf import settings
import uuid


class AuditLog(models.Model):
    """
    Immutable audit log for tracking all significant actions.
    """
    
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
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    
    # When
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Who
    actor_id = models.UUIDField(null=True, blank=True, db_index=True)
    actor_email = models.EmailField(blank=True)
    actor_type = models.CharField(
        max_length=20,
        default="user",
        choices=[
            ("user", "User"),
            ("api_key", "API Key"),
            ("system", "System"),
        ],
    )
    
    # Where
    tenant_id = models.UUIDField(null=True, blank=True, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # What
    action = models.CharField(max_length=30, choices=Action.choices, db_index=True)
    resource_type = models.CharField(max_length=50, db_index=True)
    resource_id = models.CharField(max_length=255, blank=True)
    
    # Details
    description = models.TextField(blank=True)
    old_values = models.JSONField(null=True, blank=True)
    new_values = models.JSONField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    
    # Request context
    request_id = models.CharField(max_length=100, blank=True)
    
    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["tenant_id", "timestamp"]),
            models.Index(fields=["actor_id", "timestamp"]),
            models.Index(fields=["resource_type", "resource_id"]),
        ]
    
    def __str__(self):
        return f"{self.action} {self.resource_type} by {self.actor_email}"
    
    @classmethod
    def log(
        cls,
        action: str,
        resource_type: str,
        resource_id: str = "",
        actor=None,
        tenant=None,
        request=None,
        description: str = "",
        old_values: dict = None,
        new_values: dict = None,
        metadata: dict = None,
    ):
        """Create an audit log entry."""
        entry = cls(
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id else "",
            description=description,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata or {},
        )
        
        if actor:
            entry.actor_id = actor.id if hasattr(actor, "id") else None
            entry.actor_email = actor.email if hasattr(actor, "email") else ""
        
        if tenant:
            entry.tenant_id = tenant.id
        
        if request:
            entry.ip_address = cls._get_client_ip(request)
            entry.user_agent = request.headers.get("User-Agent", "")[:500]
            entry.request_id = request.headers.get("X-Request-ID", "")
        
        entry.save()
        return entry
    
    @staticmethod
    def _get_client_ip(request):
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")
```

---

## 10. Caching & Session Management

### 10.1 Cache Service

```python
# apps/core/services/cache.py
"""Caching service with tenant isolation."""
from django.core.cache import caches
from typing import Any, Optional, Callable
from functools import wraps
import hashlib
import json
import structlog

from apps.core.middleware.tenant import get_current_tenant

logger = structlog.get_logger(__name__)


class CacheService:
    """
    Centralized caching service with tenant isolation.
    """
    
    def __init__(self, cache_alias: str = "default"):
        self.cache = caches[cache_alias]
    
    def _make_key(self, key: str, tenant_scoped: bool = True) -> str:
        """Generate cache key with optional tenant prefix."""
        if tenant_scoped:
            tenant = get_current_tenant()
            if tenant:
                return f"t:{tenant.id}:{key}"
        return key
    
    def get(
        self,
        key: str,
        default: Any = None,
        tenant_scoped: bool = True,
    ) -> Any:
        """Get value from cache."""
        cache_key = self._make_key(key, tenant_scoped)
        return self.cache.get(cache_key, default)
    
    def set(
        self,
        key: str,
        value: Any,
        timeout: int = 300,
        tenant_scoped: bool = True,
    ) -> bool:
        """Set value in cache."""
        cache_key = self._make_key(key, tenant_scoped)
        return self.cache.set(cache_key, value, timeout)
    
    def delete(self, key: str, tenant_scoped: bool = True) -> bool:
        """Delete value from cache."""
        cache_key = self._make_key(key, tenant_scoped)
        return self.cache.delete(cache_key)
    
    def get_or_set(
        self,
        key: str,
        default_func: Callable,
        timeout: int = 300,
        tenant_scoped: bool = True,
    ) -> Any:
        """Get value or set from callable if not exists."""
        cache_key = self._make_key(key, tenant_scoped)
        value = self.cache.get(cache_key)
        
        if value is None:
            value = default_func()
            self.cache.set(cache_key, value, timeout)
        
        return value
    
    def invalidate_pattern(self, pattern: str, tenant_scoped: bool = True):
        """Invalidate all keys matching pattern (Redis only)."""
        if tenant_scoped:
            tenant = get_current_tenant()
            if tenant:
                pattern = f"t:{tenant.id}:{pattern}"
        
        # This requires Redis backend
        if hasattr(self.cache, "delete_pattern"):
            self.cache.delete_pattern(pattern)


# Decorator for caching function results
def cached(
    key_template: str,
    timeout: int = 300,
    tenant_scoped: bool = True,
):
    """
    Decorator to cache function results.
    
    Usage:
        @cached("user:{user_id}", timeout=600)
        def get_user(user_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key from template
            cache_key = key_template.format(**kwargs)
            
            cache_service = CacheService()
            
            # Try to get from cache
            result = cache_service.get(cache_key, tenant_scoped=tenant_scoped)
            if result is not None:
                return result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache_service.set(cache_key, result, timeout, tenant_scoped)
            
            return result
        
        return wrapper
    return decorator


# Singleton instance
cache_service = CacheService()
```

### 10.2 Rate Limiting Middleware

```python
# apps/core/middleware/rate_limit.py
"""Rate limiting middleware."""
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import caches
from django.conf import settings
from typing import Optional, Tuple
import time
import structlog

logger = structlog.get_logger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Token bucket rate limiting middleware.
    
    Limits are applied per:
    - IP address (unauthenticated)
    - User ID (authenticated)
    - API key (API access)
    """
    
    def __init__(self, get_response):
        super().__init__(get_response)
        self.cache = caches["rate_limit"]
        self.config = settings.RATE_LIMIT_CONFIG
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Check rate limits before processing request."""
        # Skip rate limiting for certain paths
        if self._is_exempt(request.path):
            return None
        
        # Determine rate limit key and limits
        key, limits = self._get_rate_limit_params(request)
        
        # Check rate limit
        allowed, remaining, reset_time = self._check_rate_limit(
            key,
            limits["requests_per_minute"],
            60,
        )
        
        # Add rate limit headers
        request._rate_limit_headers = {
            "X-RateLimit-Limit": str(limits["requests_per_minute"]),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_time),
        }
        
        if not allowed:
            logger.warning(
                "rate_limit_exceeded",
                key=key,
                limit=limits["requests_per_minute"],
            )
            
            return JsonResponse(
                {
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": reset_time - int(time.time()),
                },
                status=429,
                headers=request._rate_limit_headers,
            )
        
        return None
    
    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Add rate limit headers to response."""
        if hasattr(request, "_rate_limit_headers"):
            for header, value in request._rate_limit_headers.items():
                response[header] = value
        return response
    
    def _get_rate_limit_params(
        self, request: HttpRequest
    ) -> Tuple[str, dict]:
        """Determine rate limit key and limits based on request."""
        # API key authentication
        if hasattr(request, "auth") and request.auth:
            if "api_key_id" in request.auth:
                tier = request.auth.get("rate_limit_tier", "standard")
                return (
                    f"api_key:{request.auth['api_key_id']}",
                    self.config.get(tier.upper(), self.config["DEFAULT"]),
                )
            
            # User authentication
            if "user_id" in request.auth:
                roles = request.auth.get("roles", [])
                if "sysadmin" in roles:
                    return (
                        f"user:{request.auth['user_id']}",
                        self.config["ADMIN"],
                    )
                return (
                    f"user:{request.auth['user_id']}",
                    self.config["API_KEY"],
                )
        
        # IP-based rate limiting
        ip = self._get_client_ip(request)
        return f"ip:{ip}", self.config["DEFAULT"]
    
    def _check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using sliding window counter.
        Returns: (allowed, remaining, reset_time)
        """
        now = int(time.time())
        window_start = now - window
        cache_key = f"rl:{key}:{now // window}"
        
        # Get current count
        current = self.cache.get(cache_key, 0)
        
        if current >= limit:
            reset_time = (now // window + 1) * window
            return False, 0, reset_time
        
        # Increment counter
        self.cache.set(cache_key, current + 1, window + 1)
        
        remaining = limit - current - 1
        reset_time = (now // window + 1) * window
        
        return True, remaining, reset_time
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
    
    def _is_exempt(self, path: str) -> bool:
        """Check if path is exempt from rate limiting."""
        exempt_paths = ["/health", "/metrics"]
        return any(path.startswith(p) for p in exempt_paths)
```

---

## 11. Background Tasks & Workers

### 11.1 Celery Configuration

```python
# config/celery.py
"""Celery configuration for AgentVoiceBox."""
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

app = Celery("agentvoicebox")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Beat schedule for periodic tasks
app.conf.beat_schedule = {
    # Cleanup expired sessions every hour
    "cleanup-expired-sessions": {
        "task": "workers.scheduled.cleanup.cleanup_expired_sessions",
        "schedule": crontab(minute=0),
    },
    
    # Sync billing data every 15 minutes
    "sync-billing-usage": {
        "task": "workers.scheduled.billing_sync.sync_usage_to_lago",
        "schedule": crontab(minute="*/15"),
    },
    
    # Aggregate metrics every 5 minutes
    "aggregate-metrics": {
        "task": "workers.scheduled.metrics_aggregation.aggregate_session_metrics",
        "schedule": crontab(minute="*/5"),
    },
    
    # Cleanup old audit logs monthly
    "cleanup-audit-logs": {
        "task": "workers.scheduled.cleanup.cleanup_old_audit_logs",
        "schedule": crontab(day_of_month=1, hour=2, minute=0),
    },
    
    # Check subscription status daily
    "check-subscriptions": {
        "task": "apps.billing.tasks.check_subscription_status",
        "schedule": crontab(hour=6, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing."""
    print(f"Request: {self.request!r}")
```

### 11.2 Task Base Class

```python
# apps/core/tasks.py
"""Base task classes with common functionality."""
from celery import Task
from django.db import connection
import structlog

from apps.core.middleware.tenant import set_current_tenant, clear_current_tenant
from apps.tenants.models import Tenant

logger = structlog.get_logger(__name__)


class TenantAwareTask(Task):
    """
    Base task that maintains tenant context.
    
    Usage:
        @app.task(base=TenantAwareTask, bind=True)
        def my_task(self, tenant_id: str, ...):
            # self.tenant is available
            ...
    """
    
    abstract = True
    
    def __call__(self, *args, **kwargs):
        """Set up tenant context before task execution."""
        tenant_id = kwargs.pop("tenant_id", None) or (args[0] if args else None)
        
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id)
                set_current_tenant(tenant)
                self.tenant = tenant
            except Tenant.DoesNotExist:
                logger.error("task_tenant_not_found", tenant_id=tenant_id)
                raise
        
        try:
            return super().__call__(*args, **kwargs)
        finally:
            clear_current_tenant()
            self.tenant = None
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure."""
        logger.error(
            "task_failed",
            task=self.name,
            task_id=task_id,
            error=str(exc),
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Log task success."""
        logger.info(
            "task_completed",
            task=self.name,
            task_id=task_id,
        )


class RetryableTask(TenantAwareTask):
    """
    Task with automatic retry on failure.
    """
    
    abstract = True
    autoretry_for = (Exception,)
    retry_backoff = True
    retry_backoff_max = 600  # 10 minutes
    retry_jitter = True
    max_retries = 3
```

### 11.3 Example Tasks

```python
# apps/tenants/tasks.py
"""Tenant-related Celery tasks."""
from celery import shared_task
from django.conf import settings
import structlog

from apps.core.tasks import TenantAwareTask, RetryableTask

logger = structlog.get_logger(__name__)


@shared_task(base=RetryableTask, bind=True)
def sync_tenant_to_billing(self, tenant_id: str):
    """Sync tenant to Lago billing system."""
    from apps.tenants.models import Tenant
    from integrations.lago.client import LagoClient
    
    tenant = Tenant.objects.get(id=tenant_id)
    lago = LagoClient()
    
    # Create or update customer in Lago
    lago.create_or_update_customer(
        external_id=str(tenant.id),
        name=tenant.name,
        email=tenant.users.filter(
            tenant_memberships__role="admin"
        ).first().email if tenant.users.exists() else None,
        metadata={
            "tier": tenant.tier,
            "slug": tenant.slug,
        },
    )
    
    # Assign subscription based on tier
    lago.assign_subscription(
        customer_id=str(tenant.id),
        plan_code=f"plan_{tenant.tier}",
    )
    
    # Update tenant with billing ID
    tenant.billing_id = str(tenant.id)
    tenant.save(update_fields=["billing_id"])
    
    logger.info(
        "tenant_synced_to_billing",
        tenant_id=tenant_id,
        tier=tenant.tier,
    )


@shared_task(base=TenantAwareTask, bind=True)
def send_welcome_email(self, user_id: str):
    """Send welcome email to new user."""
    from apps.users.models import User
    from apps.notifications.services import EmailService
    
    user = User.objects.get(id=user_id)
    
    EmailService.send_template(
        to=user.email,
        template="welcome",
        context={
            "user_name": user.first_name or user.email,
            "tenant_name": user.tenant.name if user.tenant else "AgentVoiceBox",
            "login_url": settings.FRONTEND_URL,
        },
    )
    
    logger.info(
        "welcome_email_sent",
        user_id=user_id,
        email=user.email,
    )


@shared_task
def cleanup_expired_sessions():
    """Clean up expired voice sessions."""
    from django.utils import timezone
    from datetime import timedelta
    from apps.sessions.models import Session
    
    # Sessions older than 24 hours that are still "active"
    cutoff = timezone.now() - timedelta(hours=24)
    
    expired = Session.objects.filter(
        status=Session.Status.ACTIVE,
        created_at__lt=cutoff,
    )
    
    count = expired.count()
    expired.update(
        status=Session.Status.TERMINATED,
        ended_at=timezone.now(),
    )
    
    logger.info("expired_sessions_cleaned", count=count)
```

---

## 12. Logging & Observability

### 12.1 Structured Logging Configuration

```python
# apps/core/logging/config.py
"""Structlog configuration for AgentVoiceBox."""
import structlog
import logging
from django.conf import settings


def configure_structlog():
    """Configure structlog for the application."""
    
    # Shared processors
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.DEBUG:
        # Development: pretty console output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = None):
    """Get a configured logger."""
    return structlog.get_logger(name)
```

### 12.2 Request Logging Middleware

```python
# apps/core/middleware/request_logging.py
"""Request/response logging middleware."""
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
import time
import uuid
import structlog

logger = structlog.get_logger("request")


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all HTTP requests and responses.
    
    Adds:
    - Request ID for tracing
    - Request timing
    - Structured logging
    """
    
    def process_request(self, request: HttpRequest):
        """Start request timing and add request ID."""
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request._request_id = request_id
        request._start_time = time.time()
        
        # Bind request context to logger
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.path,
        )
        
        # Add user context if available
        if hasattr(request, "user") and request.user and request.user.is_authenticated:
            structlog.contextvars.bind_contextvars(
                user_id=str(request.user.id),
            )
        
        # Add tenant context if available
        if hasattr(request, "tenant") and request.tenant:
            structlog.contextvars.bind_contextvars(
                tenant_id=str(request.tenant.id),
            )
    
    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Log request completion and add headers."""
        # Calculate duration
        duration_ms = 0
        if hasattr(request, "_start_time"):
            duration_ms = (time.time() - request._start_time) * 1000
        
        # Add request ID to response
        if hasattr(request, "_request_id"):
            response["X-Request-ID"] = request._request_id
        
        # Log request
        log_data = {
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
            "content_length": len(response.content) if hasattr(response, "content") else 0,
        }
        
        # Add client IP
        log_data["client_ip"] = self._get_client_ip(request)
        
        # Log level based on status code
        if response.status_code >= 500:
            logger.error("request_completed", **log_data)
        elif response.status_code >= 400:
            logger.warning("request_completed", **log_data)
        else:
            logger.info("request_completed", **log_data)
        
        return response
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
```

### 12.3 Prometheus Metrics

```python
# integrations/prometheus/metrics.py
"""Custom Prometheus metrics for AgentVoiceBox."""
from prometheus_client import Counter, Histogram, Gauge, Info
from functools import wraps
import time


# =============================================================================
# APPLICATION METRICS
# =============================================================================

# Request metrics
http_requests_total = Counter(
    "avb_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "avb_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# WebSocket metrics
websocket_connections = Gauge(
    "avb_websocket_connections",
    "Current WebSocket connections",
    ["consumer_type"],
)

websocket_messages_total = Counter(
    "avb_websocket_messages_total",
    "Total WebSocket messages",
    ["consumer_type", "direction"],
)

# =============================================================================
# BUSINESS METRICS
# =============================================================================

# Tenant metrics
tenants_total = Gauge(
    "avb_tenants_total",
    "Total tenants",
    ["tier", "status"],
)

# Session metrics
sessions_total = Counter(
    "avb_sessions_total",
    "Total voice sessions",
    ["tenant_id", "status"],
)

session_duration_seconds = Histogram(
    "avb_session_duration_seconds",
    "Voice session duration in seconds",
    ["tenant_id"],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800],
)

active_sessions = Gauge(
    "avb_active_sessions",
    "Currently active sessions",
    ["tenant_id"],
)

# API key metrics
api_key_usage_total = Counter(
    "avb_api_key_usage_total",
    "API key usage count",
    ["tenant_id", "key_id"],
)

# =============================================================================
# WORKER METRICS
# =============================================================================

# STT metrics
stt_requests_total = Counter(
    "avb_stt_requests_total",
    "Total STT requests",
    ["model", "language"],
)

stt_duration_seconds = Histogram(
    "avb_stt_duration_seconds",
    "STT processing duration",
    ["model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0],
)

stt_audio_duration_seconds = Histogram(
    "avb_stt_audio_duration_seconds",
    "Audio duration processed by STT",
    ["model"],
    buckets=[1, 5, 10, 30, 60, 120, 300],
)

# TTS metrics
tts_requests_total = Counter(
    "avb_tts_requests_total",
    "Total TTS requests",
    ["voice", "language"],
)

tts_duration_seconds = Histogram(
    "avb_tts_duration_seconds",
    "TTS processing duration",
    ["voice"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.0, 5.0],
)

tts_characters_total = Counter(
    "avb_tts_characters_total",
    "Total characters processed by TTS",
    ["voice"],
)

# LLM metrics
llm_requests_total = Counter(
    "avb_llm_requests_total",
    "Total LLM requests",
    ["provider", "model"],
)

llm_tokens_total = Counter(
    "avb_llm_tokens_total",
    "Total LLM tokens",
    ["provider", "model", "type"],  # type: input/output
)

llm_duration_seconds = Histogram(
    "avb_llm_duration_seconds",
    "LLM request duration",
    ["provider", "model"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
)

# =============================================================================
# INFRASTRUCTURE METRICS
# =============================================================================

# Database metrics
db_query_duration_seconds = Histogram(
    "avb_db_query_duration_seconds",
    "Database query duration",
    ["operation"],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0],
)

# Cache metrics
cache_hits_total = Counter(
    "avb_cache_hits_total",
    "Cache hits",
    ["cache"],
)

cache_misses_total = Counter(
    "avb_cache_misses_total",
    "Cache misses",
    ["cache"],
)

# Celery metrics
celery_tasks_total = Counter(
    "avb_celery_tasks_total",
    "Total Celery tasks",
    ["task", "status"],
)

celery_task_duration_seconds = Histogram(
    "avb_celery_task_duration_seconds",
    "Celery task duration",
    ["task"],
    buckets=[0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 300.0],
)


# =============================================================================
# DECORATORS
# =============================================================================

def track_request_metrics(endpoint: str):
    """Decorator to track request metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            
            try:
                response = func(request, *args, **kwargs)
                status = response.status_code
            except Exception as e:
                status = 500
                raise
            finally:
                duration = time.time() - start_time
                http_requests_total.labels(
                    method=request.method,
                    endpoint=endpoint,
                    status=status,
                ).inc()
                http_request_duration_seconds.labels(
                    method=request.method,
                    endpoint=endpoint,
                ).observe(duration)
            
            return response
        return wrapper
    return decorator


def track_task_metrics(task_name: str):
    """Decorator to track Celery task metrics."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                status = "failure"
                raise
            finally:
                duration = time.time() - start_time
                celery_tasks_total.labels(
                    task=task_name,
                    status=status,
                ).inc()
                celery_task_duration_seconds.labels(
                    task=task_name,
                ).observe(duration)
            
            return result
        return wrapper
    return decorator
```

### 12.4 Audit Middleware

```python
# apps/core/middleware/audit.py
"""Audit logging middleware."""
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from typing import Optional
import structlog

from apps.audit.models import AuditLog

logger = structlog.get_logger(__name__)


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware to automatically log auditable actions.
    
    Logs:
    - All write operations (POST, PUT, PATCH, DELETE)
    - Authentication events
    - Permission-sensitive operations
    """
    
    # Paths to always audit
    AUDIT_PATHS = [
        "/api/v2/tenants",
        "/api/v2/users",
        "/api/v2/api-keys",
        "/api/v2/projects",
        "/api/v2/billing",
        "/api/v2/admin",
    ]
    
    # Methods to audit
    AUDIT_METHODS = ["POST", "PUT", "PATCH", "DELETE"]
    
    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Log auditable actions after response."""
        # Skip if not auditable
        if not self._should_audit(request, response):
            return response
        
        # Determine action
        action = self._get_action(request)
        
        # Extract resource info
        resource_type, resource_id = self._extract_resource(request)
        
        # Create audit log
        try:
            AuditLog.log(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                actor=getattr(request, "user", None),
                tenant=getattr(request, "tenant", None),
                request=request,
                description=f"{request.method} {request.path}",
                metadata={
                    "status_code": response.status_code,
                    "request_id": getattr(request, "_request_id", ""),
                },
            )
        except Exception as e:
            logger.error("audit_log_failed", error=str(e))
        
        return response
    
    def _should_audit(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Determine if request should be audited."""
        # Only audit write methods
        if request.method not in self.AUDIT_METHODS:
            return False
        
        # Only audit specific paths
        if not any(request.path.startswith(p) for p in self.AUDIT_PATHS):
            return False
        
        # Only audit successful operations
        if response.status_code >= 400:
            return False
        
        return True
    
    def _get_action(self, request: HttpRequest) -> str:
        """Map HTTP method to audit action."""
        method_map = {
            "POST": AuditLog.Action.CREATE,
            "PUT": AuditLog.Action.UPDATE,
            "PATCH": AuditLog.Action.UPDATE,
            "DELETE": AuditLog.Action.DELETE,
        }
        return method_map.get(request.method, AuditLog.Action.API_CALL)
    
    def _extract_resource(self, request: HttpRequest) -> tuple[str, str]:
        """Extract resource type and ID from request path."""
        parts = request.path.strip("/").split("/")
        
        # Expected format: api/v2/{resource_type}/{resource_id}
        if len(parts) >= 3:
            resource_type = parts[2]  # e.g., "tenants", "users"
            resource_id = parts[3] if len(parts) > 3 else ""
            return resource_type, resource_id
        
        return "unknown", ""
```

---

## 13. Security Architecture

### 13.1 Exception Handler Middleware

```python
# apps/core/middleware/exception_handler.py
"""Global exception handling middleware."""
from django.http import HttpRequest, JsonResponse
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import structlog
import traceback

from apps.core.exceptions.base import APIException

logger = structlog.get_logger(__name__)


class ExceptionHandlerMiddleware(MiddlewareMixin):
    """
    Global exception handler for consistent error responses.
    
    Converts all exceptions to JSON responses with:
    - Consistent error format
    - Appropriate status codes
    - Sanitized error messages (no stack traces in production)
    """
    
    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> JsonResponse:
        """Handle exceptions and return JSON response."""
        
        # Handle known API exceptions
        if isinstance(exception, APIException):
            return self._handle_api_exception(request, exception)
        
        # Handle Django exceptions
        from django.core.exceptions import (
            PermissionDenied,
            ObjectDoesNotExist,
            ValidationError,
        )
        
        if isinstance(exception, PermissionDenied):
            return self._json_response(
                error="permission_denied",
                message="You do not have permission to perform this action",
                status=403,
            )
        
        if isinstance(exception, ObjectDoesNotExist):
            return self._json_response(
                error="not_found",
                message="The requested resource was not found",
                status=404,
            )
        
        if isinstance(exception, ValidationError):
            return self._json_response(
                error="validation_error",
                message=str(exception),
                status=400,
            )
        
        # Handle unexpected exceptions
        return self._handle_unexpected_exception(request, exception)
    
    def _handle_api_exception(
        self, request: HttpRequest, exception: APIException
    ) -> JsonResponse:
        """Handle custom API exceptions."""
        logger.warning(
            "api_exception",
            error_code=exception.error_code,
            message=str(exception),
            status_code=exception.status_code,
        )
        
        return self._json_response(
            error=exception.error_code,
            message=str(exception),
            status=exception.status_code,
            details=exception.details,
        )
    
    def _handle_unexpected_exception(
        self, request: HttpRequest, exception: Exception
    ) -> JsonResponse:
        """Handle unexpected exceptions."""
        # Log full exception
        logger.exception(
            "unexpected_exception",
            exception_type=type(exception).__name__,
            message=str(exception),
        )
        
        # In debug mode, include stack trace
        if settings.DEBUG:
            return self._json_response(
                error="internal_error",
                message=str(exception),
                status=500,
                details={
                    "type": type(exception).__name__,
                    "traceback": traceback.format_exc(),
                },
            )
        
        # In production, return generic message
        return self._json_response(
            error="internal_error",
            message="An unexpected error occurred. Please try again later.",
            status=500,
        )
    
    def _json_response(
        self,
        error: str,
        message: str,
        status: int,
        details: dict = None,
    ) -> JsonResponse:
        """Create JSON error response."""
        data = {
            "error": error,
            "message": message,
        }
        
        if details:
            data["details"] = details
        
        return JsonResponse(data, status=status)
```

### 13.2 Custom Exceptions

```python
# apps/core/exceptions/base.py
"""Base exception classes."""
from typing import Optional, Dict, Any


class APIException(Exception):
    """Base exception for API errors."""
    
    status_code: int = 500
    error_code: str = "internal_error"
    default_message: str = "An error occurred"
    
    def __init__(
        self,
        message: str = None,
        details: Dict[str, Any] = None,
    ):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return self.message


class ValidationError(APIException):
    """Validation error."""
    status_code = 400
    error_code = "validation_error"
    default_message = "Validation failed"


class NotFoundError(APIException):
    """Resource not found."""
    status_code = 404
    error_code = "not_found"
    default_message = "Resource not found"


class ConflictError(APIException):
    """Resource conflict."""
    status_code = 409
    error_code = "conflict"
    default_message = "Resource conflict"


class RateLimitError(APIException):
    """Rate limit exceeded."""
    status_code = 429
    error_code = "rate_limit_exceeded"
    default_message = "Too many requests"


# apps/core/exceptions/auth.py
"""Authentication and authorization exceptions."""
from .base import APIException


class AuthenticationError(APIException):
    """Authentication failed."""
    status_code = 401
    error_code = "authentication_failed"
    default_message = "Authentication required"


class TokenExpiredError(AuthenticationError):
    """Token has expired."""
    error_code = "token_expired"
    default_message = "Authentication token has expired"


class InvalidTokenError(AuthenticationError):
    """Token is invalid."""
    error_code = "invalid_token"
    default_message = "Invalid authentication token"


class PermissionDeniedError(APIException):
    """Permission denied."""
    status_code = 403
    error_code = "permission_denied"
    default_message = "You do not have permission to perform this action"


class InsufficientScopeError(PermissionDeniedError):
    """API key lacks required scope."""
    error_code = "insufficient_scope"
    default_message = "API key lacks required scope for this operation"


# apps/core/exceptions/tenant.py
"""Tenant-related exceptions."""
from .base import APIException


class TenantError(APIException):
    """Base tenant error."""
    status_code = 400
    error_code = "tenant_error"


class TenantNotFoundError(TenantError):
    """Tenant not found."""
    status_code = 404
    error_code = "tenant_not_found"
    default_message = "Tenant not found"


class TenantSuspendedError(TenantError):
    """Tenant is suspended."""
    status_code = 403
    error_code = "tenant_suspended"
    default_message = "Tenant account is suspended"


class TenantRequiredError(TenantError):
    """Tenant context required."""
    status_code = 400
    error_code = "tenant_required"
    default_message = "Tenant context is required for this operation"


class TenantLimitExceededError(TenantError):
    """Tenant limit exceeded."""
    status_code = 403
    error_code = "tenant_limit_exceeded"
    default_message = "Tenant limit exceeded"
```

### 13.3 Security Headers Middleware

```python
# apps/core/middleware/security.py
"""Security headers middleware."""
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses.
    """
    
    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Add security headers."""
        
        # Content Security Policy
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' wss: https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        
        # Prevent MIME type sniffing
        response["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        response["X-Frame-Options"] = "DENY"
        
        # XSS protection (legacy browsers)
        response["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer policy
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy
        response["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(self), "  # Allow microphone for voice
            "payment=(), "
            "usb=()"
        )
        
        return response
```

---

## 14. Deployment Architecture

### 14.1 Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.12-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/production.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command
CMD ["gunicorn", "config.asgi:application", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2", \
     "--access-logfile", "-", "--error-logfile", "-"]
```

### 14.2 Docker Compose (Development)

```yaml
# docker-compose.yml
version: "3.9"

services:
  # ==========================================================================
  # APPLICATION
  # ==========================================================================
  
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: avb_backend
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
      - DB_HOST=postgres
      - DB_NAME=agentvoicebox
      - DB_USER=agentvoicebox
      - DB_PASSWORD=agentvoicebox_dev
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/4
      - KEYCLOAK_URL=http://keycloak:8080
      - SPICEDB_ENDPOINT=spicedb:50051
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - avb-network
  
  celery-worker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: avb_celery_worker
    command: celery -A config worker -l INFO -Q default,stt,tts,llm,billing
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
      - DB_HOST=postgres
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/4
    volumes:
      - .:/app
    depends_on:
      - backend
      - redis
    networks:
      - avb-network
  
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: avb_celery_beat
    command: celery -A config beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.development
      - DB_HOST=postgres
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/4
    volumes:
      - .:/app
    depends_on:
      - backend
      - redis
    networks:
      - avb-network
  
  # ==========================================================================
  # INFRASTRUCTURE
  # ==========================================================================
  
  postgres:
    image: postgres:16-alpine
    container_name: avb_postgres
    environment:
      POSTGRES_DB: agentvoicebox
      POSTGRES_USER: agentvoicebox
      POSTGRES_PASSWORD: agentvoicebox_dev
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agentvoicebox"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - avb-network
  
  redis:
    image: redis:7-alpine
    container_name: avb_redis
    command: redis-server --appendonly yes
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - avb-network
  
  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    container_name: avb_keycloak
    command: start-dev
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin
      KC_DB: postgres
      KC_DB_URL: jdbc:postgresql://postgres:5432/keycloak
      KC_DB_USERNAME: agentvoicebox
      KC_DB_PASSWORD: agentvoicebox_dev
    ports:
      - "8080:8080"
    depends_on:
      postgres:
        condition: service_healthy
    networks:
      - avb-network
  
  spicedb:
    image: authzed/spicedb:v1.30.0
    container_name: avb_spicedb
    command: serve --grpc-preshared-key "dev-key" --datastore-engine memory
    ports:
      - "50051:50051"
    networks:
      - avb-network

volumes:
  postgres_data:
  redis_data:

networks:
  avb-network:
    driver: bridge
```

### 14.3 Kubernetes Deployment (Production)

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: avb-backend
  labels:
    app: avb-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: avb-backend
  template:
    metadata:
      labels:
        app: avb-backend
    spec:
      containers:
        - name: backend
          image: agentvoicebox/backend:latest
          ports:
            - containerPort: 8000
          env:
            - name: DJANGO_SETTINGS_MODULE
              value: config.settings.production
            - name: DB_HOST
              valueFrom:
                secretKeyRef:
                  name: avb-secrets
                  key: db-host
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: avb-secrets
                  key: db-password
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
            limits:
              memory: "1Gi"
              cpu: "1000m"
          livenessProbe:
            httpGet:
              path: /health/
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: avb-backend
spec:
  selector:
    app: avb-backend
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
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
  maxReplicas: 10
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
```

---

## 15. Summary

This Django SaaS Architecture specification provides a complete blueprint for building the AgentVoiceBox platform with:

1. **Multi-Tenancy**: Thread-local tenant context, tenant-scoped models, automatic filtering
2. **Authentication**: Keycloak JWT integration, API key support, session management
3. **Authorization**: SpiceDB fine-grained permissions, role-based access control
4. **API Layer**: Django Ninja with OpenAPI, Pydantic schemas, service layer pattern
5. **Real-Time**: Django Channels WebSocket, event streaming, session management
6. **Background Tasks**: Celery with Redis, scheduled tasks, tenant-aware tasks
7. **Observability**: Structlog, Prometheus metrics, audit logging
8. **Security**: Exception handling, rate limiting, security headers
9. **Deployment**: Docker, Kubernetes, horizontal scaling

All components follow Django best practices and enterprise patterns for maintainability, scalability, and security.
