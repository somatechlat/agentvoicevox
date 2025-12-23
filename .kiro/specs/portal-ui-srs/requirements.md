# Portal UI Software Requirements Specification (SRS)

## Document Information

**Version:** 1.0  
**Last Updated:** 2025-12-23  
**Status:** Draft - Ready for Review  
**Project:** AgentVoiceBox Portal Frontend

---

## 1. Introduction

### 1.1 Purpose

This document specifies the complete UI/UX requirements for the AgentVoiceBox Portal Frontend, following the 7-Persona VIBE Coding methodology. It covers all screens, user flows, interactions, and visual specifications.

### 1.2 Scope

The Portal Frontend is a multi-tenant SaaS dashboard providing:
- **Admin Portal** - Platform-wide management for system administrators
- **Customer Portal** - Tenant-specific dashboard for customers
- **Voice Agent Interface** - Real-time voice interaction capabilities
- **AgentSkin Theming** - Customizable visual themes

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| **Tenant** | An organization/customer with isolated data and configuration |
| **Admin** | Platform administrator with system-wide access |
| **Customer** | Tenant user with access to their organization's resources |
| **Session** | A voice interaction session between user and agent |
| **AgentSkin** | Theme system using CSS Custom Properties (26+ variables) |
| **STT** | Speech-to-Text transcription |
| **TTS** | Text-to-Speech synthesis |
| **LLM** | Large Language Model for conversation |


---

## 2. System Overview

### 2.1 Application Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PORTAL FRONTEND                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐             │
│  │   AUTH LAYER    │  │  ADMIN PORTAL   │  │ CUSTOMER PORTAL │             │
│  │                 │  │                 │  │                 │             │
│  │  • Login        │  │  • Dashboard    │  │  • Dashboard    │             │
│  │  • Signup       │  │  • Tenants      │  │  • API Keys     │             │
│  │  • Callback     │  │  • Users        │  │  • Sessions     │             │
│  │  • Logout       │  │  • Billing      │  │  • Billing      │             │
│  └─────────────────┘  │  • Monitoring   │  │  • Settings     │             │
│                       │  • Security     │  │  • Team         │             │
│                       │  • Voice Config │  │  • Usage        │             │
│                       │  • Audit        │  │  • Projects     │             │
│                       └─────────────────┘  └─────────────────┘             │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      SHARED COMPONENTS                               │   │
│  │  • Layout (Header, Sidebar, Main)                                   │   │
│  │  • UI Primitives (Button, Input, Card, Modal, Toast, etc.)          │   │
│  │  • AgentSkin Theme System                                           │   │
│  │  • Voice Components (Controls, Indicator, Visualizer)               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                      STATE MANAGEMENT                                │   │
│  │  • AuthContext (user, token, tenant)                                │   │
│  │  • ThemeContext (active theme, preview)                             │   │
│  │  • VoiceStore (provider, state, config)                             │   │
│  │  • PermissionStore (roles, cache)                                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Screen Inventory

| Category | Screen | Route | Permission |
|----------|--------|-------|------------|
| **Auth** | Login | `/login` | Public |
| **Auth** | Signup | `/signup` | Public |
| **Auth** | Callback | `/auth/callback` | Public |
| **Admin** | Dashboard | `/admin/dashboard` | `admin:view` |
| **Admin** | Tenants | `/admin/tenants-mgmt` | `admin:tenants` |
| **Admin** | Users | `/admin/users-mgmt` | `admin:users` |
| **Admin** | Billing | `/admin/billing` | `admin:billing` |
| **Admin** | Plans | `/admin/plans` | `admin:billing` |
| **Admin** | Monitoring | `/admin/monitoring` | `admin:system` |
| **Admin** | Sessions | `/admin/sessions` | `admin:sessions` |
| **Admin** | Voice Config | `/admin/voice-config` | `admin:voice` |
| **Admin** | Security | `/admin/security` | `admin:security` |
| **Admin** | Audit | `/admin/audit` | `admin:audit` |
| **Customer** | Dashboard | `/dashboard` | `tenant:view` |
| **Customer** | API Keys | `/api-keys` | `tenant:keys` |
| **Customer** | Sessions | `/sessions` | `tenant:sessions` |
| **Customer** | Billing | `/billing` | `tenant:billing` |
| **Customer** | Usage | `/usage` | `tenant:usage` |
| **Customer** | Settings | `/settings` | `tenant:settings` |
| **Customer** | Team | `/team` | `tenant:team` |
| **Customer** | Projects | `/projects` | `tenant:projects` |
| **Voice** | Voice Dashboard | `/dashboard/voice` | `tenant:voice` |
| **Voice** | STT Config | `/dashboard/stt` | `tenant:voice` |
| **Voice** | Wake Words | `/dashboard/wake-words` | `tenant:voice` |
| **Voice** | Voice Cloning | `/dashboard/voice-cloning` | `tenant:voice` |
| **Voice** | Personas | `/dashboard/personas` | `tenant:voice` |
| **Voice** | LLM Config | `/dashboard/llm` | `tenant:voice` |
| **Voice** | Intents | `/dashboard/intents` | `tenant:voice` |
| **Voice** | Skills | `/dashboard/skills` | `tenant:voice` |
| **Voice** | Message Bus | `/dashboard/messagebus` | `tenant:voice` |


