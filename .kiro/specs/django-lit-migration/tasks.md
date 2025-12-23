# Tasks

## Phase 1: Blog Removal

### Task 1.1: Remove Blog Source Files
- [ ] Delete `src/` directory (Next.js blog app)
- [ ] Delete `_posts/` directory (markdown blog posts)
- [ ] Delete `public/` directory (blog static assets)

### Task 1.2: Remove Blog Configuration Files
- [ ] Delete `package.json` (root)
- [ ] Delete `package-lock.json` (root)
- [ ] Delete `next.config.js`
- [ ] Delete `tailwind.config.ts`
- [ ] Delete `postcss.config.js`
- [ ] Delete `tsconfig.json` (root)

### Task 1.3: Update Repository Configuration
- [ ] Update `.gitignore` to remove blog-specific entries
- [ ] Update `.dockerignore` to remove blog-specific entries
- [ ] Update `README.md` to reflect new structure

### Task 1.4: Preserve Chat WebSocket Test
- [ ] Copy chat WebSocket test functionality to portal-frontend
- [ ] Create `portal-frontend/src/app/dev/websocket-test/page.tsx`

---

## Phase 2: Django Backend Setup

### Task 2.1: Initialize Django Project
- [ ] Create `backend/` directory structure
- [ ] Initialize Django project with `django-admin startproject config .`
- [ ] Configure settings split (base, development, production)
- [ ] Set up `manage.py` with environment-aware settings

### Task 2.2: Configure Django Dependencies
- [ ] Create `requirements/base.txt` with core dependencies
- [ ] Create `requirements/development.txt` with dev tools
- [ ] Create `requirements/production.txt` with prod optimizations
- [ ] Install Django, Django Ninja, Channels, psycopg, pydantic, authzed

### Task 2.3: Configure Database Connection
- [ ] Set up PostgreSQL connection in settings
- [ ] Configure connection pooling
- [ ] Set up Redis cache backend
- [ ] Configure Django Channels with Redis layer

### Task 2.4: Create Django Apps
- [ ] Create `apps/core/` for shared utilities
- [ ] Create `apps/tenants/` for tenant management
- [ ] Create `apps/projects/` for project management
- [ ] Create `apps/api_keys/` for API key management
- [ ] Create `apps/sessions/` for voice sessions
- [ ] Create `apps/billing/` for Lago integration
- [ ] Create `apps/voice/` for voice configuration
- [ ] Create `apps/themes/` for AgentSkin themes

### Task 2.5: Configure Django Ninja API
- [ ] Set up main API router in `config/api.py`
- [ ] Configure OpenAPI documentation at `/api/v2/docs`
- [ ] Set up authentication middleware for Keycloak JWT
- [ ] Configure CORS for frontend access

### Task 2.6: Configure SpiceDB Integration
- [ ] Install authzed Python client
- [ ] Create `permissions/client.py` with SpiceDB gRPC client
- [ ] Create `permissions/schema.zed` with permission schema
- [ ] Create `permissions/decorators.py` with @require_permission
- [ ] Configure SpiceDB connection in settings

---

## Phase 3: Model Migration

### Task 3.1: Migrate Tenant Model
- [ ] Create `apps/tenants/models.py` with Tenant model
- [ ] Add tier, status, billing_id fields
- [ ] Add settings JSONField
- [ ] Create initial migration

### Task 3.2: Migrate Project Model
- [ ] Create `apps/projects/models.py` with Project model
- [ ] Add tenant foreign key
- [ ] Add environment field (production/staging/development)
- [ ] Create migration

### Task 3.3: Migrate APIKey Model
- [ ] Create `apps/api_keys/models.py` with APIKey model
- [ ] Add key_hash field (Argon2id)
- [ ] Add scopes ArrayField
- [ ] Add rate_limit_tier field
- [ ] Create migration

### Task 3.4: Migrate Session Model
- [ ] Create `apps/sessions/models.py` with Session model
- [ ] Add ConversationItem model
- [ ] Add tenant partitioning support
- [ ] Create migration

### Task 3.5: Migrate UsageRecord Model
- [ ] Create `apps/billing/models.py` with UsageRecord model
- [ ] Add dimension, quantity fields
- [ ] Add TimescaleDB hypertable support (optional)
- [ ] Create migration

