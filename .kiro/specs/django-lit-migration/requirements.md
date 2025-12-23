# Requirements Document

## Introduction

This document specifies the requirements for migrating the AgentVoiceBox platform from the current Flask + React architecture to Django + Django Ninja + Lit. This migration includes:

1. **Removal of the root blog project** - The static Next.js blog at the repository root
2. **Backend migration** - Flask + Gevent → Django + Django Ninja
3. **Frontend migration** - React + Next.js → Lit 3.x web components
4. **Admin Portal as default** - The admin dashboard becomes the primary landing page
5. **AgentSkin theming system** - 26+ CSS custom properties for dynamic theming
6. **Voice provider integration** - Local (Whisper/Kokoro) and AgentVoiceBox support
7. **SpiceDB permissions** - Google Zanzibar-based permission system

## Glossary

- **Django**: Python web framework with batteries-included approach (ORM, admin, auth, migrations)
- **Django Ninja**: Fast, async-capable REST API framework for Django with automatic OpenAPI docs
- **Lit**: Google's lightweight library for building fast web components with reactive properties
- **Web Components**: Browser-native component model using Custom Elements, Shadow DOM, and HTML Templates
- **Pydantic**: Data validation library (retained for schema validation in Django Ninja)
- **SQLAlchemy**: Current ORM (to be replaced by Django ORM)
- **Flask**: Current backend framework (to be replaced)
- **Gevent**: Current async worker (to be replaced by Django's ASGI support)
- **AgentSkin**: Theme system using CSS Custom Properties (26+ variables required)
- **SpiceDB**: Google Zanzibar-based permission system for enterprise scale
- **AgentVoiceBox**: External voice service with full speech-on-speech capability
- **Local Voice**: On-device STT (Whisper) + TTS (Kokoro), NO speech-on-speech
- **Agent Mode**: Operational state: STD, TRN, ADM, DEV, RO, DGR

---

## Requirements

---

### Requirement 1: Blog Removal

**User Story:** As a platform operator, I want to remove the standalone blog, so that the repository focuses solely on the AgentVoiceBox platform.

#### Acceptance Criteria

1. WHEN the migration is complete THEN the following root-level files SHALL be removed:
   - `src/` directory (Next.js blog app)
   - `_posts/` directory (markdown blog posts)
   - `public/` directory (blog static assets)
   - `package.json`, `package-lock.json` (blog dependencies)
   - `next.config.js`, `tailwind.config.ts`, `postcss.config.js`, `tsconfig.json` (blog config)
2. WHEN the blog is removed THEN the chat WebSocket test functionality SHALL be preserved in the portal frontend
3. WHEN the blog is removed THEN the repository root SHALL contain only platform-related files and the `ovos-voice-agent/` directory
4. WHEN the migration is complete THEN the `.gitignore` and `.dockerignore` SHALL be updated to remove blog-specific entries

---

### Requirement 2: Django Backend Setup

**User Story:** As a developer, I want the backend built on Django, so that I can leverage Django's mature ecosystem, ORM, and admin interface.

#### Acceptance Criteria

1. WHEN the Django backend is created THEN it SHALL be located at `ovos-voice-agent/AgentVoiceBoxEngine/backend/`
2. WHEN the Django project is initialized THEN it SHALL use the following structure:
   ```
   backend/
   ├── manage.py
   ├── config/                    # Django project settings
   │   ├── __init__.py
   │   ├── settings/
   │   │   ├── __init__.py
   │   │   ├── base.py           # Common settings
   │   │   ├── development.py    # Dev overrides
   │   │   └── production.py     # Prod overrides
   │   ├── urls.py
   │   ├── asgi.py
   │   └── wsgi.py
   ├── apps/                      # Django applications
   │   ├── core/                  # Shared utilities
   │   ├── tenants/               # Multi-tenant management
   │   ├── projects/              # Project management
   │   ├── api_keys/              # API key management
   │   ├── sessions/              # Voice session management
   │   ├── billing/               # Lago integration
   │   ├── voice/                 # Voice pipeline (STT/TTS/LLM)
   │   └── observability/         # Metrics and logging
   └── requirements/
       ├── base.txt
       ├── development.txt
       └── production.txt
   ```
3. WHEN Django is configured THEN it SHALL support async views using ASGI (Uvicorn/Daphne)
4. WHEN Django is configured THEN it SHALL use PostgreSQL 16 as the database backend
5. WHEN Django is configured THEN it SHALL use Redis for caching and session storage
6. WHEN Django is configured THEN it SHALL integrate with Keycloak for authentication via OIDC

---

### Requirement 3: Django Ninja API Layer

**User Story:** As a developer, I want Django Ninja for the REST API, so that I get automatic OpenAPI documentation and Pydantic validation.

#### Acceptance Criteria

1. WHEN Django Ninja is configured THEN it SHALL expose APIs at `/api/v1/` prefix
2. WHEN Django Ninja is configured THEN it SHALL provide automatic OpenAPI 3.1 documentation at `/api/docs`
3. WHEN defining API schemas THEN the system SHALL use Pydantic models for request/response validation
4. WHEN defining API endpoints THEN the system SHALL use Django Ninja routers organized by domain:
   - `/api/v1/admin/` - SaaS admin endpoints
   - `/api/v1/tenants/` - Tenant management
   - `/api/v1/projects/` - Project management
   - `/api/v1/keys/` - API key management
   - `/api/v1/sessions/` - Voice session management
   - `/api/v1/billing/` - Billing and usage
   - `/api/v1/voice/` - Voice configuration (TTS/STT/LLM)
5. WHEN handling authentication THEN Django Ninja SHALL validate JWT tokens from Keycloak
6. WHEN handling errors THEN Django Ninja SHALL return consistent error responses with `error_code`, `message`, and `details`

---

### Requirement 4: Django ORM Migration

**User Story:** As a developer, I want to use Django ORM, so that I can leverage Django's migration system and admin interface.

#### Acceptance Criteria

1. WHEN migrating models THEN the following SQLAlchemy models SHALL be converted to Django models:
   - `Tenant` → `apps.tenants.models.Tenant`
   - `Project` → `apps.projects.models.Project`
   - `APIKey` → `apps.api_keys.models.APIKey`
   - `Session` → `apps.sessions.models.Session`
   - `ConversationItem` → `apps.sessions.models.ConversationItem`
   - `UsageRecord` → `apps.billing.models.UsageRecord`
2. WHEN defining models THEN they SHALL use Django's built-in field types with appropriate indexes
3. WHEN defining multi-tenant models THEN they SHALL include `tenant_id` foreign key with database-level partitioning support
4. WHEN migrations are created THEN they SHALL be compatible with PostgreSQL 16 features (partitioning, JSONB)
5. WHEN the Django admin is configured THEN it SHALL provide management interfaces for all models

---

### Requirement 5: WebSocket Support

**User Story:** As a developer, I want WebSocket support in Django, so that I can handle real-time voice sessions.

#### Acceptance Criteria

1. WHEN WebSocket support is needed THEN the system SHALL use Django Channels with Redis channel layer
2. WHEN a WebSocket connection is established at `/v1/realtime` THEN Django Channels SHALL handle the connection
3. WHEN processing WebSocket messages THEN the system SHALL maintain compatibility with the existing OpenAI Realtime API protocol
4. WHEN scaling WebSocket connections THEN the system SHALL support horizontal scaling via Redis Pub/Sub
5. WHEN a WebSocket connection is authenticated THEN the system SHALL validate the API key and extract tenant context

---

### Requirement 6: Lit Frontend Setup

**User Story:** As a developer, I want the frontend built with Lit, so that I can use lightweight, standards-based web components.

#### Acceptance Criteria

1. WHEN the Lit frontend is created THEN it SHALL be located at `ovos-voice-agent/AgentVoiceBoxEngine/frontend/`
2. WHEN the Lit project is initialized THEN it SHALL use the following structure:
   ```
   frontend/
   ├── package.json
   ├── tsconfig.json
   ├── vite.config.ts
   ├── index.html
   ├── src/
   │   ├── main.ts                # Application entry
   │   ├── router.ts              # Client-side routing
   │   ├── styles/                # Global styles
   │   │   ├── tokens.css         # Design tokens
   │   │   └── base.css           # Base styles
   │   ├── components/            # Reusable components
   │   │   ├── ui/                # Primitive UI components
   │   │   ├── layout/            # Layout components
   │   │   └── forms/             # Form components
   │   ├── pages/                 # Page components
   │   │   ├── admin/             # Admin portal pages
   │   │   ├── dashboard/         # Tenant dashboard pages
   │   │   └── settings/          # Settings pages
   │   ├── services/              # API clients
   │   ├── stores/                # State management
   │   └── utils/                 # Utilities
   └── public/                    # Static assets
   ```
3. WHEN Lit components are created THEN they SHALL use TypeScript with strict mode
4. WHEN Lit components are styled THEN they SHALL use CSS custom properties (design tokens) for theming
5. WHEN the frontend is built THEN it SHALL produce optimized bundles using Vite

---

### Requirement 7: Lit Component Architecture

**User Story:** As a developer, I want a consistent component architecture, so that the UI is maintainable and performant.

#### Acceptance Criteria

1. WHEN creating Lit components THEN they SHALL extend `LitElement` and use decorators (`@customElement`, `@property`, `@state`)
2. WHEN creating UI primitives THEN they SHALL be framework-agnostic web components usable outside the application
3. WHEN handling forms THEN the system SHALL use native form validation with custom Lit form components
4. WHEN handling state THEN the system SHALL use a lightweight reactive store (e.g., `@lit/context` or custom stores)
5. WHEN handling routing THEN the system SHALL use `@vaadin/router` or similar client-side router
6. WHEN handling API calls THEN the system SHALL use a typed fetch wrapper with automatic token refresh

---

### Requirement 8: Admin Portal as Default

**User Story:** As a platform operator, I want the admin portal as the default landing page, so that administrators see the system overview immediately.

#### Acceptance Criteria

1. WHEN a user navigates to the root URL (`/`) THEN the system SHALL redirect to `/admin/dashboard` for admin users
2. WHEN a user navigates to the root URL (`/`) THEN the system SHALL redirect to `/dashboard` for tenant users
3. WHEN the admin dashboard loads THEN it SHALL display platform-wide metrics: total tenants, active sessions, API requests, revenue
4. WHEN the admin dashboard loads THEN it SHALL display system health for all services
5. WHEN navigation is rendered THEN the admin portal SHALL show admin-specific navigation items

---

### Requirement 9: Authentication Integration

**User Story:** As a developer, I want seamless Keycloak integration, so that users can authenticate securely.

#### Acceptance Criteria

1. WHEN a user accesses a protected route THEN the frontend SHALL redirect to Keycloak login
2. WHEN Keycloak returns tokens THEN the frontend SHALL store them securely and include in API requests
3. WHEN tokens expire THEN the frontend SHALL automatically refresh using the refresh token
4. WHEN a user logs out THEN the frontend SHALL clear tokens and redirect to Keycloak logout
5. WHEN extracting user info THEN the frontend SHALL decode JWT claims for tenant_id, roles, and permissions

---

### Requirement 10: Migration Strategy

**User Story:** As a platform operator, I want a phased migration, so that the system remains operational during the transition.

#### Acceptance Criteria

1. WHEN Phase 1 begins THEN the blog SHALL be removed and the repository cleaned
2. WHEN Phase 2 begins THEN the Django backend SHALL be created alongside the existing Flask backend
3. WHEN Phase 3 begins THEN API endpoints SHALL be migrated incrementally with feature flags
4. WHEN Phase 4 begins THEN the Lit frontend SHALL be created alongside the existing React frontend
5. WHEN Phase 5 begins THEN the old Flask backend and React frontend SHALL be deprecated and removed
6. WHEN each phase completes THEN all existing tests SHALL pass and functionality SHALL be verified

---

### Requirement 11: AgentSkin Theme System

**User Story:** As a user, I want to customize the visual appearance using the AgentSkin theme system, so that I can personalize my workspace with validated, secure themes.

#### Acceptance Criteria

1. THE Theme_System SHALL use CSS Custom Properties for all themeable values (26 variables minimum)
2. WHEN theme is applied THEN the Theme_System SHALL inject variables within 50ms
3. THE Theme_System SHALL support theme JSON format with name, version, author, variables
4. WHEN theme file is dropped THEN the Theme_System SHALL validate against JSON Schema
5. THE Theme_System SHALL persist active theme to localStorage
6. WHEN theme contains `url()` in CSS values THEN the Theme_System SHALL reject (XSS prevention)
7. THE Theme_System SHALL provide default themes: Default Light, Midnight Dark, High Contrast
8. THE Theme_System SHALL support remote theme loading via HTTPS only
9. WHEN theme is previewed THEN the Theme_System SHALL show split-screen comparison
10. THE Theme_System SHALL validate WCAG AA contrast ratios (4.5:1 minimum)
11. THE Theme_System SHALL enforce rate limiting (10 uploads/hour/user)

---

### Requirement 12: SpiceDB Permission System

**User Story:** As a security architect, I want a globally consistent, high-performance permission system supporting millions of checks per second, so that I can enforce access control at enterprise scale.

#### Acceptance Criteria

1. THE Permission_System SHALL deploy SpiceDB as the permission authority
2. WHEN a permission check executes THEN the Permission_System SHALL respond within 10ms (p95)
3. THE Permission_System SHALL support 1,000,000+ permission checks per second
4. WHEN SpiceDB is unavailable THEN the Permission_System SHALL deny all requests (fail-closed)
5. THE Permission_System SHALL cache permission decisions in Redis with TTL 60s
6. WHEN a role changes THEN the Permission_System SHALL propagate changes within 5 seconds
7. THE Permission_System SHALL support hierarchical role inheritance
8. THE Permission_System SHALL provide default roles: SysAdmin, Admin, Developer, Trainer, User, Viewer
9. WHEN a user requests an action THEN the Permission_System SHALL verify tenant isolation

---

### Requirement 13: Local Voice System (STT + TTS)

**User Story:** As a user, I want to use local voice capabilities (Whisper STT + Kokoro TTS) running on my device, so that I can have voice input/output without external dependencies.

#### Acceptance Criteria

1. THE Local_Voice SHALL provide STT via Whisper (CPU or GPU auto-detection)
2. THE Local_Voice SHALL provide TTS via Kokoro (CPU or GPU auto-detection)
3. THE Local_Voice SHALL NOT support real-time speech-on-speech (use AgentVoiceBox for that)
4. WHEN GPU is available THEN the Local_Voice SHALL use CUDA-optimized models
5. WHEN GPU is unavailable THEN the Local_Voice SHALL fallback to CPU models
6. THE Local_Voice SHALL support Whisper model sizes: tiny, base, small, medium, large
7. THE Local_Voice SHALL support Kokoro model sizes: 82M, 200M
8. WHEN voice is enabled THEN the Local_Voice SHALL preload models at startup
9. THE Local_Voice SHALL support 15+ languages via Kokoro TTS
10. THE Local_Voice SHALL detect hardware architecture at Docker build time

---

### Requirement 14: AgentVoiceBox Integration (Speech-on-Speech)

**User Story:** As a user, I want full real-time speech-on-speech capability via AgentVoiceBox, so that I can have natural voice conversations with the agent.

#### Acceptance Criteria

1. THE AgentVoiceBox SHALL provide full real-time speech-on-speech capability
2. THE AgentVoiceBox SHALL connect via WebSocket to /v1/realtime endpoint
3. THE AgentVoiceBox SHALL support OpenAI Realtime API protocol compatibility
4. THE AgentVoiceBox SHALL support bidirectional audio streaming
5. WHEN AgentVoiceBox is active THEN the System SHALL achieve latency < 150ms end-to-end
6. THE AgentVoiceBox SHALL support turn detection and interruption handling
7. THE AgentVoiceBox SHALL support dual VAD (WebRTC + Silero)
8. THE AgentVoiceBox SHALL support noise reduction and AGC
9. WHEN AgentVoiceBox is local THEN the System SHALL connect to localhost
10. WHEN AgentVoiceBox is remote THEN the System SHALL connect via configured URL
11. THE AgentVoiceBox SHALL support 1000+ concurrent voice sessions per server

---

### Requirement 15: Voice Provider Selection

**User Story:** As a user, I want to choose between Local Voice and AgentVoiceBox in Settings, so that I can select the voice capability that fits my needs.

#### Acceptance Criteria

1. THE Settings SHALL allow user to select voice provider: local, agentvoicebox, or disabled
2. WHEN provider is "local" THEN the System SHALL use Local_Voice for STT/TTS only
3. WHEN provider is "agentvoicebox" THEN the System SHALL use AgentVoiceBox for full speech-on-speech
4. WHEN provider is "disabled" THEN the System SHALL hide all voice UI elements
5. THE Settings SHALL show provider-specific configuration fields dynamically
6. WHEN provider changes THEN the System SHALL validate new configuration
7. THE Settings SHALL provide "Test Connection" button for AgentVoiceBox
8. WHEN test connection succeeds THEN the Settings SHALL show green checkmark
9. THE Settings SHALL include Voice/Speech section in Connectivity tab
10. WHEN voice provider changes THEN the System SHALL emit settings.changed event

---

### Requirement 16: Mode State Management

**User Story:** As a user, I want to switch between agent modes (STD, TRN, ADM, DEV, RO, DGR) based on my permissions, so that I can access appropriate features for my role.

#### Acceptance Criteria

1. THE Mode_Manager SHALL maintain current mode state per session
2. WHEN mode changes THEN the Mode_Manager SHALL emit `mode.changed` event via WebSocket
3. THE Mode_Manager SHALL persist mode preference per user in PostgreSQL
4. WHEN session starts THEN the Mode_Manager SHALL restore last mode if permitted
5. WHEN user requests mode change THEN the Mode_Manager SHALL verify permissions via SpiceDB
6. IF user lacks permission for target mode THEN the Mode_Manager SHALL reject with HTTP 403
7. WHEN transitioning to DEGRADED mode THEN the Mode_Manager SHALL NOT require user action
8. THE Mode_Manager SHALL log all mode transitions to audit trail
9. THE Mode_Manager SHALL support modes: STD, TRN, ADM, DEV, RO, DGR
10. WHEN mode is DEGRADED THEN the Mode_Manager SHALL disable non-essential features

---

### Requirement 17: Real-Time Communication

**User Story:** As a user, I want real-time updates via WebSocket for mode changes, settings updates, and voice events, so that I can see changes immediately without refreshing.

#### Acceptance Criteria

1. THE Realtime_System SHALL use WebSocket for bidirectional communication
2. WHEN server event occurs THEN the Realtime_System SHALL deliver to client within 100ms
3. THE Realtime_System SHALL support SSE fallback when WebSocket unavailable
4. WHEN connection drops THEN the Realtime_System SHALL reconnect with exponential backoff
5. THE Realtime_System SHALL send heartbeat every 20 seconds
6. WHEN client reconnects THEN the Realtime_System SHALL replay missed events
7. THE Realtime_System SHALL support event types: mode.changed, settings.changed, theme.changed, voice.*
8. THE Realtime_System SHALL authenticate WebSocket connections via token
9. THE Realtime_System SHALL support 10,000 concurrent connections per node
10. WHEN WebSocket fails THEN the Realtime_System SHALL fallback to SSE automatically

---

### Requirement 18: Lit Component Architecture (Eye of God UIX)

**User Story:** As a developer, I want a comprehensive Lit component library following the Eye of God UIX specification, so that I can build consistent, accessible, and performant interfaces.

#### Acceptance Criteria

1. THE UI_Layer SHALL use Lit 3.x Web Components with Shadow DOM encapsulation
2. WHEN a component renders THEN the UI_Layer SHALL complete rendering within 16ms (60fps)
3. THE UI_Layer SHALL expose reactive properties via Lit's `@property` decorator
4. WHEN theme variables change THEN the UI_Layer SHALL update all components within 50ms
5. THE UI_Layer SHALL lazy-load non-critical components via dynamic imports
6. WHEN the application loads THEN the UI_Layer SHALL achieve First Contentful Paint < 1.5s
7. THE UI_Layer SHALL use CSS Custom Properties for all themeable values
8. WHEN offline THEN the UI_Layer SHALL serve cached assets via Service Worker
9. THE UI_Layer SHALL support 1,000,000+ concurrent WebSocket connections
10. THE UI_Layer SHALL render at 60fps during all user interactions

---

### Requirement 19: Accessibility (WCAG 2.1 AA)

**User Story:** As a user with disabilities, I want the interface to be fully accessible via keyboard, screen readers, and high contrast modes, so that I can use the system effectively.

#### Acceptance Criteria

1. THE Accessibility SHALL comply with WCAG 2.1 AA standards
2. THE Accessibility SHALL support keyboard navigation for all interactive elements
3. WHEN focus changes THEN the Accessibility SHALL show visible focus indicator
4. THE Accessibility SHALL provide ARIA labels for all controls
5. THE Accessibility SHALL support screen readers (NVDA, VoiceOver, JAWS)
6. WHEN color is used for meaning THEN the Accessibility SHALL provide alternative indicator
7. THE Accessibility SHALL support reduced motion preference
8. THE Accessibility SHALL maintain contrast ratio >= 4.5:1 for all text
9. THE Accessibility SHALL provide skip navigation links
10. THE Accessibility SHALL support text scaling up to 200%

---

### Requirement 20: Performance (Enterprise Scale)

**User Story:** As a platform architect, I want the system to support millions of concurrent users with sub-second response times, so that I can serve enterprise-scale deployments.

#### Acceptance Criteria

1. THE System SHALL support 1,000,000+ concurrent WebSocket connections
2. THE System SHALL achieve First Contentful Paint < 1.5 seconds
3. THE System SHALL achieve Time to Interactive < 3 seconds
4. WHEN theme switches THEN the System SHALL complete transition < 300ms
5. THE API_Layer SHALL achieve response time < 50ms (p95)
6. THE Permission_System SHALL achieve check time < 10ms (p95)
7. THE System SHALL support 10,000 concurrent WebSocket connections per node
8. WHEN under load THEN the System SHALL maintain 99.9% availability
9. THE System SHALL achieve Lighthouse score > 90 for all categories
10. THE Django_Ninja_API SHALL handle 100,000+ requests/second per node
11. THE Lit_UI SHALL render 60fps during all interactions
12. THE System SHALL support horizontal scaling via Kubernetes

---

## Technology Decisions

### Why Django + Django Ninja

| Aspect | Flask (Current) | Django + Django Ninja (Target) |
|--------|-----------------|-------------------------------|
| ORM | SQLAlchemy (manual migrations) | Django ORM (built-in migrations) |
| Admin | None (custom) | Django Admin (built-in) |
| Auth | Custom JWT validation | Django auth + Keycloak integration |
| API Docs | Manual OpenAPI | Automatic OpenAPI via Django Ninja |
| Async | Gevent (greenlets) | Native ASGI (Uvicorn) |
| Ecosystem | Smaller | Larger, more mature |
| Permissions | OPA (custom) | SpiceDB (Google Zanzibar) |

### Why Lit 3.x

| Aspect | React (Current) | Lit 3.x (Target) |
|--------|-----------------|--------------|
| Bundle Size | ~40KB (React + ReactDOM) | ~5KB (Lit) |
| Standards | Virtual DOM, JSX | Native Web Components |
| SSR | Requires Next.js | Optional (works without) |
| Learning Curve | React-specific patterns | Web platform standards |
| Interoperability | React ecosystem only | Works with any framework |
| Shadow DOM | No (CSS leaks) | Yes (style encapsulation) |
| Scale | Good | Excellent (millions of users) |

### Why SpiceDB

| Aspect | OPA (Current) | SpiceDB (Target) |
|--------|---------------|------------------|
| Model | Policy-based | Relationship-based (Zanzibar) |
| Scale | Thousands/sec | Millions/sec |
| Caching | Manual | Built-in with Redis |
| Hierarchy | Manual | Native inheritance |
| Consistency | Eventual | Strong |

---

## UI Component Catalog (Eye of God UIX)

### Primitive Components

| Component | Tag | Purpose |
|-----------|-----|---------|
| Button | `<eog-button>` | Primary action trigger |
| Input | `<eog-input>` | Text input field |
| Select | `<eog-select>` | Dropdown selection |
| Toggle | `<eog-toggle>` | Boolean switch |
| Slider | `<eog-slider>` | Range input |
| Modal | `<eog-modal>` | Dialog overlay |
| Toast | `<eog-toast>` | Notification popup |
| Card | `<eog-card>` | Content container |
| Tabs | `<eog-tabs>` | Tab navigation |
| Spinner | `<eog-spinner>` | Loading indicator |
| Badge | `<eog-badge>` | Status indicator |
| Avatar | `<eog-avatar>` | User/agent image |
| Icon | `<eog-icon>` | SVG icon wrapper |
| Tooltip | `<eog-tooltip>` | Hover information |
| Progress | `<eog-progress>` | Progress bar |

### Layout Components

| Component | Tag | Purpose |
|-----------|-----|---------|
| App Shell | `<eog-app>` | Root application |
| Header | `<eog-header>` | Top navigation bar |
| Sidebar | `<eog-sidebar>` | Side navigation |
| Main | `<eog-main>` | Content area |
| Panel | `<eog-panel>` | Collapsible section |
| Split | `<eog-split>` | Resizable split view |
| Grid | `<eog-grid>` | CSS Grid wrapper |
| Stack | `<eog-stack>` | Flex stack layout |

### View Components (Pages)

| Component | Tag | Route | Permission |
|-----------|-----|-------|------------|
| Chat | `<eog-chat>` | `/chat` | `tenant->use` |
| Memory | `<eog-memory>` | `/memory` | `tenant->view` |
| Tools | `<eog-tools>` | `/tools` | `tenant->view` |
| Settings | `<eog-settings>` | `/settings` | `tenant->view` |
| Themes | `<eog-themes>` | `/themes` | `tenant->view` |
| Voice | `<eog-voice>` | `/voice` | `tenant->use` |
| Cognitive | `<eog-cognitive>` | `/cognitive` | `tenant->train` |
| Admin | `<eog-admin>` | `/admin` | `tenant->administrate` |
| Audit | `<eog-audit>` | `/audit` | `tenant->administrate` |

### Voice Components

| Component | Tag | Purpose |
|-----------|-----|---------|
| Voice Controls | `<eog-voice-controls>` | Record/Stop/Mute buttons |
| Voice Indicator | `<eog-voice-indicator>` | State and audio level |
| Voice Overlay | `<eog-voice-overlay>` | Floating voice UI |
| Voice Visualizer | `<eog-voice-visualizer>` | Audio waveform |
| Voice Transcript | `<eog-voice-transcript>` | Live transcription |

### Theme Components

| Component | Tag | Purpose |
|-----------|-----|---------|
| Theme Gallery | `<eog-theme-gallery>` | Browse themes |
| Theme Card | `<eog-theme-card>` | Theme preview |
| Theme Preview | `<eog-theme-preview>` | Split comparison |
| Theme Editor | `<eog-theme-editor>` | Customize theme |
| Theme Upload | `<eog-theme-upload>` | Import theme |

---

## AgentSkin CSS Variables (26 Required)

```css
:root {
  /* Background Colors */
  --eog-bg-void: #0f172a;
  --eog-bg-surface: rgba(30, 41, 59, 0.85);
  --eog-bg-elevated: rgba(51, 65, 85, 0.9);
  
  /* Glass Effects */
  --eog-glass-surface: rgba(30, 41, 59, 0.85);
  --eog-glass-border: rgba(255, 255, 255, 0.05);
  
  /* Text Colors */
  --eog-text-main: #e2e8f0;
  --eog-text-dim: #64748b;
  
  /* Accent Colors */
  --eog-accent-primary: #3b82f6;
  --eog-accent-secondary: #8b5cf6;
  --eog-accent-success: #22c55e;
  --eog-accent-warning: #f59e0b;
  --eog-accent-danger: #ef4444;
  
  /* Shadows */
  --eog-shadow-soft: 0 10px 40px -10px rgba(0, 0, 0, 0.5);
  
  /* Border Radius */
  --eog-radius-sm: 4px;
  --eog-radius-md: 8px;
  --eog-radius-lg: 16px;
  --eog-radius-full: 9999px;
  
  /* Spacing */
  --eog-spacing-xs: 4px;
  --eog-spacing-sm: 8px;
  --eog-spacing-md: 16px;
  --eog-spacing-lg: 24px;
  --eog-spacing-xl: 32px;
  
  /* Typography */
  --eog-font-sans: 'Space Grotesk', system-ui, sans-serif;
  --eog-font-mono: 'JetBrains Mono', monospace;
  --eog-text-xs: 10px;
  --eog-text-sm: 12px;
  --eog-text-base: 14px;
  --eog-text-lg: 16px;
}
```

---

## Dependencies

### Django Backend

```
# base.txt
django>=5.0,<6.0
django-ninja>=1.3,<2.0
django-cors-headers>=4.3,<5.0
django-redis>=5.4,<6.0
channels>=4.0,<5.0
channels-redis>=4.2,<5.0
psycopg[binary]>=3.1,<4.0
pydantic>=2.5,<3.0
pydantic-settings>=2.1,<3.0
python-jose[cryptography]>=3.3,<4.0
httpx>=0.27,<1.0
uvicorn[standard]>=0.27,<1.0
gunicorn>=21.0,<23.0
prometheus-client>=0.19,<1.0
structlog>=24.1,<25.0
authzed>=0.14,<1.0  # SpiceDB client
grpcio>=1.60,<2.0   # gRPC for SpiceDB
hypothesis>=6.0,<7.0  # Property-based testing
```

### Lit Frontend

```json
{
  "dependencies": {
    "lit": "^3.1.0",
    "@lit/context": "^1.1.0",
    "@lit-labs/signals": "^1.0.0",
    "@vaadin/router": "^1.7.5"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@open-wc/testing": "^4.0.0",
    "web-test-runner": "^0.18.0",
    "fast-check": "^3.15.0",
    "playwright": "^1.40.0"
  }
}
```

---

## State Management (Lit Context + Signals)

### Store Architecture

| Store | Purpose | Key State |
|-------|---------|-----------|
| AuthStore | Authentication | user, token, tenant_id |
| ModeStore | Agent mode | current, available, loading |
| ThemeStore | Active theme | active, list, preview |
| PermStore | Permissions | cache, roles, loading |
| VoiceStore | Voice state | provider, state, config |
| SettingsStore | Settings | tabs, values, dirty |
| ChatStore | Chat state | messages, streaming, session |

---

## Migration Phases

### Phase 1: Blog Removal (Week 1)
- Remove `src/`, `_posts/`, `public/` directories
- Remove root `package.json`, `next.config.js`, etc.
- Update `.gitignore`, `.dockerignore`
- Preserve chat WebSocket test in portal

### Phase 2: Django Backend Setup (Weeks 2-3)
- Initialize Django project structure
- Configure Django Ninja API
- Set up Django Channels for WebSocket
- Migrate database models from SQLAlchemy to Django ORM
- Create initial migrations
- Integrate SpiceDB for permissions

### Phase 3: API Migration (Weeks 4-6)
- Migrate REST endpoints incrementally
- Implement authentication middleware
- Migrate WebSocket handlers
- Run both Flask and Django in parallel with feature flags
- Implement SpiceDB permission checks

### Phase 4: Lit Frontend Setup (Weeks 7-10)
- Initialize Lit project with Vite
- Create UI component library (primitives)
- Create layout components (shell, header, sidebar)
- Implement routing and state management
- Implement AgentSkin theme system
- Migrate pages from React to Lit

### Phase 5: Voice Integration (Weeks 11-12)
- Implement VoiceStore and VoiceService
- Create voice UI components
- Integrate Local Voice (Whisper/Kokoro)
- Integrate AgentVoiceBox provider
- Implement voice settings UI

### Phase 6: Cutover and Cleanup (Week 13)
- Remove Flask backend
- Remove React frontend
- Update Docker Compose
- Update documentation
- Performance testing and optimization

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data migration errors | High | Run migrations in staging first, create rollback scripts |
| WebSocket compatibility | High | Maintain protocol compatibility, extensive testing |
| Performance regression | Medium | Benchmark before/after, optimize hot paths |
| Team learning curve | Medium | Documentation, pair programming, gradual rollout |
| Third-party integration breaks | Medium | Test Keycloak, Lago, Redis integrations early |
| SpiceDB learning curve | Medium | Start with simple schema, iterate |
| Voice latency issues | High | Test with real hardware, optimize audio pipeline |

---

## Correctness Properties

### Property 1: Theme Validation Completeness
*For any* theme JSON object, validation SHALL verify 26 required CSS variables, reject `url()` values, and validate WCAG AA contrast.
**Validates: Requirements 11.1, 11.3, 11.4, 11.6, 11.10**

### Property 2: Permission Enforcement Consistency
*For any* user action, SpiceDB SHALL return consistent decisions within cache TTL, deny when unavailable, and enforce tenant isolation.
**Validates: Requirements 12.2, 12.4, 12.5, 12.9**

### Property 3: Real-time Event Delivery
*For any* server event, WebSocket SHALL deliver within 100ms, maintain heartbeat, and replay missed events on reconnect.
**Validates: Requirements 17.2, 17.5, 17.6**

### Property 4: Voice Provider Selection Consistency
*For any* provider selection, the system SHALL use correct provider, show appropriate UI, and emit settings.changed event.
**Validates: Requirements 15.2, 15.3, 15.4, 15.10**

### Property 5: Component Render Performance
*For any* Lit component, rendering SHALL complete within 16ms (60fps) and apply theme changes within 50ms.
**Validates: Requirements 18.2, 18.4, 18.10**