---

## 3. Requirements by Persona

---

### 🎯 PERSONA 1: PRODUCT MANAGER — Vision & Features

#### 3.1.1 Product Vision

The AgentVoiceBox Portal transforms voice AI deployment into a **self-service, enterprise-grade platform** where organizations can:
- Deploy and manage voice agents at scale
- Monitor real-time voice sessions
- Customize agent behavior and appearance
- Track usage and billing transparently

#### 3.1.2 Core Value Propositions

1. **Self-Service Deployment** - Launch voice agents without engineering support
2. **Enterprise Scale** - Support millions of concurrent sessions
3. **Full Customization** - AgentSkin themes + voice personas
4. **Transparent Billing** - Real-time usage tracking and cost visibility
5. **Security First** - Multi-tenant isolation, audit trails, RBAC

#### 3.1.3 Feature Categories

**F-AUTH: Authentication & Authorization**
- F-AUTH-01: Keycloak SSO integration
- F-AUTH-02: Multi-tenant user management
- F-AUTH-03: Role-based access control (RBAC)
- F-AUTH-04: API key management with scopes

**F-ADMIN: Platform Administration**
- F-ADMIN-01: System-wide dashboard with KPIs
- F-ADMIN-02: Tenant lifecycle management
- F-ADMIN-03: User management across tenants
- F-ADMIN-04: Billing and plan management
- F-ADMIN-05: System monitoring and health
- F-ADMIN-06: Security policy management
- F-ADMIN-07: Audit log viewer

**F-CUSTOMER: Customer Portal**
- F-CUST-01: Tenant dashboard with metrics
- F-CUST-02: API key generation and rotation
- F-CUST-03: Session history and replay
- F-CUST-04: Usage analytics and reports
- F-CUST-05: Billing and invoices
- F-CUST-06: Team member management
- F-CUST-07: Project organization

**F-VOICE: Voice Agent Configuration**
- F-VOICE-01: Voice provider selection (Local/AgentVoiceBox)
- F-VOICE-02: STT engine configuration
- F-VOICE-03: TTS voice selection and preview
- F-VOICE-04: Wake word management
- F-VOICE-05: Voice cloning interface
- F-VOICE-06: Persona creation and editing
- F-VOICE-07: LLM model selection
- F-VOICE-08: Intent and skill management

**F-THEME: AgentSkin Theming**
- F-THEME-01: Theme gallery with previews
- F-THEME-02: One-click theme switching
- F-THEME-03: Drag-and-drop theme installation
- F-THEME-04: Live theme preview (split-screen)
- F-THEME-05: Theme validation (WCAG AA)
- F-THEME-06: Admin theme management


---

### 🎨 PERSONA 2: UX DESIGNER — User Experience & Flows

#### 3.2.1 Design Principles

1. **Clarity First** - Every action has clear feedback
2. **Progressive Disclosure** - Show complexity only when needed
3. **Consistent Patterns** - Same actions work the same everywhere
4. **Accessible by Default** - WCAG AA compliance minimum
5. **Performance Perception** - Skeleton loaders, optimistic updates

#### 3.2.2 User Flows

##### Flow UF-01: First-Time Admin Login

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FIRST-TIME ADMIN LOGIN                              │
└─────────────────────────────────────────────────────────────────────────────┘

1. Admin navigates to /login
   │
   ▼
2. Clicks "Sign in with SSO"
   │
   ▼
3. Redirected to Keycloak login page
   │
   ▼
4. Enters credentials → Keycloak validates
   │
   ├─── [Invalid] → Error message, retry
   │
   ▼ [Valid]