### Task 3.6: Create Theme Model (AgentSkin)
- [ ] Create `apps/themes/models.py` with Theme model
- [ ] Add name, version, author, description fields
- [ ] Add variables JSONField (26+ CSS properties)
- [ ] Add is_default, is_public, downloads, rating fields
- [ ] Add tenant foreign key and owner foreign key
- [ ] Create migration

### Task 3.7: Create VoiceConfig Model
- [ ] Create `apps/voice/models.py` with VoiceConfig model
- [ ] Add provider field (disabled, local, agentvoicebox)
- [ ] Add local voice settings (stt_engine, stt_model_size, tts_engine, etc.)
- [ ] Add agentvoicebox settings (url, ws_url, token, model, voice)
- [ ] Add audio settings (input_device, output_device, sample_rate)
- [ ] Create migration

---

## Phase 4: API Migration

### Task 4.1: Implement Tenant API
- [ ] Create `apps/tenants/schemas.py` with Pydantic schemas
- [ ] Create `apps/tenants/api.py` with Django Ninja router
- [ ] Implement CRUD endpoints
- [ ] Add tenant suspension/reactivation

### Task 4.2: Implement Project API
- [ ] Create `apps/projects/schemas.py`
- [ ] Create `apps/projects/api.py`
- [ ] Implement CRUD endpoints
- [ ] Add project-tenant association

### Task 4.3: Implement API Key API
- [ ] Create `apps/api_keys/schemas.py`
- [ ] Create `apps/api_keys/api.py`
- [ ] Implement key generation with Argon2id hashing
- [ ] Implement key rotation with grace period
- [ ] Implement key revocation

### Task 4.4: Implement Session API
- [ ] Create `apps/sessions/schemas.py`
- [ ] Create `apps/sessions/api.py`
- [ ] Implement session listing with filters
- [ ] Implement session detail view
- [ ] Implement session termination

### Task 4.5: Implement Billing API
- [ ] Create `apps/billing/schemas.py`
- [ ] Create `apps/billing/api.py`
- [ ] Implement usage query endpoints
- [ ] Implement Lago webhook handlers

### Task 4.6: Implement Admin Metrics API
- [ ] Create admin dashboard metrics endpoint
- [ ] Aggregate tenant counts, session counts
- [ ] Query system health status
- [ ] Return revenue metrics from Lago

### Task 4.7: Implement Theme API (AgentSkin)
- [ ] Create `apps/themes/schemas.py` with Theme schemas
- [ ] Create `apps/themes/api.py` with Django Ninja router
- [ ] Implement GET /api/v2/themes (list themes)
- [ ] Implement GET /api/v2/themes/{id} (get theme)
- [ ] Implement POST /api/v2/themes (upload theme, admin only)
- [ ] Implement DELETE /api/v2/themes/{id} (delete theme, admin only)
- [ ] Create `apps/themes/validators.py` with XSS and contrast validation

### Task 4.8: Implement Voice API
- [ ] Create `apps/voice/schemas.py` with VoiceConfig schemas
- [ ] Create `apps/voice/api.py` with Django Ninja router
- [ ] Implement GET /api/v2/voice/config (get voice config)
- [ ] Implement PUT /api/v2/voice/config (update voice config)
- [ ] Implement POST /api/v2/voice/test (test AgentVoiceBox connection)

---

## Phase 5: WebSocket Migration

### Task 5.1: Configure Django Channels
- [ ] Set up ASGI application in `config/asgi.py`
- [ ] Configure channel layers with Redis
- [ ] Set up routing for WebSocket consumers

### Task 5.2: Implement Event Consumer
- [ ] Create `realtime/consumers.py` with EventConsumer
- [ ] Implement connection authentication
- [ ] Implement mode.changed event handling
- [ ] Implement settings.changed event handling
- [ ] Implement theme.changed event handling
- [ ] Implement voice.* event handling
- [ ] Implement heartbeat (system.keepalive)

### Task 5.3: Implement Realtime Consumer
- [ ] Create `apps/sessions/consumers.py`
- [ ] Implement connection authentication
- [ ] Implement session.created event
- [ ] Implement conversation.item.create handler
- [ ] Implement response.create handler
- [ ] Implement disconnect cleanup

