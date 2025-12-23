# Design Document

## Overview

This document details the technical design for migrating AgentVoiceBox from Flask + React to Django + Django Ninja + Lit 3.x, incorporating the Eye of God UIX architecture and AgentSkin theming system.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Load Balancer (HAProxy)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    │                                      │
                    ▼                                      ▼
┌─────────────────────────────────┐    ┌─────────────────────────────────────┐
│     Lit 3.x Frontend (Vite)     │    │     Django Backend (ASGI)           │
│     Port: 3000                  │    │     Port: 8020                      │
│                                 │    │                                     │
│  ┌───────────────────────────┐  │    │  ┌─────────────────────────────┐   │
│  │  Web Components (EOG-*)   │  │    │  │  Django Ninja API           │   │
│  │  - eog-app (Shell)        │  │    │  │  - /api/v2/admin/*          │   │
│  │  - eog-chat               │  │    │  │  - /api/v2/tenants/*        │   │
│  │  - eog-settings           │  │    │  │  - /api/v2/sessions/*       │   │
│  │  - eog-themes             │  │    │  │  - /api/v2/themes/*         │   │
│  │  - eog-voice              │  │    │  │  - /api/v2/voice/*          │   │
│  └───────────────────────────┘  │    │  └─────────────────────────────┘   │
│                                 │    │                                     │
│  ┌───────────────────────────┐  │    │  ┌─────────────────────────────┐   │
│  │  Stores (Lit Context)     │  │    │  │  Django Channels            │   │
│  │  - AuthStore              │  │    │  │  WebSocket: /ws/v2/*        │   │
│  │  - ModeStore              │  │    │  └─────────────────────────────┘   │
│  │  - ThemeStore             │  │    │                                     │
│  │  - VoiceStore             │  │    │  ┌─────────────────────────────┐   │
│  └───────────────────────────┘  │    │  │  SpiceDB Client             │   │
│                                 │    │  │  Permission checks          │   │
│  ┌───────────────────────────┐  │    │  └─────────────────────────────┘   │
│  │  @vaadin/router           │  │    │                                     │
│  │  Client-side routing      │  │    │                                     │
│  └───────────────────────────┘  │    │                                     │
└─────────────────────────────────┘    └─────────────────────────────────────┘
                                                       │
          ┌────────────────────────────────────────────┼────────────────────┐
          │                                            │                    │
          ▼                                            ▼                    ▼
┌─────────────────┐              ┌─────────────────┐   ┌─────────────────┐  ┌──────────────┐
│   PostgreSQL    │              │     Redis       │   │    SpiceDB      │  │   Keycloak   │
│   Port: 5432    │              │   Port: 6379    │   │  Port: 50051    │  │  Port: 8080  │
└─────────────────┘              └─────────────────┘   └─────────────────┘  └──────────────┘
```

## Component Design

### 1. Django Project Structure

```
ovos-voice-agent/AgentVoiceBoxEngine/backend/
├── manage.py
├── config/
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── apps/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── middleware.py      # Tenant context, auth
│   │   ├── permissions.py     # SpiceDB helpers
│   │   └── exceptions.py      # Custom exceptions
│   ├── tenants/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   ├── api.py             # Django Ninja router
│   │   ├── schemas.py         # Pydantic schemas
│   │   └── services.py
│   ├── projects/
│   ├── api_keys/
│   ├── sessions/
│   ├── billing/
│   ├── voice/                 # Voice configuration
│   │   ├── models.py          # VoiceConfig model
│   │   ├── api.py             # Voice endpoints
│   │   ├── schemas.py         # Voice schemas
│   │   └── providers/         # Local/AgentVoiceBox
│   └── themes/                # AgentSkin themes
│       ├── models.py          # Theme model
│       ├── api.py             # Theme endpoints
│       ├── schemas.py         # Theme schemas
│       └── validators.py      # XSS, contrast validation
├── permissions/               # SpiceDB integration
│   ├── __init__.py
│   ├── client.py              # SpiceDB gRPC client
│   ├── schema.zed             # Permission schema
│   └── decorators.py          # @require_permission
├── realtime/                  # Django Channels
│   ├── __init__.py
│   ├── consumers.py           # WebSocket consumers
│   ├── routing.py             # WS URL routing
│   └── events.py              # Event types
└── requirements/
```


### 2. Django Ninja API Design

```python
# apps/tenants/api.py
from ninja import Router
from ninja.security import HttpBearer
from .schemas import TenantCreate, TenantResponse, TenantUpdate
from .services import TenantService

router = Router(tags=["tenants"])

class KeycloakAuth(HttpBearer):
    def authenticate(self, request, token: str):
        # Validate JWT from Keycloak
        # Extract tenant_id, user_id, roles
        pass

@router.post("/", response=TenantResponse, auth=KeycloakAuth())
def create_tenant(request, payload: TenantCreate):
    return TenantService.create(payload, request.auth)

@router.get("/{tenant_id}", response=TenantResponse, auth=KeycloakAuth())
def get_tenant(request, tenant_id: str):
    return TenantService.get(tenant_id, request.auth)
```

### 3. Django Models Design

```python
# apps/tenants/models.py
from django.db import models
from django.contrib.postgres.fields import ArrayField
import uuid

class Tenant(models.Model):
    class Tier(models.TextChoices):
        FREE = "free", "Free"
        PRO = "pro", "Pro"
        ENTERPRISE = "enterprise", "Enterprise"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        DELETED = "deleted", "Deleted"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    tier = models.CharField(max_length=20, choices=Tier.choices, default=Tier.FREE)
    billing_id = models.CharField(max_length=255, blank=True)  # Lago customer ID
    settings = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tenants"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["tier"]),
        ]
```

### 4. Django Channels WebSocket

```python
# apps/sessions/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class RealtimeConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Validate API key from query params or headers
        token = self.scope["query_string"].decode().split("=")[-1]
        self.tenant_id = await self.validate_token(token)
        if not self.tenant_id:
            await self.close(code=4001)
            return
        
        await self.accept()
        await self.send_json({
            "type": "session.created",
            "session": {"id": str(self.session_id)}
        })

    async def receive_json(self, content):
        event_type = content.get("type")
        if event_type == "conversation.item.create":
            await self.handle_conversation_item(content)
        elif event_type == "response.create":
            await self.handle_response_create(content)

    async def disconnect(self, code):
        # Cleanup session state in Redis
        pass
```


### 5. Lit Frontend Structure

```
ovos-voice-agent/AgentVoiceBoxEngine/frontend/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.ts
│   ├── router.ts
│   ├── styles/
│   │   ├── tokens.css          # AgentSkin CSS custom properties (26+)
│   │   ├── reset.css           # CSS reset
│   │   └── themes/
│   │       ├── default-light.json
│   │       ├── midnight-dark.json
│   │       └── high-contrast.json
│   ├── components/             # Primitive UI components
│   │   ├── eog-button.ts
│   │   ├── eog-card.ts
│   │   ├── eog-input.ts
│   │   ├── eog-select.ts
│   │   ├── eog-toggle.ts
│   │   ├── eog-slider.ts
│   │   ├── eog-modal.ts
│   │   ├── eog-toast.ts
│   │   ├── eog-tabs.ts
│   │   ├── eog-spinner.ts
│   │   ├── eog-badge.ts
│   │   ├── eog-avatar.ts
│   │   ├── eog-icon.ts
│   │   ├── eog-tooltip.ts
│   │   ├── eog-progress.ts
│   │   └── index.ts
│   ├── layout/                 # Layout components
│   │   ├── eog-app.ts          # Root shell
│   │   ├── eog-header.ts       # Top navigation
│   │   ├── eog-sidebar.ts      # Side navigation
│   │   ├── eog-main.ts         # Content area
│   │   ├── eog-panel.ts        # Collapsible section
│   │   └── index.ts
│   ├── views/                  # Page components
│   │   ├── eog-chat.ts         # Chat interface
│   │   ├── eog-memory.ts       # Memory browser
│   │   ├── eog-tools.ts        # Tool catalog
│   │   ├── eog-settings.ts     # Settings panel
│   │   ├── eog-themes.ts       # Theme gallery
│   │   ├── eog-voice.ts        # Voice interface
│   │   ├── eog-cognitive.ts    # Cognitive panel
│   │   ├── eog-admin.ts        # Admin dashboard
│   │   ├── eog-audit.ts        # Audit logs
│   │   └── index.ts
│   ├── voice/                  # Voice components
│   │   ├── eog-voice-controls.ts
│   │   ├── eog-voice-indicator.ts
│   │   ├── eog-voice-overlay.ts
│   │   ├── eog-voice-visualizer.ts
│   │   └── index.ts
│   ├── themes/                 # Theme components
│   │   ├── eog-theme-gallery.ts
│   │   ├── eog-theme-card.ts
│   │   ├── eog-theme-preview.ts
│   │   ├── eog-theme-editor.ts
│   │   └── index.ts
│   ├── stores/                 # State management (Lit Context + Signals)
│   │   ├── auth-store.ts
│   │   ├── mode-store.ts
│   │   ├── theme-store.ts
│   │   ├── voice-store.ts
│   │   ├── perm-store.ts
│   │   ├── settings-store.ts
│   │   ├── chat-store.ts
│   │   └── index.ts
│   ├── services/               # API clients
│   │   ├── api-client.ts       # Base fetch wrapper
│   │   ├── websocket-client.ts # WS connection manager
│   │   ├── auth-service.ts
│   │   ├── voice-service.ts    # Voice provider abstraction
│   │   ├── theme-service.ts
│   │   └── index.ts
│   └── utils/
│       ├── validators.ts
│       ├── formatters.ts
│       └── constants.ts
└── public/
    └── favicon.ico
```

### 6. Lit Component Example

```typescript
// src/components/eog-button.ts
import { LitElement, html, css } from 'lit';
import { customElement, property } from 'lit/decorators.js';

@customElement('eog-button')
export class EogButton extends LitElement {
  static styles = css`
    :host {
      display: inline-block;
    }
    button {
      padding: var(--eog-spacing-sm) var(--eog-spacing-md);
      border-radius: var(--eog-radius-md);
      font-weight: 600;
      font-size: var(--eog-text-base);
      cursor: pointer;
      transition: all 0.2s ease;
      border: 1px solid var(--eog-glass-border);
      font-family: var(--eog-font-sans);
    }
    button.primary {
      background: var(--eog-accent-primary);
      color: white;
      border-color: var(--eog-accent-primary);
    }
    button.primary:hover:not(:disabled) {
      filter: brightness(1.1);
    }
    button.secondary {
      background: var(--eog-glass-surface);
      color: var(--eog-text-main);
    }
    button.danger {
      background: var(--eog-accent-danger);
      color: white;
      border-color: var(--eog-accent-danger);
    }
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    button:focus-visible {
      outline: 2px solid var(--eog-accent-primary);
      outline-offset: 2px;
    }
  `;

  @property({ type: String }) variant: 'primary' | 'secondary' | 'danger' = 'primary';
  @property({ type: Boolean }) disabled = false;
  @property({ type: Boolean }) loading = false;
  @property({ type: String }) ariaLabel = '';

  render() {
    return html`
      <button
        class=${this.variant}
        ?disabled=${this.disabled || this.loading}
        aria-label=${this.ariaLabel || nothing}
        aria-disabled=${this.disabled}
        @click=${this._handleClick}
      >
        ${this.loading ? html`<eog-spinner size="sm"></eog-spinner>` : html`<slot></slot>`}
      </button>
    `;
  }

  private _handleClick(e: Event) {
    if (!this.disabled && !this.loading) {
      this.dispatchEvent(new CustomEvent('eog-click', { bubbles: true, composed: true }));
    }
  }
}
```

### 7. Store Implementation (Lit Context + Signals)

```typescript
// src/stores/voice-store.ts
import { createContext } from '@lit/context';
import { signal, computed } from '@lit-labs/signals';

export type VoiceProvider = 'disabled' | 'local' | 'agentvoicebox';
export type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking' | 'error';

export interface VoiceConfig {
  provider: VoiceProvider;
  local: {
    stt_engine: 'whisper' | 'faster-whisper';
    stt_model_size: 'tiny' | 'base' | 'small' | 'medium' | 'large';
    tts_engine: 'kokoro' | 'browser';
    tts_voice: string;
    tts_speed: number;
    language: string;
  };
  agentvoicebox: {
    base_url: string;
    ws_url: string;
    api_token: string;
    model: string;
    voice: string;
    turn_detection: boolean;
  };
}

export interface VoiceStoreState {
  enabled: boolean;
  provider: VoiceProvider;
  state: VoiceState;
  config: VoiceConfig;
  transcript: string;
  error: string | null;
}

export const voiceContext = createContext<VoiceStoreState>('voice-state');

class VoiceStore {
  private _enabled = signal(false);
  private _provider = signal<VoiceProvider>('disabled');
  private _state = signal<VoiceState>('idle');
  private _transcript = signal('');
  private _error = signal<string | null>(null);

  readonly isActive = computed(() => 
    this._enabled.get() && this._state.get() !== 'idle' && this._state.get() !== 'error'
  );

  readonly canUseSpeechOnSpeech = computed(() => 
    this._provider.get() === 'agentvoicebox'
  );

  setProvider(provider: VoiceProvider): void {
    this._provider.set(provider);
    this._enabled.set(provider !== 'disabled');
  }

  setState(state: VoiceState): void {
    this._state.set(state);
  }

  setTranscript(text: string): void {
    this._transcript.set(text);
  }

  setError(error: string | null): void {
    this._error.set(error);
    if (error) this._state.set('error');
  }
}

export const voiceStore = new VoiceStore();
```

### 8. Theme Store (AgentSkin)

```typescript
// src/stores/theme-store.ts
import { createContext } from '@lit/context';
import { signal } from '@lit-labs/signals';

export interface Theme {
  id: string;
  name: string;
  version: string;
  author: string;
  description?: string;
  variables: Record<string, string>;
}

const REQUIRED_VARIABLES = [
  'bg-void', 'glass-surface', 'glass-border', 'text-main', 'text-dim',
  'accent-primary', 'accent-secondary', 'accent-success', 'accent-warning', 'accent-danger',
  'shadow-soft', 'radius-sm', 'radius-md', 'radius-lg', 'radius-full',
  'spacing-xs', 'spacing-sm', 'spacing-md', 'spacing-lg', 'spacing-xl',
  'font-sans', 'font-mono', 'text-xs', 'text-sm', 'text-base', 'text-lg'
];

class ThemeStore {
  private _active = signal<Theme | null>(null);
  private _list = signal<Theme[]>([]);
  private _preview = signal<Theme | null>(null);
  private _loading = signal(false);

  validateTheme(theme: Theme): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Check required variables
    for (const v of REQUIRED_VARIABLES) {
      if (!(v in theme.variables)) {
        errors.push(`Missing required variable: ${v}`);
      }
    }
    
    // Check for url() (XSS prevention)
    for (const [key, value] of Object.entries(theme.variables)) {
      if (typeof value === 'string' && value.includes('url(')) {
        errors.push(`Security violation: url() not allowed in ${key}`);
      }
    }
    
    return { valid: errors.length === 0, errors };
  }

  applyTheme(theme: Theme): void {
    const validation = this.validateTheme(theme);
    if (!validation.valid) {
      throw new Error(validation.errors.join(', '));
    }
    
    const root = document.documentElement;
    for (const [key, value] of Object.entries(theme.variables)) {
      root.style.setProperty(`--eog-${key}`, value);
    }
    
    this._active.set(theme);
    localStorage.setItem('eog-theme', JSON.stringify(theme));
  }

  previewTheme(theme: Theme | null): void {
    this._preview.set(theme);
    if (theme) {
      const root = document.documentElement;
      for (const [key, value] of Object.entries(theme.variables)) {
        root.style.setProperty(`--eog-${key}`, value);
      }
    } else if (this._active.get()) {
      this.applyTheme(this._active.get()!);
    }
  }
}

export const themeStore = new ThemeStore();
```


### 7. Lit Page Component Example

```typescript
// src/pages/admin/admin-dashboard.ts
import { LitElement, html, css } from 'lit';
import { customElement, state } from 'lit/decorators.js';
import { consume } from '@lit/context';
import { authContext, AuthState } from '../../stores/auth-store';
import { ApiClient } from '../../services/api-client';
import '../../components/ui/avb-card';
import '../../components/charts/avb-usage-chart';

interface DashboardMetrics {
  totalTenants: number;
  activeSessions: number;
  apiRequests: number;
  revenue: number;
}

@customElement('admin-dashboard')
export class AdminDashboard extends LitElement {
  static styles = css`
    :host {
      display: block;
      padding: var(--spacing-6);
    }
    .metrics-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: var(--spacing-4);
      margin-bottom: var(--spacing-6);
    }
    h1 {
      margin-bottom: var(--spacing-6);
      font-size: var(--text-2xl);
    }
  `;

  @consume({ context: authContext })
  @state()
  auth?: AuthState;

  @state() metrics?: DashboardMetrics;
  @state() loading = true;
  @state() error?: string;

  async connectedCallback() {
    super.connectedCallback();
    await this.loadMetrics();
  }

  private async loadMetrics() {
    try {
      this.metrics = await ApiClient.get<DashboardMetrics>('/api/v1/admin/metrics');
    } catch (e) {
      this.error = 'Failed to load metrics';
    } finally {
      this.loading = false;
    }
  }

  render() {
    if (this.loading) {
      return html`<div>Loading...</div>`;
    }
    if (this.error) {
      return html`<div class="error">${this.error}</div>`;
    }
    return html`
      <h1>Admin Dashboard</h1>
      <div class="metrics-grid">
        <avb-card title="Total Tenants" value=${this.metrics?.totalTenants}></avb-card>
        <avb-card title="Active Sessions" value=${this.metrics?.activeSessions}></avb-card>
        <avb-card title="API Requests" value=${this.metrics?.apiRequests}></avb-card>
        <avb-card title="Revenue" value=${this.metrics?.revenue} prefix="$"></avb-card>
      </div>
      <avb-usage-chart></avb-usage-chart>
    `;
  }
}
```

### 9. Router Configuration

```typescript
// src/router.ts
import { Router } from '@vaadin/router';

const outlet = document.getElementById('outlet');
const router = new Router(outlet);

router.setRoutes([
  { path: '/', redirect: '/admin/dashboard' },
  { path: '/login', component: 'eog-login', action: async () => {
    await import('./views/eog-login');
  }},
  
  // Admin routes (tenant->administrate)
  { path: '/admin', children: [
    { path: '/', redirect: '/admin/dashboard' },
    { path: '/dashboard', component: 'eog-admin', action: async () => {
      await import('./views/eog-admin');
    }},
    { path: '/tenants', component: 'eog-admin-tenants', action: async () => {
      await import('./views/eog-admin-tenants');
    }},
    { path: '/monitoring', component: 'eog-admin-monitoring', action: async () => {
      await import('./views/eog-admin-monitoring');
    }},
  ]},
  
  // Main app routes
  { path: '/chat', component: 'eog-chat', action: async () => {
    await import('./views/eog-chat');
  }},
  { path: '/chat/:sessionId', component: 'eog-chat', action: async () => {
    await import('./views/eog-chat');
  }},
  { path: '/memory', component: 'eog-memory', action: async () => {
    await import('./views/eog-memory');
  }},
  { path: '/tools', component: 'eog-tools', action: async () => {
    await import('./views/eog-tools');
  }},
  { path: '/settings', component: 'eog-settings', action: async () => {
    await import('./views/eog-settings');
  }},
  { path: '/settings/:tab', component: 'eog-settings', action: async () => {
    await import('./views/eog-settings');
  }},
  { path: '/themes', component: 'eog-themes', action: async () => {
    await import('./views/eog-themes');
  }},
  { path: '/voice', component: 'eog-voice', action: async () => {
    await import('./views/eog-voice');
  }},
  { path: '/cognitive', component: 'eog-cognitive', action: async () => {
    await import('./views/eog-cognitive');
  }},
  { path: '/audit', component: 'eog-audit', action: async () => {
    await import('./views/eog-audit');
  }},
  
  // Dashboard routes (tenant users)
  { path: '/dashboard', children: [
    { path: '/', component: 'tenant-dashboard', action: async () => {
      await import('./views/tenant-dashboard');
    }},
    { path: '/sessions', component: 'tenant-sessions', action: async () => {
      await import('./views/tenant-sessions');
    }},
    { path: '/api-keys', component: 'tenant-api-keys', action: async () => {
      await import('./views/tenant-api-keys');
    }},
  ]},
]);

export { router };
```

### 10. SpiceDB Permission Schema

```zed
// permissions/schema.zed

definition user {}

definition tenant {
    relation sysadmin: user
    relation admin: user
    relation developer: user
    relation trainer: user
    relation member: user
    relation viewer: user
    
    // Computed permissions
    permission manage = sysadmin
    permission administrate = sysadmin + admin
    permission develop = sysadmin + admin + developer
    permission train = sysadmin + admin + trainer
    permission use = sysadmin + admin + developer + trainer + member
    permission view = sysadmin + admin + developer + trainer + member + viewer
}

definition agent_mode {
    relation tenant: tenant
    relation allowed_role: tenant#admin | tenant#developer | tenant#trainer | tenant#member | tenant#viewer
    
    permission activate = allowed_role
}

definition theme {
    relation tenant: tenant
    relation owner: user
    
    permission view = tenant->view
    permission apply = tenant->use
    permission edit = owner + tenant->administrate
    permission delete = tenant->administrate
}

definition voice_config {
    relation tenant: tenant
    
    permission view = tenant->view
    permission edit = tenant->administrate
    permission use = tenant->use
}
```

### 11. Voice Service Implementation

```typescript
// src/services/voice-service.ts
import { voiceStore, VoiceProvider } from '../stores/voice-store';
import { wsClient } from './websocket-client';

export class VoiceService {
  private mediaStream: MediaStream | null = null;
  private audioContext: AudioContext | null = null;
  private agentVoiceBoxWs: WebSocket | null = null;

  async initialize(provider: VoiceProvider): Promise<void> {
    if (provider === 'disabled') return;

    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
    });

    this.audioContext = new AudioContext({ sampleRate: 24000 });

    if (provider === 'agentvoicebox') {
      await this.connectAgentVoiceBox();
    }

    voiceStore.setState('idle');
  }

  private async connectAgentVoiceBox(): Promise<void> {
    const config = voiceStore.state.config.agentvoicebox;
    if (!config.ws_url) throw new Error('AgentVoiceBox WebSocket URL not configured');

    return new Promise((resolve, reject) => {
      this.agentVoiceBoxWs = new WebSocket(config.ws_url);

      this.agentVoiceBoxWs.onopen = () => {
        this.agentVoiceBoxWs!.send(JSON.stringify({
          type: 'session.update',
          session: {
            voice: config.voice,
            model: config.model,
            turn_detection: config.turn_detection ? { type: 'server_vad' } : null,
            input_audio_format: 'pcm16',
            output_audio_format: 'pcm16',
          },
        }));
        resolve();
      };

      this.agentVoiceBoxWs.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.handleAgentVoiceBoxEvent(data);
      };

      this.agentVoiceBoxWs.onerror = (error) => {
        voiceStore.setError('AgentVoiceBox connection failed');
        reject(error);
      };
    });
  }

  private handleAgentVoiceBoxEvent(event: any): void {
    switch (event.type) {
      case 'input_audio_buffer.speech_started':
        voiceStore.setState('listening');
        wsClient.send('voice.speech_started', {});
        break;
      case 'input_audio_buffer.speech_stopped':
        voiceStore.setState('processing');
        wsClient.send('voice.speech_stopped', {});
        break;
      case 'conversation.item.created':
        if (event.item?.content?.[0]?.transcript) {
          voiceStore.setTranscript(event.item.content[0].transcript);
          wsClient.send('voice.transcription', { text: event.item.content[0].transcript });
        }
        break;
      case 'response.audio.delta':
        voiceStore.setState('speaking');
        wsClient.send('voice.audio_delta', { delta: event.delta });
        break;
      case 'response.done':
        voiceStore.setState('idle');
        wsClient.send('voice.response_done', {});
        break;
      case 'error':
        voiceStore.setError(event.error?.message || 'Unknown error');
        break;
    }
  }

  async testConnection(): Promise<boolean> {
    const config = voiceStore.state.config.agentvoicebox;
    if (!config.base_url) return false;
    try {
      const response = await fetch(`${config.base_url}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  dispose(): void {
    this.agentVoiceBoxWs?.close();
    this.audioContext?.close();
    this.mediaStream?.getTracks().forEach(track => track.stop());
  }
}

export const voiceService = new VoiceService();
```

### 12. WebSocket Event Types

```typescript
// src/services/websocket-client.ts

export type WSEventType = 
  | 'mode.changed'
  | 'settings.changed'
  | 'theme.changed'
  | 'voice.started'
  | 'voice.speech_started'
  | 'voice.speech_stopped'
  | 'voice.transcription'
  | 'voice.response_started'
  | 'voice.audio_delta'
  | 'voice.response_done'
  | 'voice.error'
  | 'assistant.started'
  | 'assistant.delta'
  | 'assistant.final'
  | 'system.keepalive';

export interface WSEvent<T = unknown> {
  type: WSEventType;
  data: T;
  timestamp: number;
}
```