5. Redirected to /auth/callback with tokens
   │
   ▼
6. System extracts: user_id, tenant_id, roles
   │
   ▼
7. [If admin role] → Redirect to /admin/dashboard
   │
   ▼
8. Admin Dashboard loads with:
   • Platform KPIs (tenants, sessions, revenue)
   • System health indicators
   • Recent activity feed
   • Quick action buttons
```

##### Flow UF-02: Customer Creates API Key

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CREATE API KEY FLOW                                 │
└─────────────────────────────────────────────────────────────────────────────┘

1. Customer navigates to /api-keys
   │
   ▼
2. Sees list of existing keys (masked)
   │
   ▼
3. Clicks "Create New Key" button
   │
   ▼
4. Modal opens with form:
   • Key name (required)
   • Description (optional)
   • Scopes checkboxes (realtime, billing, admin)
   • Expiration dropdown (30d, 90d, 1y, never)
   │
   ▼
5. Fills form → Clicks "Generate"
   │
   ▼
6. System generates key with Argon2id hash
   │
   ▼
7. Modal shows FULL key (one-time display)
   • Copy button with confirmation
   • Warning: "This key won't be shown again"
   │
   ▼
8. User copies key → Clicks "Done"
   │
   ▼
9. Key appears in list (masked: sk_live_****1234)
```

##### Flow UF-03: Voice Session Monitoring

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      VOICE SESSION MONITORING                               │
└─────────────────────────────────────────────────────────────────────────────┘

1. Admin navigates to /admin/sessions
   │
   ▼
2. Sees real-time session list:
   • Session ID, Tenant, Status, Duration
   • Live indicator (green dot) for active
   │
   ▼
3. Clicks on active session row
   │
   ▼
4. Session detail panel slides in:
   │
   ├── [Tab: Overview]
   │   • Session metadata
   │   • Tenant info
   │   • API key used
   │
   ├── [Tab: Transcript]
   │   • Real-time transcript (WebSocket)
   │   • User/Agent turns highlighted
   │
   ├── [Tab: Audio]
   │   • Waveform visualizer
   │   • Playback controls (if recorded)
   │
   └── [Tab: Metrics]
       • Latency graph
       • Token usage
       • Error events
```

##### Flow UF-04: Theme Switching

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         THEME SWITCHING FLOW                                │
└─────────────────────────────────────────────────────────────────────────────┘

1. User opens Settings → Themes tab
   │
   ▼
2. Sees theme gallery grid:
   • Current theme highlighted
   • Preview thumbnails
   • Theme name, author, downloads
   │
   ▼
3. Hovers over "Midnight Dark" theme
   │
   ▼
4. Preview overlay appears (50% opacity)
   │
   ▼
5. Clicks "Preview" button
   │
   ▼
6. Split-screen mode activates:
   • Left: Current theme
   • Right: Preview theme
   │
   ▼
7. User interacts with preview side
   │
   ├─── [Satisfied] → Clicks "Apply"
   │    │
   │    ▼
   │    Theme applies with 300ms transition
   │    Toast: "Midnight Dark activated!"
   │    Persists to localStorage
   │
   └─── [Not satisfied] → Clicks "Cancel"
        │
        ▼
        Returns to original theme
```


---

## 4. Role-Based Access Control (RBAC) Matrix

### 4.1 Role Definitions

| Role | Code | Description | Scope |
|------|------|-------------|-------|
| **System Admin** | `SYSADMIN` | Platform-wide administrator | All tenants |
| **Tenant Admin** | `ADMIN` | Organization administrator | Single tenant |
| **Developer** | `DEVELOPER` | API integration developer | Single tenant |
| **Operator** | `OPERATOR` | Voice session operator | Single tenant |
| **Viewer** | `VIEWER` | Read-only access | Single tenant |
| **Billing Admin** | `BILLING` | Billing and invoices only | Single tenant |

### 4.2 Complete Permission Matrix

#### 4.2.1 Authentication Screens

| Screen | Route | SYSADMIN | ADMIN | DEVELOPER | OPERATOR | VIEWER | BILLING | Public |
|--------|-------|----------|-------|-----------|----------|--------|---------|--------|
| Login | `/login` | - | - | - | - | - | - | ✅ |
| Signup | `/signup` | - | - | - | - | - | - | ✅ |
| OAuth Callback | `/auth/callback` | - | - | - | - | - | - | ✅ |
| Logout | `/logout` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | - |

#### 4.2.2 Admin Portal Screens