### Task 5.4: Integrate with Workers
- [ ] Set up NATS/Redis pub-sub for worker communication
- [ ] Implement STT request publishing
- [ ] Implement TTS request publishing
- [ ] Implement LLM request publishing
- [ ] Handle worker responses

---

## Phase 6: Lit Frontend Setup

### Task 6.1: Initialize Lit Project
- [ ] Create `frontend/` directory
- [ ] Initialize npm project with `package.json`
- [ ] Configure TypeScript with `tsconfig.json`
- [ ] Configure Vite with `vite.config.ts`
- [ ] Create `index.html` entry point

### Task 6.2: Set Up Project Structure
- [ ] Create `src/main.ts` entry point
- [ ] Create `src/styles/tokens.css` with 26+ AgentSkin CSS variables
- [ ] Create `src/styles/reset.css` base styles
- [ ] Create default theme JSON files (default-light, midnight-dark, high-contrast)
- [ ] Set up folder structure (components, layout, views, stores, services)

### Task 6.3: Configure Router
- [ ] Install `@vaadin/router`
- [ ] Create `src/router.ts` with route definitions
- [ ] Set up lazy loading for page components
- [ ] Configure route guards for authentication and permissions

---

## Phase 7: Lit Primitive Components

### Task 7.1: Create Core UI Components
- [ ] Create `eog-button` component (primary, secondary, danger variants)
- [ ] Create `eog-input` component (text, password, email types)
- [ ] Create `eog-select` component (dropdown selection)
- [ ] Create `eog-toggle` component (boolean switch)
- [ ] Create `eog-slider` component (range input)
- [ ] Create `eog-spinner` component (loading indicator)

### Task 7.2: Create Feedback Components
- [ ] Create `eog-modal` component (dialog overlay)
- [ ] Create `eog-toast` component (notification popup)
- [ ] Create `eog-tooltip` component (hover information)
- [ ] Create `eog-progress` component (progress bar)

### Task 7.3: Create Display Components
- [ ] Create `eog-card` component (content container)
- [ ] Create `eog-tabs` component (tab navigation)
- [ ] Create `eog-badge` component (status indicator)
- [ ] Create `eog-avatar` component (user/agent image)
- [ ] Create `eog-icon` component (SVG icon wrapper)

---

## Phase 8: Lit Layout Components

### Task 8.1: Create Shell Components
- [ ] Create `eog-app` component (root application shell)
- [ ] Create `eog-header` component (top navigation bar with mode selector)
- [ ] Create `eog-sidebar` component (side navigation)
- [ ] Create `eog-main` component (content area with router outlet)

### Task 8.2: Create Layout Utilities
- [ ] Create `eog-panel` component (collapsible section)
- [ ] Create `eog-split` component (resizable split view)
- [ ] Create `eog-grid` component (CSS Grid wrapper)
- [ ] Create `eog-stack` component (Flex stack layout)

---

## Phase 9: Lit State Management

### Task 9.1: Implement Core Stores
- [ ] Create `src/stores/auth-store.ts` with Lit Context + Signals
- [ ] Create `src/stores/mode-store.ts` for agent mode state
- [ ] Create `src/stores/perm-store.ts` for permission cache
- [ ] Create `src/stores/settings-store.ts` for settings state

### Task 9.2: Implement Feature Stores
- [ ] Create `src/stores/theme-store.ts` with AgentSkin validation
- [ ] Create `src/stores/voice-store.ts` with provider state
- [ ] Create `src/stores/chat-store.ts` for chat messages

---

## Phase 10: Lit Services

### Task 10.1: Implement API Client
- [ ] Create `src/services/api-client.ts` with typed fetch wrapper
- [ ] Add automatic token injection
- [ ] Add token refresh on 401
- [ ] Add error handling

### Task 10.2: Implement WebSocket Client
- [ ] Create `src/services/websocket-client.ts`
- [ ] Implement connection management with reconnection
- [ ] Implement event subscription/dispatch
- [ ] Implement heartbeat (20s interval)

