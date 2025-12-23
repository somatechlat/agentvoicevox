o yo u# Software Requirements Specification (SRS)

## AgentVoiceBox Portal Frontend

**Document Identifier:** AVB-SRS-UI-001  
**Version:** 1.0.0  
**Date:** 2025-12-23  
**Status:** Draft  
**Classification:** Internal  

**Prepared by:** Engineering Team  
**Approved by:** [Pending Review]  

---

## Document Control

### Revision History

| Version | Date | Author | Description |
|---------|------|--------|-------------|
| 1.0.0 | 2025-12-23 | Engineering | Initial draft |

### Document Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Technical Lead | | | |
| QA Lead | | | |
| Security Officer | | | |

### Referenced Documents

| Document ID | Title | Version |
|-------------|-------|---------|
| AVB-ARCH-001 | System Architecture Document | 1.0 |
| AVB-SEC-001 | Security Requirements Specification | 1.0 |
| AVB-API-001 | API Specification (OpenAPI) | 1.0 |
| ISO/IEC/IEEE 29148:2018 | Requirements Engineering | 2018 |
| WCAG 2.1 | Web Content Accessibility Guidelines | 2.1 |

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Overall Description](#2-overall-description)
3. [Specific Requirements](#3-specific-requirements)
4. [System Features](#4-system-features)
5. [External Interface Requirements](#5-external-interface-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [Data Requirements](#7-data-requirements)
8. [Appendices](#8-appendices)

---

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) document provides a complete description of all functional and non-functional requirements for the AgentVoiceBox Portal Frontend system. This document is intended for:

- **Development Team**: To implement the system according to specifications
- **QA Team**: To develop test cases and validation criteria
- **Project Management**: To track progress and scope
- **Stakeholders**: To review and approve requirements

### 1.2 Scope

#### 1.2.1 Product Name
AgentVoiceBox Portal Frontend

#### 1.2.2 Product Description
A multi-tenant SaaS web application providing:
- Platform administration for system operators
- Customer portal for tenant organizations
- Voice agent configuration and monitoring
- Real-time session management
- Billing and usage tracking
- Customizable theming system

#### 1.2.3 Product Boundaries

**In Scope:**
- Web-based user interface (responsive)
- Authentication via Keycloak with Google OAuth
- Admin portal for platform management
- Customer portal for tenant management
- Voice configuration interfaces
- Real-time WebSocket communication
- AgentSkin theming system

**Out of Scope:**
- Mobile native applications
- Backend API implementation (separate document)
- Voice processing workers
- Billing system (Lago) implementation

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| **API** | Application Programming Interface |
| **CRUD** | Create, Read, Update, Delete operations |
| **JWT** | JSON Web Token |
| **LLM** | Large Language Model |
| **OIDC** | OpenID Connect |
| **RBAC** | Role-Based Access Control |
| **SaaS** | Software as a Service |
| **SSO** | Single Sign-On |
| **STT** | Speech-to-Text |
| **TTS** | Text-to-Speech |
| **UI** | User Interface |
| **UX** | User Experience |
| **WCAG** | Web Content Accessibility Guidelines |
| **WebSocket** | Full-duplex communication protocol |

### 1.4 References

1. ISO/IEC/IEEE 29148:2018 - Systems and software engineering — Requirements engineering
2. ISO/IEC 25010:2011 - Systems and software Quality Requirements and Evaluation (SQuaRE)
3. WCAG 2.1 - Web Content Accessibility Guidelines
4. OAuth 2.0 Authorization Framework (RFC 6749)
5. OpenID Connect Core 1.0

### 1.5 Overview

This document is organized according to ISO/IEC/IEEE 29148:2018 structure:
- **Section 2** provides system context and constraints
- **Section 3** details specific functional requirements
- **Section 4** describes system features with use cases
- **Section 5** specifies external interfaces
- **Section 6** defines non-functional requirements
- **Section 7** covers data requirements
- **Section 8** contains appendices with supplementary information

---

## 2. Overall Description

### 2.1 Product Perspective

#### 2.1.1 System Context

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            EXTERNAL SYSTEMS                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   Keycloak   │  │    Lago      │  │   SpiceDB    │  │  PostgreSQL  │   │
│  │   (Auth)     │  │  (Billing)   │  │ (Permissions)│  │  (Database)  │   │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │
│         │                 │                 │                 │           │
│         └─────────────────┴────────┬────────┴─────────────────┘           │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                     AGENTVOICEBOX BACKEND API                        │  │
│  │                     (Django + Django Ninja)                          │  │
│  └─────────────────────────────────┬───────────────────────────────────┘  │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                                                                      │  │
│  │                    ╔═══════════════════════════╗                     │  │
│  │                    ║   PORTAL FRONTEND         ║                     │  │
│  │                    ║   (This Document)         ║                     │  │
│  │                    ╚═══════════════════════════╝                     │  │
│  │                                                                      │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                    │                                       │
│                                    ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐  │
│  │                           END USERS                                  │  │
│  │   • System Administrators    • Tenant Administrators                 │  │
│  │   • Developers               • Operators                             │  │
│  │   • Viewers                  • Billing Administrators                │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 2.1.2 System Interfaces

| Interface | Type | Description |
|-----------|------|-------------|
| Backend API | REST/HTTP | Django Ninja API at `/api/v1/*` |
| WebSocket | WS | Real-time events at `/ws/v1/*` |
| Keycloak | OIDC | Authentication and authorization |
| Browser Storage | Local | Theme persistence, session cache |

### 2.2 Product Functions

#### 2.2.1 Function Summary

| ID | Function | Priority |
|----|----------|----------|
| F-AUTH | Authentication & Authorization | Critical |
| F-ADMIN | Platform Administration | Critical |
| F-TENANT | Tenant Management | Critical |
| F-KEYS | API Key Management | High |
| F-SESSIONS | Session Management | High |
| F-BILLING | Billing & Usage | High |
| F-VOICE | Voice Configuration | Medium |
| F-THEME | Theming System | Medium |
| F-AUDIT | Audit Logging | Medium |

### 2.3 User Classes and Characteristics

#### 2.3.1 User Class Definitions

| User Class | Code | Description | Technical Expertise | Frequency |
|------------|------|-------------|---------------------|-----------|
| System Administrator | SYSADMIN | Platform operator with full access | Expert | Daily |
| Tenant Administrator | ADMIN | Organization administrator | Advanced | Daily |
| Developer | DEVELOPER | API integration developer | Expert | Daily |
| Operator | OPERATOR | Voice session operator | Intermediate | Daily |
| Viewer | VIEWER | Read-only access user | Basic | Weekly |
| Billing Administrator | BILLING | Financial management only | Basic | Monthly |

#### 2.3.2 User Class Hierarchy

```
                    ┌─────────────┐
                    │  SYSADMIN   │
                    │ (Platform)  │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │    ADMIN    │ │  DEVELOPER  │ │   BILLING   │
    │  (Tenant)   │ │  (Tenant)   │ │  (Tenant)   │
    └──────┬──────┘ └─────────────┘ └─────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
┌─────────┐ ┌─────────┐
│OPERATOR │ │ VIEWER  │
│(Tenant) │ │(Tenant) │
└─────────┘ └─────────┘
```

### 2.4 Operating Environment

#### 2.4.1 Client Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Browser | Chrome 90+, Firefox 88+, Safari 14+, Edge 90+ | Latest stable |
| JavaScript | ES2020 support | ES2022 support |
| Screen Resolution | 1280 × 720 | 1920 × 1080 |
| Network | 1 Mbps | 10 Mbps |
| WebSocket | Supported | Supported |

#### 2.4.2 Server Requirements

| Component | Specification |
|-----------|---------------|
| Web Server | Nginx 1.24+ |
| CDN | Cloudflare or equivalent |
| SSL/TLS | TLS 1.3 required |

### 2.5 Design and Implementation Constraints

#### 2.5.1 Technical Constraints

| ID | Constraint | Rationale |
|----|------------|-----------|
| TC-01 | Must use Lit 3.x Web Components | Standardization, performance |
| TC-02 | Must use TypeScript strict mode | Type safety, maintainability |
| TC-03 | Must use Vite for bundling | Build performance |
| TC-04 | Must use CSS Custom Properties | Theming support |
| TC-05 | Must support offline mode | Reliability |

#### 2.5.2 Regulatory Constraints

| ID | Constraint | Standard |
|----|------------|----------|
| RC-01 | WCAG 2.1 AA compliance | Accessibility |
| RC-02 | GDPR compliance | Data protection |
| RC-03 | SOC 2 Type II controls | Security |

### 2.6 Assumptions and Dependencies

#### 2.6.1 Assumptions

| ID | Assumption |
|----|------------|
| A-01 | Users have modern web browsers with JavaScript enabled |
| A-02 | Users have stable internet connectivity |
| A-03 | Backend API is available and responsive |
| A-04 | Keycloak is configured with Google OAuth provider |

#### 2.6.2 Dependencies

| ID | Dependency | Impact if Unavailable |
|----|------------|----------------------|
| D-01 | Backend API | Application non-functional |
| D-02 | Keycloak | Authentication impossible |
| D-03 | WebSocket | Real-time features disabled |
| D-04 | Lago | Billing data unavailable |



---

## 3. Specific Requirements

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces

##### UI-001: General Interface Requirements

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| UI-001.1 | The system SHALL provide a responsive layout supporting viewport widths from 320px to 3840px | High | Test |
| UI-001.2 | The system SHALL render at 60 frames per second during all user interactions | High | Test |
| UI-001.3 | The system SHALL provide visual feedback within 100ms of user input | High | Test |
| UI-001.4 | The system SHALL support keyboard navigation for all interactive elements | Critical | Test |
| UI-001.5 | The system SHALL maintain WCAG 2.1 AA contrast ratios (4.5:1 minimum) | Critical | Test |
| UI-001.6 | The system SHALL provide ARIA labels for all interactive controls | Critical | Test |
| UI-001.7 | The system SHALL support screen readers (NVDA, VoiceOver, JAWS) | Critical | Test |
| UI-001.8 | The system SHALL support text scaling up to 200% without loss of functionality | High | Test |

##### UI-002: Layout Structure

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| UI-002.1 | The system SHALL display a persistent header containing logo, search, notifications, and user menu | High | Inspection |
| UI-002.2 | The system SHALL display a collapsible sidebar navigation on screens ≥768px | High | Test |
| UI-002.3 | The system SHALL display a bottom navigation bar on screens <768px | High | Test |
| UI-002.4 | The system SHALL provide a main content area with scrollable overflow | High | Test |
| UI-002.5 | The sidebar SHALL collapse to icons-only mode when user preference is set | Medium | Test |

##### UI-003: Theme System (AgentSkin)

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| UI-003.1 | The system SHALL support dynamic theming via CSS Custom Properties | High | Test |
| UI-003.2 | The system SHALL define minimum 26 CSS custom properties for theming | High | Inspection |
| UI-003.3 | The system SHALL apply theme changes within 50ms without page reload | High | Test |
| UI-003.4 | The system SHALL persist active theme to localStorage | High | Test |
| UI-003.5 | The system SHALL provide default themes: Light, Dark, High Contrast | High | Inspection |
| UI-003.6 | The system SHALL validate theme files against JSON Schema before application | High | Test |
| UI-003.7 | The system SHALL reject theme values containing `url()` (XSS prevention) | Critical | Test |
| UI-003.8 | The system SHALL validate WCAG AA contrast ratios for theme colors | High | Test |

#### 3.1.2 Hardware Interfaces

Not applicable. The system is a web application with no direct hardware interfaces.

#### 3.1.3 Software Interfaces

##### SI-001: Backend API Interface

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| SI-001.1 | The system SHALL communicate with Backend API via HTTPS REST endpoints | Critical | Test |
| SI-001.2 | The system SHALL include JWT bearer token in Authorization header for all authenticated requests | Critical | Test |
| SI-001.3 | The system SHALL handle HTTP status codes according to RFC 7231 | High | Test |
| SI-001.4 | The system SHALL implement automatic token refresh on 401 responses | High | Test |
| SI-001.5 | The system SHALL implement request retry with exponential backoff for 5xx errors | High | Test |
| SI-001.6 | The system SHALL timeout requests after 30 seconds | High | Test |

##### SI-002: WebSocket Interface

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| SI-002.1 | The system SHALL establish WebSocket connection to `/ws/v1/events` for real-time updates | High | Test |
| SI-002.2 | The system SHALL authenticate WebSocket connections via token query parameter | Critical | Test |
| SI-002.3 | The system SHALL implement automatic reconnection with exponential backoff | High | Test |
| SI-002.4 | The system SHALL send heartbeat messages every 20 seconds | High | Test |
| SI-002.5 | The system SHALL handle connection drops gracefully with user notification | High | Test |
| SI-002.6 | The system SHALL fall back to Server-Sent Events if WebSocket unavailable | Medium | Test |

##### SI-003: Keycloak Interface

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| SI-003.1 | The system SHALL redirect unauthenticated users to Keycloak login | Critical | Test |
| SI-003.2 | The system SHALL support Google OAuth via Keycloak identity provider | Critical | Test |
| SI-003.3 | The system SHALL process OAuth callback and extract tokens | Critical | Test |
| SI-003.4 | The system SHALL decode JWT claims for user_id, tenant_id, and roles | Critical | Test |
| SI-003.5 | The system SHALL redirect to Keycloak logout on user logout | High | Test |
| SI-003.6 | The system SHALL clear all local tokens and storage on logout | Critical | Test |

#### 3.1.4 Communications Interfaces

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| CI-001 | The system SHALL use HTTPS (TLS 1.3) for all communications | Critical | Test |
| CI-002 | The system SHALL use WSS (WebSocket Secure) for real-time connections | Critical | Test |
| CI-003 | The system SHALL implement Content Security Policy headers | Critical | Inspection |
| CI-004 | The system SHALL set secure, httpOnly, sameSite flags on cookies | Critical | Inspection |

### 3.2 Functional Requirements

#### 3.2.1 Authentication (F-AUTH)

##### F-AUTH-001: Login

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-AUTH-001.1 | The system SHALL display login page at route `/login` | Critical | Test |
| F-AUTH-001.2 | The system SHALL provide "Sign in with Google" button | Critical | Test |
| F-AUTH-001.3 | The system SHALL provide "Sign in with SSO" button for enterprise users | Critical | Test |
| F-AUTH-001.4 | The system SHALL redirect to Keycloak with appropriate provider on button click | Critical | Test |
| F-AUTH-001.5 | The system SHALL display loading state during authentication | High | Test |
| F-AUTH-001.6 | The system SHALL display error message on authentication failure | High | Test |
| F-AUTH-001.7 | The system SHALL redirect authenticated users away from login page | High | Test |
| F-AUTH-001.8 | The system SHALL store intended destination for post-login redirect | High | Test |

##### F-AUTH-002: OAuth Callback

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-AUTH-002.1 | The system SHALL process OAuth callback at route `/auth/callback` | Critical | Test |
| F-AUTH-002.2 | The system SHALL validate state parameter to prevent CSRF | Critical | Test |
| F-AUTH-002.3 | The system SHALL exchange authorization code for tokens | Critical | Test |
| F-AUTH-002.4 | The system SHALL store access token securely (httpOnly cookie preferred) | Critical | Test |
| F-AUTH-002.5 | The system SHALL store refresh token securely | Critical | Test |
| F-AUTH-002.6 | The system SHALL extract user claims from ID token | Critical | Test |
| F-AUTH-002.7 | The system SHALL redirect SYSADMIN users to `/admin/dashboard` | High | Test |
| F-AUTH-002.8 | The system SHALL redirect tenant users to `/dashboard` | High | Test |
| F-AUTH-002.9 | The system SHALL redirect to stored destination if available | High | Test |

##### F-AUTH-003: Session Management

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-AUTH-003.1 | The system SHALL validate token on each protected route access | Critical | Test |
| F-AUTH-003.2 | The system SHALL refresh token automatically before expiration | High | Test |
| F-AUTH-003.3 | The system SHALL redirect to login on token refresh failure | High | Test |
| F-AUTH-003.4 | The system SHALL display session expiration warning 5 minutes before expiry | Medium | Test |
| F-AUTH-003.5 | The system SHALL support "Remember me" functionality (extended token lifetime) | Medium | Test |

##### F-AUTH-004: Logout

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-AUTH-004.1 | The system SHALL provide logout option in user menu | Critical | Test |
| F-AUTH-004.2 | The system SHALL clear all local storage on logout | Critical | Test |
| F-AUTH-004.3 | The system SHALL clear all session storage on logout | Critical | Test |
| F-AUTH-004.4 | The system SHALL invalidate tokens with backend | High | Test |
| F-AUTH-004.5 | The system SHALL redirect to Keycloak logout endpoint | High | Test |
| F-AUTH-004.6 | The system SHALL redirect to login page after logout | High | Test |

##### F-AUTH-005: Authorization

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-AUTH-005.1 | The system SHALL enforce role-based access control on all routes | Critical | Test |
| F-AUTH-005.2 | The system SHALL hide UI elements user lacks permission to access | High | Test |
| F-AUTH-005.3 | The system SHALL display 403 page for unauthorized route access | High | Test |
| F-AUTH-005.4 | The system SHALL cache permission checks for performance | Medium | Test |
| F-AUTH-005.5 | The system SHALL refresh permissions on role change event | High | Test |



#### 3.2.2 Platform Administration (F-ADMIN)

##### F-ADMIN-001: Admin Dashboard

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-001.1 | The system SHALL display admin dashboard at route `/admin/dashboard` | Critical | Test |
| F-ADMIN-001.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-001.3 | The system SHALL display total tenant count with month-to-date trend | High | Test |
| F-ADMIN-001.4 | The system SHALL display active session count with live updates | High | Test |
| F-ADMIN-001.5 | The system SHALL display total API requests with week-over-week trend | High | Test |
| F-ADMIN-001.6 | The system SHALL display revenue metrics with month-over-month trend | High | Test |
| F-ADMIN-001.7 | The system SHALL display system health status for all services | Critical | Test |
| F-ADMIN-001.8 | The system SHALL update health status every 30 seconds | High | Test |
| F-ADMIN-001.9 | The system SHALL display recent activity feed with last 10 events | High | Test |
| F-ADMIN-001.10 | The system SHALL provide quick action buttons for common tasks | Medium | Test |

##### F-ADMIN-002: Tenant Management

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-002.1 | The system SHALL display tenant list at route `/admin/tenants-mgmt` | Critical | Test |
| F-ADMIN-002.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-002.3 | The system SHALL display tenants in paginated data table | High | Test |
| F-ADMIN-002.4 | The system SHALL support sorting by name, tier, status, sessions, created date | High | Test |
| F-ADMIN-002.5 | The system SHALL support filtering by status (active, suspended, deleted) | High | Test |
| F-ADMIN-002.6 | The system SHALL support filtering by tier (free, pro, enterprise) | High | Test |
| F-ADMIN-002.7 | The system SHALL support text search on tenant name | High | Test |
| F-ADMIN-002.8 | The system SHALL provide "Create Tenant" action opening modal form | High | Test |
| F-ADMIN-002.9 | The system SHALL validate tenant name (2-100 characters) | High | Test |
| F-ADMIN-002.10 | The system SHALL validate tenant slug (3-50 lowercase alphanumeric + hyphens, unique) | High | Test |
| F-ADMIN-002.11 | The system SHALL require tier selection (free, pro, enterprise) | High | Test |
| F-ADMIN-002.12 | The system SHALL require initial admin email and name | High | Test |
| F-ADMIN-002.13 | The system SHALL optionally send welcome email to admin | Medium | Test |
| F-ADMIN-002.14 | The system SHALL provide row actions: View, Edit, Suspend, Reactivate, Delete | High | Test |
| F-ADMIN-002.15 | The system SHALL require confirmation for suspend action | High | Test |
| F-ADMIN-002.16 | The system SHALL require double confirmation for delete action | Critical | Test |
| F-ADMIN-002.17 | The system SHALL support bulk selection and bulk actions | Medium | Test |
| F-ADMIN-002.18 | The system SHALL support CSV export of tenant list | Medium | Test |

##### F-ADMIN-003: User Management

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-003.1 | The system SHALL display user list at route `/admin/users-mgmt` | Critical | Test |
| F-ADMIN-003.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-003.3 | The system SHALL display users across all tenants | High | Test |
| F-ADMIN-003.4 | The system SHALL support filtering by tenant | High | Test |
| F-ADMIN-003.5 | The system SHALL support filtering by role | High | Test |
| F-ADMIN-003.6 | The system SHALL support filtering by status (active, disabled) | High | Test |
| F-ADMIN-003.7 | The system SHALL display user's tenant, role, last login, status | High | Test |
| F-ADMIN-003.8 | The system SHALL provide actions: View, Edit Role, Disable, Enable, Delete | High | Test |
| F-ADMIN-003.9 | The system SHALL require confirmation for disable/delete actions | High | Test |

##### F-ADMIN-004: Platform Billing

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-004.1 | The system SHALL display billing overview at route `/admin/billing` | High | Test |
| F-ADMIN-004.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-004.3 | The system SHALL display total MRR (Monthly Recurring Revenue) | High | Test |
| F-ADMIN-004.4 | The system SHALL display revenue by tier breakdown | High | Test |
| F-ADMIN-004.5 | The system SHALL display outstanding invoices count and amount | High | Test |
| F-ADMIN-004.6 | The system SHALL display failed payment count | High | Test |
| F-ADMIN-004.7 | The system SHALL provide link to Lago dashboard | Medium | Test |

##### F-ADMIN-005: Subscription Plans

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-005.1 | The system SHALL display plan management at route `/admin/plans` | High | Test |
| F-ADMIN-005.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-005.3 | The system SHALL display all subscription plans with limits | High | Test |
| F-ADMIN-005.4 | The system SHALL allow editing plan limits (sessions, API calls, storage) | High | Test |
| F-ADMIN-005.5 | The system SHALL allow editing plan pricing | High | Test |
| F-ADMIN-005.6 | The system SHALL display tenant count per plan | High | Test |
| F-ADMIN-005.7 | The system SHALL require confirmation for plan changes affecting existing tenants | High | Test |

##### F-ADMIN-006: System Monitoring

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-006.1 | The system SHALL display monitoring dashboard at route `/admin/monitoring` | High | Test |
| F-ADMIN-006.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-006.3 | The system SHALL display health status for: Gateway, Workers, Redis, PostgreSQL, Keycloak, SpiceDB, Lago, NATS | Critical | Test |
| F-ADMIN-006.4 | The system SHALL display latency metrics for each service | High | Test |
| F-ADMIN-006.5 | The system SHALL use color coding: green (<threshold), yellow (warning), red (critical) | High | Test |
| F-ADMIN-006.6 | The system SHALL display uptime percentage for each service | High | Test |
| F-ADMIN-006.7 | The system SHALL display incident history | Medium | Test |
| F-ADMIN-006.8 | The system SHALL provide link to Grafana dashboards | Medium | Test |

##### F-ADMIN-007: Session Management (Admin)

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-007.1 | The system SHALL display all sessions at route `/admin/sessions` | High | Test |
| F-ADMIN-007.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-007.3 | The system SHALL display sessions across all tenants | High | Test |
| F-ADMIN-007.4 | The system SHALL support filtering by tenant | High | Test |
| F-ADMIN-007.5 | The system SHALL support filtering by status (active, completed, error) | High | Test |
| F-ADMIN-007.6 | The system SHALL support filtering by date range | High | Test |
| F-ADMIN-007.7 | The system SHALL display live indicator for active sessions | High | Test |
| F-ADMIN-007.8 | The system SHALL update active session list via WebSocket | High | Test |
| F-ADMIN-007.9 | The system SHALL provide session detail view with tabs: Overview, Transcript, Audio, Metrics | High | Test |
| F-ADMIN-007.10 | The system SHALL display real-time transcript for active sessions | High | Test |
| F-ADMIN-007.11 | The system SHALL provide action to terminate active session | High | Test |

##### F-ADMIN-008: Security Settings

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-008.1 | The system SHALL display security settings at route `/admin/security` | High | Test |
| F-ADMIN-008.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-008.3 | The system SHALL provide Keycloak configuration view at `/admin/security/keycloak` | High | Test |
| F-ADMIN-008.4 | The system SHALL provide OPA policy management at `/admin/security/policies` | High | Test |
| F-ADMIN-008.5 | The system SHALL provide Vault secrets overview at `/admin/security/secrets` | High | Test |
| F-ADMIN-008.6 | The system SHALL display security audit summary | High | Test |

##### F-ADMIN-009: Audit Logs

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-ADMIN-009.1 | The system SHALL display audit logs at route `/admin/audit` | High | Test |
| F-ADMIN-009.2 | The system SHALL restrict access to SYSADMIN role only | Critical | Test |
| F-ADMIN-009.3 | The system SHALL display audit events in chronological order | High | Test |
| F-ADMIN-009.4 | The system SHALL support filtering by event type | High | Test |
| F-ADMIN-009.5 | The system SHALL support filtering by actor (user) | High | Test |
| F-ADMIN-009.6 | The system SHALL support filtering by tenant | High | Test |
| F-ADMIN-009.7 | The system SHALL support filtering by date range | High | Test |
| F-ADMIN-009.8 | The system SHALL display event details: timestamp, actor, action, target, IP address | High | Test |
| F-ADMIN-009.9 | The system SHALL support CSV export of audit logs | Medium | Test |
| F-ADMIN-009.10 | The system SHALL retain audit logs for minimum 90 days | High | Inspection |



#### 3.2.3 Customer Portal (F-TENANT)

##### F-TENANT-001: Customer Dashboard

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TENANT-001.1 | The system SHALL display customer dashboard at route `/dashboard` | Critical | Test |
| F-TENANT-001.2 | The system SHALL restrict access to authenticated tenant users | Critical | Test |
| F-TENANT-001.3 | The system SHALL display personalized greeting with user name | Medium | Test |
| F-TENANT-001.4 | The system SHALL display tenant name and subscription tier | High | Test |
| F-TENANT-001.5 | The system SHALL display session count for current month | High | Test |
| F-TENANT-001.6 | The system SHALL display active API key count | High | Test |
| F-TENANT-001.7 | The system SHALL display usage percentage of quota | High | Test |
| F-TENANT-001.8 | The system SHALL display month-to-date cost | High | Test |
| F-TENANT-001.9 | The system SHALL display usage progress bars for sessions, API calls, storage | High | Test |
| F-TENANT-001.10 | The system SHALL display recent sessions list (last 5) | High | Test |
| F-TENANT-001.11 | The system SHALL provide quick action buttons: Create API Key, Start Session, View Reports, Invite Team | Medium | Test |

##### F-TENANT-002: API Key Management

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TENANT-002.1 | The system SHALL display API keys at route `/api-keys` | Critical | Test |
| F-TENANT-002.2 | The system SHALL restrict access to ADMIN and DEVELOPER roles | Critical | Test |
| F-TENANT-002.3 | The system SHALL display security warning about API key handling | High | Inspection |
| F-TENANT-002.4 | The system SHALL display API keys in table with columns: Name, Key (masked), Scopes, Expires, Actions | High | Test |
| F-TENANT-002.5 | The system SHALL mask API keys showing only prefix and last 4 characters | Critical | Test |
| F-TENANT-002.6 | The system SHALL provide "Create New Key" action | High | Test |
| F-TENANT-002.7 | The system SHALL require key name (1-100 characters) | High | Test |
| F-TENANT-002.8 | The system SHALL allow optional description | Medium | Test |
| F-TENANT-002.9 | The system SHALL require scope selection (realtime, billing, admin) | High | Test |
| F-TENANT-002.10 | The system SHALL require expiration selection (30d, 90d, 1y, never) | High | Test |
| F-TENANT-002.11 | The system SHALL allow rate limit tier selection based on plan | High | Test |
| F-TENANT-002.12 | The system SHALL display full API key only once after creation | Critical | Test |
| F-TENANT-002.13 | The system SHALL provide copy-to-clipboard functionality | High | Test |
| F-TENANT-002.14 | The system SHALL display warning that key cannot be shown again | Critical | Inspection |
| F-TENANT-002.15 | The system SHALL provide code example for API usage | Medium | Inspection |
| F-TENANT-002.16 | The system SHALL provide "Rotate" action with grace period option | High | Test |
| F-TENANT-002.17 | The system SHALL provide "Revoke" action with confirmation | High | Test |
| F-TENANT-002.18 | The system SHALL display last used timestamp for each key | Medium | Test |
| F-TENANT-002.19 | The system SHALL enforce maximum API key limit based on plan | High | Test |

##### F-TENANT-003: Session History

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TENANT-003.1 | The system SHALL display session history at route `/sessions` | High | Test |
| F-TENANT-003.2 | The system SHALL restrict access to tenant users (not BILLING) | Critical | Test |
| F-TENANT-003.3 | The system SHALL display sessions for current tenant only | Critical | Test |
| F-TENANT-003.4 | The system SHALL display sessions in paginated table | High | Test |
| F-TENANT-003.5 | The system SHALL support filtering by status (active, completed, error) | High | Test |
| F-TENANT-003.6 | The system SHALL support filtering by date range | High | Test |
| F-TENANT-003.7 | The system SHALL support filtering by API key used | Medium | Test |
| F-TENANT-003.8 | The system SHALL display: Session ID, Status, Duration, API Key, Created | High | Test |
| F-TENANT-003.9 | The system SHALL provide session detail view | High | Test |
| F-TENANT-003.10 | The system SHALL display session transcript in detail view | High | Test |
| F-TENANT-003.11 | The system SHALL display session metrics (latency, tokens) in detail view | High | Test |
| F-TENANT-003.12 | The system SHALL provide audio playback if recording enabled | Medium | Test |

##### F-TENANT-004: Billing

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TENANT-004.1 | The system SHALL display billing at route `/billing` | High | Test |
| F-TENANT-004.2 | The system SHALL restrict access to ADMIN and BILLING roles | Critical | Test |
| F-TENANT-004.3 | The system SHALL display current subscription plan | High | Test |
| F-TENANT-004.4 | The system SHALL display current billing period | High | Test |
| F-TENANT-004.5 | The system SHALL display month-to-date charges | High | Test |
| F-TENANT-004.6 | The system SHALL display projected monthly total | High | Test |
| F-TENANT-004.7 | The system SHALL display invoice history | High | Test |
| F-TENANT-004.8 | The system SHALL provide invoice download (PDF) | High | Test |
| F-TENANT-004.9 | The system SHALL display payment method on file | High | Test |
| F-TENANT-004.10 | The system SHALL provide link to update payment method (Lago portal) | High | Test |
| F-TENANT-004.11 | The system SHALL display usage breakdown by category | High | Test |

##### F-TENANT-005: Usage Analytics

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TENANT-005.1 | The system SHALL display usage analytics at route `/usage` | High | Test |
| F-TENANT-005.2 | The system SHALL restrict access to tenant users | Critical | Test |
| F-TENANT-005.3 | The system SHALL display usage charts for: Sessions, API Calls, Storage | High | Test |
| F-TENANT-005.4 | The system SHALL support time range selection: 7d, 30d, 90d, custom | High | Test |
| F-TENANT-005.5 | The system SHALL display usage vs quota comparison | High | Test |
| F-TENANT-005.6 | The system SHALL display usage trends | High | Test |
| F-TENANT-005.7 | The system SHALL display top API keys by usage | Medium | Test |
| F-TENANT-005.8 | The system SHALL provide CSV export of usage data | Medium | Test |

##### F-TENANT-006: Settings

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TENANT-006.1 | The system SHALL display settings at route `/settings` | High | Test |
| F-TENANT-006.2 | The system SHALL restrict write access to ADMIN and DEVELOPER roles | Critical | Test |
| F-TENANT-006.3 | The system SHALL organize settings in tabs: General, Notifications, Themes, Connectivity | High | Test |
| F-TENANT-006.4 | The system SHALL allow editing organization name (ADMIN only) | High | Test |
| F-TENANT-006.5 | The system SHALL allow configuring notification preferences | Medium | Test |
| F-TENANT-006.6 | The system SHALL allow theme selection and customization | High | Test |
| F-TENANT-006.7 | The system SHALL allow voice provider configuration | High | Test |
| F-TENANT-006.8 | The system SHALL validate settings before save | High | Test |
| F-TENANT-006.9 | The system SHALL display success/error feedback on save | High | Test |

##### F-TENANT-007: Team Management

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TENANT-007.1 | The system SHALL display team management at route `/team` | High | Test |
| F-TENANT-007.2 | The system SHALL restrict access to ADMIN role only | Critical | Test |
| F-TENANT-007.3 | The system SHALL display team members in table | High | Test |
| F-TENANT-007.4 | The system SHALL display: Name, Email, Role, Status, Last Login | High | Test |
| F-TENANT-007.5 | The system SHALL provide "Invite Member" action | High | Test |
| F-TENANT-007.6 | The system SHALL require email and role for invitation | High | Test |
| F-TENANT-007.7 | The system SHALL send invitation email via Keycloak | High | Test |
| F-TENANT-007.8 | The system SHALL display pending invitations | High | Test |
| F-TENANT-007.9 | The system SHALL allow resending invitation | Medium | Test |
| F-TENANT-007.10 | The system SHALL allow revoking invitation | High | Test |
| F-TENANT-007.11 | The system SHALL allow changing member role | High | Test |
| F-TENANT-007.12 | The system SHALL allow removing member (with confirmation) | High | Test |
| F-TENANT-007.13 | The system SHALL prevent removing last ADMIN | Critical | Test |
| F-TENANT-007.14 | The system SHALL enforce maximum team size based on plan | High | Test |

##### F-TENANT-008: Projects

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-TENANT-008.1 | The system SHALL display projects at route `/projects` | High | Test |
| F-TENANT-008.2 | The system SHALL restrict write access to ADMIN and DEVELOPER roles | Critical | Test |
| F-TENANT-008.3 | The system SHALL display projects in card grid or table view | High | Test |
| F-TENANT-008.4 | The system SHALL display: Name, Environment, API Keys, Sessions | High | Test |
| F-TENANT-008.5 | The system SHALL provide "Create Project" action | High | Test |
| F-TENANT-008.6 | The system SHALL require project name and environment (production, staging, development) | High | Test |
| F-TENANT-008.7 | The system SHALL allow editing project settings | High | Test |
| F-TENANT-008.8 | The system SHALL allow archiving project (with confirmation) | High | Test |
| F-TENANT-008.9 | The system SHALL allow deleting archived project (with double confirmation) | High | Test |



#### 3.2.4 Voice Configuration (F-VOICE)

##### F-VOICE-001: Voice Dashboard

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-001.1 | The system SHALL display voice dashboard at route `/dashboard/voice` | High | Test |
| F-VOICE-001.2 | The system SHALL restrict write access to ADMIN and DEVELOPER roles | Critical | Test |
| F-VOICE-001.3 | The system SHALL display current voice provider status | High | Test |
| F-VOICE-001.4 | The system SHALL display voice configuration summary | High | Test |
| F-VOICE-001.5 | The system SHALL provide quick links to all voice configuration sections | High | Test |
| F-VOICE-001.6 | The system SHALL display voice usage statistics | High | Test |

##### F-VOICE-002: Voice Provider Selection

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-002.1 | The system SHALL allow selection of voice provider: disabled, local, agentvoicebox | High | Test |
| F-VOICE-002.2 | The system SHALL display provider-specific configuration when selected | High | Test |
| F-VOICE-002.3 | WHEN provider is "disabled" THEN the system SHALL hide all voice UI elements | High | Test |
| F-VOICE-002.4 | WHEN provider is "local" THEN the system SHALL display STT/TTS configuration | High | Test |
| F-VOICE-002.5 | WHEN provider is "agentvoicebox" THEN the system SHALL display connection settings | High | Test |
| F-VOICE-002.6 | The system SHALL provide "Test Connection" button for agentvoicebox | High | Test |
| F-VOICE-002.7 | The system SHALL display connection test result (success/failure with details) | High | Test |
| F-VOICE-002.8 | The system SHALL emit settings.changed event on provider change | High | Test |

##### F-VOICE-003: STT Configuration

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-003.1 | The system SHALL display STT config at route `/dashboard/stt` | High | Test |
| F-VOICE-003.2 | The system SHALL restrict access to ADMIN and DEVELOPER roles | Critical | Test |
| F-VOICE-003.3 | The system SHALL allow selection of STT engine (whisper, faster-whisper) | High | Test |
| F-VOICE-003.4 | The system SHALL allow selection of model size (tiny, base, small, medium, large) | High | Test |
| F-VOICE-003.5 | The system SHALL display model size trade-offs (accuracy vs speed vs memory) | Medium | Inspection |
| F-VOICE-003.6 | The system SHALL allow language selection | High | Test |
| F-VOICE-003.7 | The system SHALL display estimated resource requirements | Medium | Test |

##### F-VOICE-004: TTS Configuration

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-004.1 | The system SHALL allow selection of TTS engine (kokoro, browser) | High | Test |
| F-VOICE-004.2 | The system SHALL allow voice selection from available voices | High | Test |
| F-VOICE-004.3 | The system SHALL provide voice preview (play sample) | High | Test |
| F-VOICE-004.4 | The system SHALL allow speech rate adjustment (0.5x - 2.0x) | High | Test |
| F-VOICE-004.5 | The system SHALL allow pitch adjustment | Medium | Test |
| F-VOICE-004.6 | The system SHALL display supported languages per voice | High | Test |

##### F-VOICE-005: Wake Words

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-005.1 | The system SHALL display wake words at route `/dashboard/wake-words` | High | Test |
| F-VOICE-005.2 | The system SHALL restrict access to ADMIN and DEVELOPER roles | Critical | Test |
| F-VOICE-005.3 | The system SHALL display configured wake words in list | High | Test |
| F-VOICE-005.4 | The system SHALL allow adding custom wake words | High | Test |
| F-VOICE-005.5 | The system SHALL allow enabling/disabling individual wake words | High | Test |
| F-VOICE-005.6 | The system SHALL allow adjusting sensitivity per wake word | Medium | Test |
| F-VOICE-005.7 | The system SHALL provide wake word testing interface | Medium | Test |

##### F-VOICE-006: Voice Cloning

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-006.1 | The system SHALL display voice cloning at route `/dashboard/voice-cloning` | High | Test |
| F-VOICE-006.2 | The system SHALL restrict access to ADMIN and DEVELOPER roles | Critical | Test |
| F-VOICE-006.3 | The system SHALL display cloned voices in gallery | High | Test |
| F-VOICE-006.4 | The system SHALL allow uploading audio samples for cloning | High | Test |
| F-VOICE-006.5 | The system SHALL validate audio format (WAV, MP3, minimum 30 seconds) | High | Test |
| F-VOICE-006.6 | The system SHALL display cloning progress | High | Test |
| F-VOICE-006.7 | The system SHALL allow previewing cloned voice | High | Test |
| F-VOICE-006.8 | The system SHALL allow deleting cloned voice | High | Test |

##### F-VOICE-007: Personas

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-007.1 | The system SHALL display personas at route `/dashboard/personas` | High | Test |
| F-VOICE-007.2 | The system SHALL restrict write access to ADMIN and DEVELOPER roles | Critical | Test |
| F-VOICE-007.3 | The system SHALL display personas in card grid | High | Test |
| F-VOICE-007.4 | The system SHALL display: Name, Voice, Language, Active status | High | Test |
| F-VOICE-007.5 | The system SHALL allow creating new persona | High | Test |
| F-VOICE-007.6 | The system SHALL require persona name, voice selection, system prompt | High | Test |
| F-VOICE-007.7 | The system SHALL allow editing persona | High | Test |
| F-VOICE-007.8 | The system SHALL allow duplicating persona | Medium | Test |
| F-VOICE-007.9 | The system SHALL allow setting default persona | High | Test |
| F-VOICE-007.10 | The system SHALL allow deleting persona (with confirmation) | High | Test |

##### F-VOICE-008: LLM Configuration

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-008.1 | The system SHALL display LLM config at route `/dashboard/llm` | High | Test |
| F-VOICE-008.2 | The system SHALL restrict access to ADMIN and DEVELOPER roles | Critical | Test |
| F-VOICE-008.3 | The system SHALL allow selection of LLM provider (groq, openai, local) | High | Test |
| F-VOICE-008.4 | The system SHALL allow selection of model | High | Test |
| F-VOICE-008.5 | The system SHALL allow configuring temperature (0.0 - 2.0) | High | Test |
| F-VOICE-008.6 | The system SHALL allow configuring max tokens | High | Test |
| F-VOICE-008.7 | The system SHALL allow configuring system prompt | High | Test |
| F-VOICE-008.8 | The system SHALL display estimated cost per request | Medium | Test |

##### F-VOICE-009: Intents

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-009.1 | The system SHALL display intents at route `/dashboard/intents` | High | Test |
| F-VOICE-009.2 | The system SHALL restrict write access to ADMIN and DEVELOPER roles | Critical | Test |
| F-VOICE-009.3 | The system SHALL display intents in table | High | Test |
| F-VOICE-009.4 | The system SHALL display: Name, Description, Sample Utterances, Actions | High | Test |
| F-VOICE-009.5 | The system SHALL allow creating new intent | High | Test |
| F-VOICE-009.6 | The system SHALL require intent name and at least one sample utterance | High | Test |
| F-VOICE-009.7 | The system SHALL allow adding multiple sample utterances | High | Test |
| F-VOICE-009.8 | The system SHALL allow mapping intent to skill | High | Test |
| F-VOICE-009.9 | The system SHALL allow editing intent | High | Test |
| F-VOICE-009.10 | The system SHALL allow deleting intent (with confirmation) | High | Test |

##### F-VOICE-010: Skills

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-010.1 | The system SHALL display skills at route `/dashboard/skills` | High | Test |
| F-VOICE-010.2 | The system SHALL restrict write access to ADMIN and DEVELOPER roles | Critical | Test |
| F-VOICE-010.3 | The system SHALL display skills in card grid | High | Test |
| F-VOICE-010.4 | The system SHALL display: Name, Description, Type, Status | High | Test |
| F-VOICE-010.5 | The system SHALL allow enabling/disabling skills | High | Test |
| F-VOICE-010.6 | The system SHALL allow configuring skill parameters | High | Test |
| F-VOICE-010.7 | The system SHALL display skill documentation | Medium | Test |

##### F-VOICE-011: Message Bus

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-VOICE-011.1 | The system SHALL display message bus at route `/dashboard/messagebus` | High | Test |
| F-VOICE-011.2 | The system SHALL restrict access to ADMIN, DEVELOPER, OPERATOR roles | Critical | Test |
| F-VOICE-011.3 | The system SHALL display real-time message stream | High | Test |
| F-VOICE-011.4 | The system SHALL allow filtering by message type | High | Test |
| F-VOICE-011.5 | The system SHALL allow pausing/resuming stream | High | Test |
| F-VOICE-011.6 | The system SHALL display message details on selection | High | Test |
| F-VOICE-011.7 | The system SHALL allow sending test messages (DEVELOPER only) | Medium | Test |



#### 3.2.5 Theming System (F-THEME)

##### F-THEME-001: Theme Gallery

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-THEME-001.1 | The system SHALL display theme gallery at route `/themes` | High | Test |
| F-THEME-001.2 | The system SHALL restrict access to authenticated users | Critical | Test |
| F-THEME-001.3 | The system SHALL display themes in responsive card grid | High | Test |
| F-THEME-001.4 | The system SHALL display theme preview thumbnail for each theme | High | Test |
| F-THEME-001.5 | The system SHALL display theme name, author, and version | High | Test |
| F-THEME-001.6 | The system SHALL indicate currently active theme | High | Test |
| F-THEME-001.7 | The system SHALL provide "Apply" action for each theme | High | Test |
| F-THEME-001.8 | The system SHALL provide "Preview" action for each theme | High | Test |
| F-THEME-001.9 | The system SHALL provide "Edit" action for custom themes (ADMIN, DEVELOPER) | High | Test |
| F-THEME-001.10 | The system SHALL provide "Delete" action for custom themes (ADMIN only) | High | Test |
| F-THEME-001.11 | The system SHALL provide "Upload Theme" action (ADMIN, DEVELOPER) | High | Test |
| F-THEME-001.12 | The system SHALL provide "Create Theme" action (ADMIN, DEVELOPER) | High | Test |
| F-THEME-001.13 | The system SHALL support filtering by category (light, dark, high-contrast, custom) | Medium | Test |
| F-THEME-001.14 | The system SHALL support search by theme name | Medium | Test |

##### F-THEME-002: Default Themes

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-THEME-002.1 | The system SHALL provide "Default Light" theme | Critical | Inspection |
| F-THEME-002.2 | The system SHALL provide "Midnight Dark" theme | Critical | Inspection |
| F-THEME-002.3 | The system SHALL provide "High Contrast" theme (WCAG AAA compliant) | Critical | Inspection |
| F-THEME-002.4 | Default themes SHALL NOT be editable or deletable | Critical | Test |
| F-THEME-002.5 | Default themes SHALL be available to all users | Critical | Test |
| F-THEME-002.6 | The system SHALL apply "Default Light" theme for new users | High | Test |

##### F-THEME-003: Theme Preview

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-THEME-003.1 | The system SHALL display theme preview in split-screen mode | High | Test |
| F-THEME-003.2 | The system SHALL show current theme on left, preview theme on right | High | Test |
| F-THEME-003.3 | The system SHALL render sample UI components in preview | High | Test |
| F-THEME-003.4 | The system SHALL include: buttons, inputs, cards, tables, charts in preview | High | Test |
| F-THEME-003.5 | The system SHALL provide "Apply" button in preview mode | High | Test |
| F-THEME-003.6 | The system SHALL provide "Cancel" button to exit preview | High | Test |
| F-THEME-003.7 | The system SHALL revert to current theme on cancel | High | Test |
| F-THEME-003.8 | The system SHALL apply preview theme within 50ms | High | Test |

##### F-THEME-004: Theme Upload

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-THEME-004.1 | The system SHALL accept theme files via drag-and-drop | High | Test |
| F-THEME-004.2 | The system SHALL accept theme files via file picker | High | Test |
| F-THEME-004.3 | The system SHALL accept JSON file format only | High | Test |
| F-THEME-004.4 | The system SHALL validate file size (max 100KB) | High | Test |
| F-THEME-004.5 | The system SHALL validate JSON syntax | High | Test |
| F-THEME-004.6 | The system SHALL validate against theme JSON Schema | Critical | Test |
| F-THEME-004.7 | The system SHALL validate all 26 required CSS variables present | Critical | Test |
| F-THEME-004.8 | The system SHALL reject themes containing `url()` in CSS values | Critical | Test |
| F-THEME-004.9 | The system SHALL reject themes containing `javascript:` in values | Critical | Test |
| F-THEME-004.10 | The system SHALL reject themes containing `expression()` in values | Critical | Test |
| F-THEME-004.11 | The system SHALL validate WCAG AA contrast ratios (4.5:1 minimum) | High | Test |
| F-THEME-004.12 | The system SHALL display validation errors with specific details | High | Test |
| F-THEME-004.13 | The system SHALL display validation warnings (non-blocking) | Medium | Test |
| F-THEME-004.14 | The system SHALL enforce rate limit (10 uploads/hour/user) | High | Test |
| F-THEME-004.15 | The system SHALL display rate limit status | Medium | Test |

##### F-THEME-005: Theme Editor

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-THEME-005.1 | The system SHALL display theme editor at route `/themes/editor` | High | Test |
| F-THEME-005.2 | The system SHALL restrict access to ADMIN and DEVELOPER roles | Critical | Test |
| F-THEME-005.3 | The system SHALL display all 26 CSS variables in organized sections | High | Test |
| F-THEME-005.4 | The system SHALL organize variables: Colors, Typography, Spacing, Effects | High | Test |
| F-THEME-005.5 | The system SHALL provide color picker for color variables | High | Test |
| F-THEME-005.6 | The system SHALL provide numeric input for spacing variables | High | Test |
| F-THEME-005.7 | The system SHALL provide font selector for typography variables | High | Test |
| F-THEME-005.8 | The system SHALL display live preview while editing | High | Test |
| F-THEME-005.9 | The system SHALL validate contrast ratios in real-time | High | Test |
| F-THEME-005.10 | The system SHALL display contrast warnings for failing combinations | High | Test |
| F-THEME-005.11 | The system SHALL provide "Save" action | High | Test |
| F-THEME-005.12 | The system SHALL provide "Save As" action for creating new theme | High | Test |
| F-THEME-005.13 | The system SHALL provide "Reset" action to revert changes | High | Test |
| F-THEME-005.14 | The system SHALL provide "Export" action to download JSON | High | Test |
| F-THEME-005.15 | The system SHALL warn on unsaved changes before navigation | High | Test |

##### F-THEME-006: Theme Application

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-THEME-006.1 | The system SHALL apply theme changes within 50ms | Critical | Test |
| F-THEME-006.2 | The system SHALL NOT require page reload for theme changes | Critical | Test |
| F-THEME-006.3 | The system SHALL persist active theme to localStorage | High | Test |
| F-THEME-006.4 | The system SHALL persist active theme to user preferences (backend) | High | Test |
| F-THEME-006.5 | The system SHALL restore theme on page load from localStorage | High | Test |
| F-THEME-006.6 | The system SHALL sync theme across browser tabs | Medium | Test |
| F-THEME-006.7 | The system SHALL emit `theme.changed` WebSocket event | High | Test |
| F-THEME-006.8 | The system SHALL apply theme to all Shadow DOM components | Critical | Test |

##### F-THEME-007: Theme CSS Variables

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-THEME-007.1 | The system SHALL define `--eog-bg-void` (background void color) | Critical | Inspection |
| F-THEME-007.2 | The system SHALL define `--eog-bg-surface` (surface background) | Critical | Inspection |
| F-THEME-007.3 | The system SHALL define `--eog-bg-elevated` (elevated surface) | Critical | Inspection |
| F-THEME-007.4 | The system SHALL define `--eog-glass-surface` (glass effect surface) | Critical | Inspection |
| F-THEME-007.5 | The system SHALL define `--eog-glass-border` (glass effect border) | Critical | Inspection |
| F-THEME-007.6 | The system SHALL define `--eog-text-main` (primary text color) | Critical | Inspection |
| F-THEME-007.7 | The system SHALL define `--eog-text-dim` (secondary text color) | Critical | Inspection |
| F-THEME-007.8 | The system SHALL define `--eog-accent-primary` (primary accent) | Critical | Inspection |
| F-THEME-007.9 | The system SHALL define `--eog-accent-secondary` (secondary accent) | Critical | Inspection |
| F-THEME-007.10 | The system SHALL define `--eog-accent-success` (success color) | Critical | Inspection |
| F-THEME-007.11 | The system SHALL define `--eog-accent-warning` (warning color) | Critical | Inspection |
| F-THEME-007.12 | The system SHALL define `--eog-accent-danger` (danger/error color) | Critical | Inspection |
| F-THEME-007.13 | The system SHALL define `--eog-shadow-soft` (soft shadow) | Critical | Inspection |
| F-THEME-007.14 | The system SHALL define `--eog-radius-sm` (small border radius) | Critical | Inspection |
| F-THEME-007.15 | The system SHALL define `--eog-radius-md` (medium border radius) | Critical | Inspection |
| F-THEME-007.16 | The system SHALL define `--eog-radius-lg` (large border radius) | Critical | Inspection |
| F-THEME-007.17 | The system SHALL define `--eog-radius-full` (full/pill border radius) | Critical | Inspection |
| F-THEME-007.18 | The system SHALL define `--eog-spacing-xs` (extra small spacing) | Critical | Inspection |
| F-THEME-007.19 | The system SHALL define `--eog-spacing-sm` (small spacing) | Critical | Inspection |
| F-THEME-007.20 | The system SHALL define `--eog-spacing-md` (medium spacing) | Critical | Inspection |
| F-THEME-007.21 | The system SHALL define `--eog-spacing-lg` (large spacing) | Critical | Inspection |
| F-THEME-007.22 | The system SHALL define `--eog-spacing-xl` (extra large spacing) | Critical | Inspection |
| F-THEME-007.23 | The system SHALL define `--eog-font-sans` (sans-serif font family) | Critical | Inspection |
| F-THEME-007.24 | The system SHALL define `--eog-font-mono` (monospace font family) | Critical | Inspection |
| F-THEME-007.25 | The system SHALL define `--eog-text-xs` through `--eog-text-lg` (font sizes) | Critical | Inspection |
| F-THEME-007.26 | The system SHALL define `--eog-focus-ring` (focus indicator color) | Critical | Inspection |



#### 3.2.6 Real-Time Communication (F-REALTIME)

##### F-REALTIME-001: WebSocket Connection

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-REALTIME-001.1 | The system SHALL establish WebSocket connection on application load | Critical | Test |
| F-REALTIME-001.2 | The system SHALL connect to `/ws/v1/events` endpoint | Critical | Test |
| F-REALTIME-001.3 | The system SHALL authenticate connection via token query parameter | Critical | Test |
| F-REALTIME-001.4 | The system SHALL display connection status indicator | High | Test |
| F-REALTIME-001.5 | The system SHALL reconnect automatically on connection drop | Critical | Test |
| F-REALTIME-001.6 | The system SHALL use exponential backoff for reconnection (1s, 2s, 4s, 8s, max 30s) | High | Test |
| F-REALTIME-001.7 | The system SHALL display reconnection status to user | High | Test |
| F-REALTIME-001.8 | The system SHALL send heartbeat every 20 seconds | High | Test |
| F-REALTIME-001.9 | The system SHALL timeout connection after 60 seconds without heartbeat response | High | Test |
| F-REALTIME-001.10 | The system SHALL fall back to Server-Sent Events if WebSocket unavailable | Medium | Test |

##### F-REALTIME-002: Event Handling

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-REALTIME-002.1 | The system SHALL handle `mode.changed` events | High | Test |
| F-REALTIME-002.2 | The system SHALL handle `settings.changed` events | High | Test |
| F-REALTIME-002.3 | The system SHALL handle `theme.changed` events | High | Test |
| F-REALTIME-002.4 | The system SHALL handle `voice.*` events (started, stopped, transcription, etc.) | High | Test |
| F-REALTIME-002.5 | The system SHALL handle `session.*` events (created, updated, ended) | High | Test |
| F-REALTIME-002.6 | The system SHALL handle `notification.*` events | High | Test |
| F-REALTIME-002.7 | The system SHALL handle `system.maintenance` events | High | Test |
| F-REALTIME-002.8 | The system SHALL update UI within 100ms of receiving event | High | Test |
| F-REALTIME-002.9 | The system SHALL queue events during reconnection | High | Test |
| F-REALTIME-002.10 | The system SHALL replay missed events after reconnection | High | Test |

##### F-REALTIME-003: Notifications

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-REALTIME-003.1 | The system SHALL display notification bell icon in header | High | Test |
| F-REALTIME-003.2 | The system SHALL display unread notification count badge | High | Test |
| F-REALTIME-003.3 | The system SHALL display notification dropdown on click | High | Test |
| F-REALTIME-003.4 | The system SHALL display notifications in chronological order (newest first) | High | Test |
| F-REALTIME-003.5 | The system SHALL display notification: title, message, timestamp, type | High | Test |
| F-REALTIME-003.6 | The system SHALL support notification types: info, success, warning, error | High | Test |
| F-REALTIME-003.7 | The system SHALL mark notification as read on click | High | Test |
| F-REALTIME-003.8 | The system SHALL provide "Mark all as read" action | Medium | Test |
| F-REALTIME-003.9 | The system SHALL provide "Clear all" action | Medium | Test |
| F-REALTIME-003.10 | The system SHALL display toast notification for high-priority events | High | Test |
| F-REALTIME-003.11 | The system SHALL auto-dismiss toast after 5 seconds | High | Test |
| F-REALTIME-003.12 | The system SHALL allow manual dismissal of toast | High | Test |



#### 3.2.7 User Profile (F-PROFILE)

##### F-PROFILE-001: User Menu

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-PROFILE-001.1 | The system SHALL display user avatar in header | High | Test |
| F-PROFILE-001.2 | The system SHALL display user menu dropdown on avatar click | High | Test |
| F-PROFILE-001.3 | The system SHALL display user name and email in menu header | High | Test |
| F-PROFILE-001.4 | The system SHALL display current role | High | Test |
| F-PROFILE-001.5 | The system SHALL display tenant name (for tenant users) | High | Test |
| F-PROFILE-001.6 | The system SHALL provide "Profile" link | High | Test |
| F-PROFILE-001.7 | The system SHALL provide "Preferences" link | High | Test |
| F-PROFILE-001.8 | The system SHALL provide "Logout" action | Critical | Test |
| F-PROFILE-001.9 | The system SHALL provide keyboard shortcut for logout (Ctrl+Shift+L) | Medium | Test |

##### F-PROFILE-002: Profile Page

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-PROFILE-002.1 | The system SHALL display profile page at route `/profile` | High | Test |
| F-PROFILE-002.2 | The system SHALL display user avatar (large) | High | Test |
| F-PROFILE-002.3 | The system SHALL display user name | High | Test |
| F-PROFILE-002.4 | The system SHALL display user email | High | Test |
| F-PROFILE-002.5 | The system SHALL display user role | High | Test |
| F-PROFILE-002.6 | The system SHALL display account creation date | Medium | Test |
| F-PROFILE-002.7 | The system SHALL display last login timestamp | Medium | Test |
| F-PROFILE-002.8 | The system SHALL provide link to Keycloak account management | High | Test |
| F-PROFILE-002.9 | The system SHALL display active sessions count | Medium | Test |

##### F-PROFILE-003: User Preferences

| ID | Requirement | Priority | Verification |
|----|-------------|----------|--------------|
| F-PROFILE-003.1 | The system SHALL display preferences at route `/preferences` | High | Test |
| F-PROFILE-003.2 | The system SHALL allow language selection | High | Test |
| F-PROFILE-003.3 | The system SHALL allow timezone selection | High | Test |
| F-PROFILE-003.4 | The system SHALL allow date format selection | Medium | Test |
| F-PROFILE-003.5 | The system SHALL allow notification preferences configuration | High | Test |
| F-PROFILE-003.6 | The system SHALL allow email notification toggle | High | Test |
| F-PROFILE-003.7 | The system SHALL allow in-app notification toggle | High | Test |
| F-PROFILE-003.8 | The system SHALL allow sidebar collapsed preference | Medium | Test |
| F-PROFILE-003.9 | The system SHALL allow reduced motion preference | High | Test |
| F-PROFILE-003.10 | The system SHALL persist preferences to backend | High | Test |
| F-PROFILE-003.11 | The system SHALL sync preferences across devices | High | Test |



---

## 4. System Features

This section provides detailed use cases and interaction diagrams for key system features.

### 4.1 Authentication Flow

#### 4.1.1 Use Case: UC-AUTH-001 - User Login with Google OAuth

**Primary Actor:** Unauthenticated User  
**Preconditions:** User has valid Google account  
**Postconditions:** User is authenticated and redirected to appropriate dashboard  

**Main Success Scenario:**

| Step | Actor | System |
|------|-------|--------|
| 1 | User navigates to application URL | |
| 2 | | System detects no valid session |
| 3 | | System redirects to `/login` |
| 4 | | System displays login page with "Sign in with Google" button |
| 5 | User clicks "Sign in with Google" | |
| 6 | | System generates state parameter and stores in session |
| 7 | | System redirects to Keycloak authorization endpoint with Google IDP hint |
| 8 | | Keycloak redirects to Google OAuth consent screen |
| 9 | User authenticates with Google credentials | |
| 10 | User grants consent | |
| 11 | | Google redirects to Keycloak callback |
| 12 | | Keycloak creates/updates user, generates tokens |
| 13 | | Keycloak redirects to `/auth/callback` with authorization code |
| 14 | | System validates state parameter |
| 15 | | System exchanges code for tokens via backend |
| 16 | | System stores tokens securely |
| 17 | | System decodes JWT to extract user_id, tenant_id, roles |
| 18 | | System determines redirect based on role |
| 19 | | System redirects SYSADMIN to `/admin/dashboard` |
| 20 | | System redirects tenant users to `/dashboard` |

**Alternative Flows:**

| ID | Condition | Steps |
|----|-----------|-------|
| 4a | User already authenticated | System redirects to appropriate dashboard |
| 9a | User cancels Google authentication | Keycloak redirects with error, system displays error message |
| 14a | State parameter invalid | System displays CSRF error, redirects to login |
| 15a | Token exchange fails | System displays authentication error, redirects to login |
| 17a | User not associated with tenant | System displays "No tenant access" error |

**Sequence Diagram:**

```
┌─────┐          ┌─────────┐          ┌──────────┐          ┌────────┐          ┌────────┐
│User │          │Frontend │          │ Backend  │          │Keycloak│          │ Google │
└──┬──┘          └────┬────┘          └────┬─────┘          └───┬────┘          └───┬────┘
   │                  │                    │                    │                   │
   │ Navigate to /    │                    │                    │                   │
   │─────────────────>│                    │                    │                   │
   │                  │                    │                    │                   │
   │                  │ Check session      │                    │                   │
   │                  │───────────────────>│                    │                   │
   │                  │                    │                    │                   │
   │                  │ No valid session   │                    │                   │
   │                  │<───────────────────│                    │                   │
   │                  │                    │                    │                   │
   │ Redirect /login  │                    │                    │                   │
   │<─────────────────│                    │                    │                   │
   │                  │                    │                    │                   │
   │ Click Google SSO │                    │                    │                   │
   │─────────────────>│                    │                    │                   │
   │                  │                    │                    │                   │
   │                  │ Generate state     │                    │                   │
   │                  │────────┐           │                    │                   │
   │                  │        │           │                    │                   │
   │                  │<───────┘           │                    │                   │
   │                  │                    │                    │                   │
   │ Redirect to Keycloak                  │                    │                   │
   │<─────────────────│                    │                    │                   │
   │                  │                    │                    │                   │
   │ Authorization request (kc_idp_hint=google)                 │                   │
   │────────────────────────────────────────────────────────────>                   │
   │                  │                    │                    │                   │
   │ Redirect to Google                    │                    │                   │
   │<────────────────────────────────────────────────────────────                   │
   │                  │                    │                    │                   │
   │ Google OAuth consent                  │                    │                   │
   │───────────────────────────────────────────────────────────────────────────────>│
   │                  │                    │                    │                   │
   │ User authenticates & consents         │                    │                   │
   │<───────────────────────────────────────────────────────────────────────────────│
   │                  │                    │                    │                   │
   │ Callback to Keycloak                  │                    │                   │
   │────────────────────────────────────────────────────────────>                   │
   │                  │                    │                    │                   │
   │ Redirect to /auth/callback?code=xxx&state=yyy              │                   │
   │<────────────────────────────────────────────────────────────                   │
   │                  │                    │                    │                   │
   │ /auth/callback   │                    │                    │                   │
   │─────────────────>│                    │                    │                   │
   │                  │                    │                    │                   │
   │                  │ Validate state     │                    │                   │
   │                  │────────┐           │                    │                   │
   │                  │        │           │                    │                   │
   │                  │<───────┘           │                    │                   │
   │                  │                    │                    │                   │
   │                  │ Exchange code      │                    │                   │
   │                  │───────────────────>│                    │                   │
   │                  │                    │                    │                   │
   │                  │                    │ Token request      │                   │
   │                  │                    │───────────────────>│                   │
   │                  │                    │                    │                   │
   │                  │                    │ Tokens (access, refresh, id)           │
   │                  │                    │<───────────────────│                   │
   │                  │                    │                    │                   │
   │                  │ Tokens             │                    │                   │
   │                  │<───────────────────│                    │                   │
   │                  │                    │                    │                   │
   │                  │ Store tokens       │                    │                   │
   │                  │────────┐           │                    │                   │
   │                  │        │           │                    │                   │
   │                  │<───────┘           │                    │                   │
   │                  │                    │                    │                   │
   │                  │ Decode JWT claims  │                    │                   │
   │                  │────────┐           │                    │                   │
   │                  │        │           │                    │                   │
   │                  │<───────┘           │                    │                   │
   │                  │                    │                    │                   │
   │ Redirect to dashboard                 │                    │                   │
   │<─────────────────│                    │                    │                   │
   │                  │                    │                    │                   │
```


#### 4.1.2 Use Case: UC-AUTH-002 - Session Refresh

**Primary Actor:** Authenticated User  
**Preconditions:** User has valid refresh token  
**Postconditions:** User has new access token  

**Main Success Scenario:**

| Step | Actor | System |
|------|-------|--------|
| 1 | | System detects access token expiring in < 5 minutes |
| 2 | | System initiates token refresh in background |
| 3 | | System sends refresh token to backend |
| 4 | | Backend exchanges refresh token with Keycloak |
| 5 | | Keycloak validates refresh token |
| 6 | | Keycloak issues new access and refresh tokens |
| 7 | | Backend returns new tokens to frontend |
| 8 | | System stores new tokens |
| 9 | | System continues normal operation |

**Alternative Flows:**

| ID | Condition | Steps |
|----|-----------|-------|
| 5a | Refresh token expired | Keycloak returns error, system redirects to login |
| 5b | Refresh token revoked | Keycloak returns error, system clears tokens, redirects to login |
| 4a | Backend unavailable | System displays warning, retries with backoff |

#### 4.1.3 Use Case: UC-AUTH-003 - User Logout

**Primary Actor:** Authenticated User  
**Preconditions:** User is authenticated  
**Postconditions:** User session is terminated, tokens cleared  

**Main Success Scenario:**

| Step | Actor | System |
|------|-------|--------|
| 1 | User clicks "Logout" in user menu | |
| 2 | | System clears localStorage |
| 3 | | System clears sessionStorage |
| 4 | | System invalidates tokens with backend |
| 5 | | Backend revokes tokens with Keycloak |
| 6 | | System redirects to Keycloak logout endpoint |
| 7 | | Keycloak terminates SSO session |
| 8 | | Keycloak redirects to login page |
| 9 | | System displays login page |

---

### 4.2 Tenant Management Flow

#### 4.2.1 Use Case: UC-TENANT-001 - Create New Tenant

**Primary Actor:** SYSADMIN  
**Preconditions:** User has SYSADMIN role  
**Postconditions:** New tenant created with initial admin user  

**Main Success Scenario:**

| Step | Actor | System |
|------|-------|--------|
| 1 | SYSADMIN navigates to `/admin/tenants-mgmt` | |
| 2 | | System displays tenant list |
| 3 | SYSADMIN clicks "Create Tenant" | |
| 4 | | System displays create tenant modal |
| 5 | SYSADMIN enters tenant name | |
| 6 | | System auto-generates slug from name |
| 7 | SYSADMIN modifies slug if needed | |
| 8 | | System validates slug uniqueness in real-time |
| 9 | SYSADMIN selects tier (free/pro/enterprise) | |
| 10 | SYSADMIN enters initial admin email | |
| 11 | SYSADMIN enters initial admin name | |
| 12 | SYSADMIN optionally checks "Send welcome email" | |
| 13 | SYSADMIN clicks "Create" | |
| 14 | | System validates all fields |
| 15 | | System sends create request to backend |
| 16 | | Backend creates tenant in PostgreSQL |
| 17 | | Backend creates tenant in Lago (billing) |
| 18 | | Backend creates admin user in Keycloak |
| 19 | | Backend creates SpiceDB relationships |
| 20 | | Backend sends welcome email if requested |
| 21 | | System displays success notification |
| 22 | | System closes modal |
| 23 | | System refreshes tenant list |

**State Diagram - Tenant Lifecycle:**

```
                    ┌─────────────────┐
                    │                 │
                    │    CREATING     │
                    │                 │
                    └────────┬────────┘
                             │
                             │ Creation successful
                             ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│                 │    │                 │    │                 │
│   SUSPENDED     │◄───│     ACTIVE      │───►│    DELETED      │
│                 │    │                 │    │                 │
└────────┬────────┘    └─────────────────┘    └─────────────────┘
         │                     ▲
         │                     │
         │   Reactivate        │
         └─────────────────────┘
```


### 4.3 API Key Management Flow

#### 4.3.1 Use Case: UC-KEY-001 - Create API Key

**Primary Actor:** ADMIN or DEVELOPER  
**Preconditions:** User has ADMIN or DEVELOPER role within tenant  
**Postconditions:** New API key created and displayed once  

**Main Success Scenario:**

| Step | Actor | System |
|------|-------|--------|
| 1 | User navigates to `/api-keys` | |
| 2 | | System displays API key list |
| 3 | User clicks "Create New Key" | |
| 4 | | System displays create key modal |
| 5 | User enters key name | |
| 6 | User optionally enters description | |
| 7 | User selects scopes (realtime, billing, admin) | |
| 8 | User selects expiration (30d, 90d, 1y, never) | |
| 9 | User selects rate limit tier | |
| 10 | User clicks "Create" | |
| 11 | | System validates all fields |
| 12 | | System sends create request to backend |
| 13 | | Backend generates cryptographically secure key |
| 14 | | Backend hashes key for storage |
| 15 | | Backend stores key metadata |
| 16 | | Backend returns full key (only time) |
| 17 | | System displays key in modal with copy button |
| 18 | | System displays warning: "This key will not be shown again" |
| 19 | User copies key | |
| 20 | User clicks "Done" | |
| 21 | | System closes modal |
| 22 | | System refreshes key list |

**Sequence Diagram - API Key Creation:**

```
┌─────┐          ┌─────────┐          ┌──────────┐          ┌──────────┐
│User │          │Frontend │          │ Backend  │          │PostgreSQL│
└──┬──┘          └────┬────┘          └────┬─────┘          └────┬─────┘
   │                  │                    │                     │
   │ Click Create Key │                    │                     │
   │─────────────────>│                    │                     │
   │                  │                    │                     │
   │                  │ Display modal      │                     │
   │<─────────────────│                    │                     │
   │                  │                    │                     │
   │ Fill form        │                    │                     │
   │─────────────────>│                    │                     │
   │                  │                    │                     │
   │ Click Create     │                    │                     │
   │─────────────────>│                    │                     │
   │                  │                    │                     │
   │                  │ Validate form      │                     │
   │                  │────────┐           │                     │
   │                  │        │           │                     │
   │                  │<───────┘           │                     │
   │                  │                    │                     │
   │                  │ POST /api/v1/keys  │                     │
   │                  │───────────────────>│                     │
   │                  │                    │                     │
   │                  │                    │ Generate key        │
   │                  │                    │────────┐            │
   │                  │                    │        │            │
   │                  │                    │<───────┘            │
   │                  │                    │                     │
   │                  │                    │ Hash key            │
   │                  │                    │────────┐            │
   │                  │                    │        │            │
   │                  │                    │<───────┘            │
   │                  │                    │                     │
   │                  │                    │ INSERT api_keys     │
   │                  │                    │────────────────────>│
   │                  │                    │                     │
   │                  │                    │ Success             │
   │                  │                    │<────────────────────│
   │                  │                    │                     │
   │                  │ {key: "avb_xxx...", id: "..."}           │
   │                  │<───────────────────│                     │
   │                  │                    │                     │
   │                  │ Display key modal  │                     │
   │<─────────────────│                    │                     │
   │                  │                    │                     │
   │ Copy key         │                    │                     │
   │─────────────────>│                    │                     │
   │                  │                    │                     │
   │                  │ Copy to clipboard  │                     │
   │                  │────────┐           │                     │
   │                  │        │           │                     │
   │                  │<───────┘           │                     │
   │                  │                    │                     │
   │ Click Done       │                    │                     │
   │─────────────────>│                    │                     │
   │                  │                    │                     │
   │                  │ Close modal        │                     │
   │<─────────────────│                    │                     │
   │                  │                    │                     │
```


### 4.4 Voice Session Flow

#### 4.4.1 Use Case: UC-VOICE-001 - Start Voice Session with AgentVoiceBox

**Primary Actor:** OPERATOR or higher  
**Preconditions:** Voice provider configured as "agentvoicebox", valid API key  
**Postconditions:** Active voice session with bidirectional audio  

**Main Success Scenario:**

| Step | Actor | System |
|------|-------|--------|
| 1 | User navigates to voice interface | |
| 2 | | System checks voice provider configuration |
| 3 | | System displays voice controls |
| 4 | User clicks "Start Session" | |
| 5 | | System requests microphone permission |
| 6 | User grants microphone permission | |
| 7 | | System initializes AudioContext (24kHz) |
| 8 | | System establishes WebSocket to AgentVoiceBox |
| 9 | | System sends session.update with voice config |
| 10 | | AgentVoiceBox confirms session ready |
| 11 | | System displays "Listening" state |
| 12 | | System starts streaming audio to AgentVoiceBox |
| 13 | User speaks | |
| 14 | | AgentVoiceBox detects speech start (VAD) |
| 15 | | System receives input_audio_buffer.speech_started |
| 16 | | System updates UI to "Listening" with audio level |
| 17 | User stops speaking | |
| 18 | | AgentVoiceBox detects speech end |
| 19 | | System receives input_audio_buffer.speech_stopped |
| 20 | | System updates UI to "Processing" |
| 21 | | AgentVoiceBox processes speech (STT → LLM → TTS) |
| 22 | | System receives conversation.item.created with transcript |
| 23 | | System displays user transcript |
| 24 | | System receives response.audio.delta (streaming audio) |
| 25 | | System plays audio through speakers |
| 26 | | System updates UI to "Speaking" |
| 27 | | System receives response.done |
| 28 | | System displays assistant transcript |
| 29 | | System returns to "Listening" state |

**State Diagram - Voice Session:**

```
                              ┌─────────────────┐
                              │                 │
                              │      IDLE       │
                              │                 │
                              └────────┬────────┘
                                       │
                                       │ Start session
                                       ▼
                              ┌─────────────────┐
                              │                 │
                              │   CONNECTING    │
                              │                 │
                              └────────┬────────┘
                                       │
                                       │ Connected
                                       ▼
┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐
│                 │           │                 │           │                 │
│    SPEAKING     │◄──────────│    LISTENING    │──────────►│   PROCESSING    │
│                 │           │                 │           │                 │
└────────┬────────┘           └────────┬────────┘           └────────┬────────┘
         │                             │                             │
         │                             │                             │
         │    Response done            │                             │
         └─────────────────────────────┤                             │
                                       │                             │
                                       │    Transcription done       │
                                       │◄────────────────────────────┘
                                       │
                                       │ End session / Error
                                       ▼
                              ┌─────────────────┐
                              │                 │
                              │      IDLE       │
                              │                 │
                              └─────────────────┘
```


### 4.5 Theme Application Flow

#### 4.5.1 Use Case: UC-THEME-001 - Apply Theme

**Primary Actor:** Authenticated User  
**Preconditions:** User is authenticated, theme exists  
**Postconditions:** Theme applied to UI, persisted to storage  

**Main Success Scenario:**

| Step | Actor | System |
|------|-------|--------|
| 1 | User navigates to `/themes` | |
| 2 | | System displays theme gallery |
| 3 | User clicks "Apply" on desired theme | |
| 4 | | System validates theme (26 variables, no XSS) |
| 5 | | System injects CSS custom properties to :root |
| 6 | | System updates all Shadow DOM components |
| 7 | | System persists theme to localStorage |
| 8 | | System sends theme preference to backend |
| 9 | | System emits theme.changed WebSocket event |
| 10 | | System displays success notification |

**Activity Diagram - Theme Validation:**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           THEME VALIDATION FLOW                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Receive Theme JSON │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Parse JSON Syntax   │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
            ┌──────────────┐               ┌──────────────┐
            │ Valid JSON   │               │ Invalid JSON │
            └──────┬───────┘               └──────┬───────┘
                   │                               │
                   ▼                               ▼
        ┌─────────────────────┐           ┌──────────────┐
        │ Validate Schema     │           │ Return Error │
        │ (name, version,     │           │ "Invalid JSON│
        │  author, variables) │           │  syntax"     │
        └──────────┬──────────┘           └──────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
        ▼                     ▼
┌──────────────┐      ┌──────────────┐
│ Schema Valid │      │Schema Invalid│
└──────┬───────┘      └──────┬───────┘
       │                     │
       ▼                     ▼
┌─────────────────┐   ┌──────────────┐
│ Check 26 vars   │   │ Return Error │
│ present         │   │ "Missing     │
└────────┬────────┘   │  required    │
         │            │  fields"     │
         │            └──────────────┘
┌────────┴────────┐
│                 │
▼                 ▼
┌────────┐  ┌─────────────┐
│All 26  │  │Missing vars │
│present │  └──────┬──────┘
└───┬────┘         │
    │              ▼
    │        ┌──────────────┐
    │        │ Return Error │
    │        │ "Missing:    │
    │        │  var1, var2" │
    │        └──────────────┘
    ▼
┌─────────────────┐
│ XSS Scan        │
│ (url, javascript│
│  expression)    │
└────────┬────────┘
         │
┌────────┴────────┐
│                 │
▼                 ▼
┌────────┐  ┌─────────────┐
│Clean   │  │XSS Detected │
└───┬────┘  └──────┬──────┘
    │              │
    │              ▼
    │        ┌──────────────┐
    │        │ Return Error │
    │        │ "Security    │
    │        │  violation"  │
    │        └──────────────┘
    ▼
┌─────────────────┐
│ Contrast Check  │
│ (WCAG AA 4.5:1) │
└────────┬────────┘
         │
┌────────┴────────┐
│                 │
▼                 ▼
┌────────┐  ┌─────────────┐
│Pass    │  │Fail         │
└───┬────┘  └──────┬──────┘
    │              │
    │              ▼
    │        ┌──────────────┐
    │        │ Return       │
    │        │ Warning      │
    │        │ (non-block)  │
    │        └──────┬───────┘
    │              │
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Theme Valid  │
    │ Apply Theme  │
    └──────────────┘
```


---

## 5. External Interface Requirements (Detailed)

### 5.1 API Contracts

#### 5.1.1 Authentication API

##### POST /api/v1/auth/token

**Purpose:** Exchange authorization code for tokens

**Request:**
```json
{
  "grant_type": "authorization_code",
  "code": "string",
  "redirect_uri": "string",
  "code_verifier": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "id_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | invalid_grant | Invalid authorization code |
| 400 | invalid_request | Missing required parameter |
| 401 | unauthorized | Invalid client credentials |

##### POST /api/v1/auth/refresh

**Purpose:** Refresh access token

**Request:**
```json
{
  "grant_type": "refresh_token",
  "refresh_token": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

##### POST /api/v1/auth/logout

**Purpose:** Invalidate tokens

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Response (204 No Content)**

---

#### 5.1.2 Tenant API

##### GET /api/v1/admin/tenants

**Purpose:** List all tenants (SYSADMIN only)

**Request Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| page | integer | No | Page number (default: 1) |
| per_page | integer | No | Items per page (default: 20, max: 100) |
| status | string | No | Filter by status (active, suspended, deleted) |
| tier | string | No | Filter by tier (free, pro, enterprise) |
| search | string | No | Search by name |
| sort_by | string | No | Sort field (name, created_at, sessions) |
| sort_order | string | No | Sort order (asc, desc) |

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "string",
      "slug": "string",
      "tier": "free|pro|enterprise",
      "status": "active|suspended|deleted",
      "billing_id": "string",
      "settings": {},
      "stats": {
        "user_count": 0,
        "session_count": 0,
        "api_key_count": 0
      },
      "created_at": "ISO8601",
      "updated_at": "ISO8601"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

##### POST /api/v1/admin/tenants

**Purpose:** Create new tenant (SYSADMIN only)

**Request:**
```json
{
  "name": "string (2-100 chars)",
  "slug": "string (3-50 chars, lowercase alphanumeric + hyphens)",
  "tier": "free|pro|enterprise",
  "admin": {
    "email": "string (valid email)",
    "name": "string (2-100 chars)"
  },
  "send_welcome_email": true
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "string",
  "slug": "string",
  "tier": "string",
  "status": "active",
  "admin": {
    "id": "uuid",
    "email": "string",
    "name": "string"
  },
  "created_at": "ISO8601"
}
```

**Error Responses:**

| Status | Code | Description |
|--------|------|-------------|
| 400 | validation_error | Invalid request body |
| 409 | slug_exists | Slug already in use |
| 403 | forbidden | Insufficient permissions |