| Screen | Route | SYSADMIN | ADMIN | DEVELOPER | OPERATOR | VIEWER | BILLING |
|--------|-------|----------|-------|-----------|----------|--------|---------|
| Admin Dashboard | `/admin/dashboard` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Tenant Management | `/admin/tenants-mgmt` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| User Management | `/admin/users-mgmt` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Platform Billing | `/admin/billing` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Subscription Plans | `/admin/plans` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| System Monitoring | `/admin/monitoring` | ✅ R | ❌ | ❌ | ❌ | ❌ | ❌ |
| All Sessions | `/admin/sessions` | ✅ RD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Voice Config (Global) | `/admin/voice-config` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Security Settings | `/admin/security` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Keycloak Config | `/admin/security/keycloak` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| OPA Policies | `/admin/security/policies` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Vault Secrets | `/admin/security/secrets` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Audit Logs | `/admin/audit` | ✅ R | ❌ | ❌ | ❌ | ❌ | ❌ |
| System Gateway | `/admin/system/gateway` | ✅ CRUD | ❌ | ❌ | ❌ | ❌ | ❌ |
| Infrastructure | `/admin/system/infrastructure` | ✅ R | ❌ | ❌ | ❌ | ❌ | ❌ |
| Observability | `/admin/system/observability` | ✅ R | ❌ | ❌ | ❌ | ❌ | ❌ |
| Workers Status | `/admin/system/workers` | ✅ R | ❌ | ❌ | ❌ | ❌ | ❌ |

**Legend:** C=Create, R=Read, U=Update, D=Delete

#### 4.2.3 Customer Portal Screens

| Screen | Route | SYSADMIN | ADMIN | DEVELOPER | OPERATOR | VIEWER | BILLING |
|--------|-------|----------|-------|-----------|----------|--------|---------|
| Customer Dashboard | `/dashboard` | ✅ R | ✅ R | ✅ R | ✅ R | ✅ R | ❌ |
| API Keys | `/api-keys` | ✅ CRUD | ✅ CRUD | ✅ CRD | ❌ | ❌ | ❌ |
| Sessions | `/sessions` | ✅ RD | ✅ RD | ✅ R | ✅ R | ✅ R | ❌ |
| Billing | `/billing` | ✅ R | ✅ R | ❌ | ❌ | ❌ | ✅ R |
| Usage | `/usage` | ✅ R | ✅ R | ✅ R | ✅ R | ✅ R | ✅ R |
| Settings | `/settings` | ✅ CRUD | ✅ CRUD | ✅ RU | ❌ | ❌ | ❌ |
| Team | `/team` | ✅ CRUD | ✅ CRUD | ❌ | ❌ | ❌ | ❌ |
| Projects | `/projects` | ✅ CRUD | ✅ CRUD | ✅ CRUD | ✅ R | ✅ R | ❌ |

#### 4.2.4 Voice Configuration Screens

| Screen | Route | SYSADMIN | ADMIN | DEVELOPER | OPERATOR | VIEWER | BILLING |
|--------|-------|----------|-------|-----------|----------|--------|---------|
| Voice Dashboard | `/dashboard/voice` | ✅ CRUD | ✅ CRUD | ✅ RU | ✅ R | ✅ R | ❌ |
| STT Config | `/dashboard/stt` | ✅ CRUD | ✅ CRUD | ✅ RU | ❌ | ❌ | ❌ |
| Wake Words | `/dashboard/wake-words` | ✅ CRUD | ✅ CRUD | ✅ CRUD | ❌ | ❌ | ❌ |
| Voice Cloning | `/dashboard/voice-cloning` | ✅ CRUD | ✅ CRUD | ✅ CRUD | ❌ | ❌ | ❌ |
| Personas | `/dashboard/personas` | ✅ CRUD | ✅ CRUD | ✅ CRUD | ✅ R | ✅ R | ❌ |
| LLM Config | `/dashboard/llm` | ✅ CRUD | ✅ CRUD | ✅ RU | ❌ | ❌ | ❌ |
| Intents | `/dashboard/intents` | ✅ CRUD | ✅ CRUD | ✅ CRUD | ✅ R | ✅ R | ❌ |
| Skills | `/dashboard/skills` | ✅ CRUD | ✅ CRUD | ✅ CRUD | ✅ R | ✅ R | ❌ |
| Message Bus | `/dashboard/messagebus` | ✅ R | ✅ R | ✅ R | ✅ R | ❌ | ❌ |