### Task 10.3: Implement Auth Service
- [ ] Create `src/services/auth-service.ts`
- [ ] Implement Keycloak redirect flow
- [ ] Implement token storage
- [ ] Implement logout

### Task 10.4: Implement Voice Service
- [ ] Create `src/services/voice-service.ts`
- [ ] Implement Local Voice provider (Whisper/Kokoro)
- [ ] Implement AgentVoiceBox provider (WebSocket)
- [ ] Implement audio capture and playback
- [ ] Implement test connection

### Task 10.5: Implement Theme Service
- [ ] Create `src/services/theme-service.ts`
- [ ] Implement theme loading and validation
- [ ] Implement theme application (CSS variables)
- [ ] Implement theme persistence (localStorage)

---

## Phase 11: Lit View Components

### Task 11.1: Implement Admin Views
- [ ] Create `eog-admin` component (admin dashboard)
- [ ] Create `eog-admin-tenants` component (tenant management)
- [ ] Create `eog-admin-monitoring` component (system health)

### Task 11.2: Implement Main Views
- [ ] Create `eog-chat` component (chat interface)
- [ ] Create `eog-memory` component (memory browser)
- [ ] Create `eog-tools` component (tool catalog)
- [ ] Create `eog-settings` component (settings panel with tabs)
- [ ] Create `eog-cognitive` component (cognitive panel)
- [ ] Create `eog-audit` component (audit log viewer)

### Task 11.3: Implement Theme Views
- [ ] Create `eog-themes` component (theme gallery)
- [ ] Create `eog-theme-gallery` component (theme grid)
- [ ] Create `eog-theme-card` component (theme preview card)
- [ ] Create `eog-theme-preview` component (split comparison)
- [ ] Create `eog-theme-editor` component (customize theme)

### Task 11.4: Implement Voice Views
- [ ] Create `eog-voice` component (voice interface)
- [ ] Create `eog-voice-controls` component (record/stop/mute)
- [ ] Create `eog-voice-indicator` component (state and level)
- [ ] Create `eog-voice-overlay` component (floating UI)
- [ ] Create `eog-voice-visualizer` component (audio waveform)

### Task 11.5: Implement Dashboard Views
- [ ] Create `tenant-dashboard` component (tenant overview)
- [ ] Create `tenant-sessions` component (session list)
- [ ] Create `tenant-api-keys` component (API key management)

---

## Phase 12: Integration and Testing

### Task 12.1: Backend Testing
- [ ] Write unit tests for models
- [ ] Write unit tests for API endpoints
- [ ] Write integration tests for WebSocket
- [ ] Write property tests for theme validation (Hypothesis)
- [ ] Write property tests for permission enforcement
- [ ] Configure pytest with Django

### Task 12.2: Frontend Testing
- [ ] Configure web-test-runner
- [ ] Write unit tests for primitive components
- [ ] Write unit tests for stores
- [ ] Write property tests for theme validation (fast-check)
- [ ] Write property tests for component render performance
- [ ] Write E2E tests with Playwright

### Task 12.3: Docker Integration
- [ ] Create Dockerfile for Django backend
- [ ] Create Dockerfile for Lit frontend
- [ ] Update docker-compose.yml with SpiceDB service
- [ ] Configure Uvicorn for production
- [ ] Set up health checks

---

## Phase 13: Cleanup and Documentation

### Task 13.1: Remove Old Code
- [ ] Remove Flask `app/` directory
- [ ] Remove React `portal-frontend/` directory
- [ ] Remove Alembic migrations (replaced by Django migrations)
- [ ] Update imports and references

### Task 13.2: Update Documentation
- [ ] Update README.md with new architecture
- [ ] Update steering files (tech.md, structure.md, product.md)
- [ ] Create migration guide for developers
- [ ] Update API documentation

### Task 13.3: Final Verification
- [ ] Run full test suite
- [ ] Verify all endpoints work
- [ ] Verify WebSocket functionality
- [ ] Verify Keycloak integration
- [ ] Verify Lago integration
- [ ] Verify SpiceDB permissions
- [ ] Verify AgentSkin theming
- [ ] Verify voice providers (Local and AgentVoiceBox)
- [ ] Performance benchmarking
- [ ] Accessibility audit (WCAG 2.1 AA)
