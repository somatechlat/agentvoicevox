# Design Document: AgentVoiceBox Multi-Portal Platform

## Overview

This document describes the technical design for a complete, production-ready multi-portal SaaS platform for AgentVoiceBox. The platform serves three distinct user audiences through dedicated portal experiences:

1. **SaaS Admin Portal** (`/admin/*`) - Platform operators managing all tenants
2. **Customer Portal** (`/dashboard/*`) - Organization admins managing their tenant
3. **User Portal** (`/app/*`) - End users with limited permissions

All portals share a single Next.js codebase with role-based routing and navigation.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PORTAL FRONTEND (Next.js)                       │
│  ┌─────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ SaaS Admin  │  │ Customer Portal │  │      User Portal            │  │
│  │  /admin/*   │  │  /dashboard/*   │  │       /app/*                │  │
│  └──────┬──────┘  └────────┬────────┘  └─────────────┬───────────────┘  │
│         │                  │                         │                  │
│         └──────────────────┼─────────────────────────┘                  │
│                            │                                            │
│                   ┌────────▼────────┐                                   │
│                   │  AuthContext    │                                   │
│                   │  (Keycloak JWT) │                                   │
│                   └────────┬────────┘                                   │
└────────────────────────────┼────────────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   Portal API    │
                    │   (FastAPI)     │
                    │   Port 25001    │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐       ┌──────▼──────┐     ┌──────▼──────┐
    │Keycloak │       │ PostgreSQL  │     │    Lago     │
    │  Auth   │       │   + Redis   │     │   Billing   │
    │  25004  │       │ 25002/25003 │     │    25005    │
    └─────────┘       └─────────────┘     └─────────────┘
```

## Components and Interfaces

### 1. Portal Frontend (Next.js)

**Technology:** Next.js 14, TypeScript, Tailwind CSS, Radix UI, TanStack Query

**Route Structure:**
```
src/app/
├── (auth)/
│   └── login/page.tsx           # Keycloak login redirect
├── admin/                        # SaaS Admin Portal
│   ├── layout.tsx               # Admin layout with full nav
│   ├── page.tsx                 # Admin dashboard
│   ├── tenants/page.tsx         # Tenant management
│   ├── billing/page.tsx         # Global billing
│   ├── plans/page.tsx           # Plan management
│   ├── monitoring/page.tsx      # System monitoring
│   ├── audit/page.tsx           # Audit logs
│   └── users/page.tsx           # User management
├── dashboard/                    # Customer Portal
│   ├── layout.tsx               # Customer layout
│   ├── page.tsx                 # Customer dashboard
│   ├── sessions/page.tsx        # Voice sessions
│   ├── projects/page.tsx        # Projects
│   ├── api-keys/page.tsx        # API keys
│   ├── usage/page.tsx           # Usage analytics
│   ├── billing/page.tsx         # Billing
│   ├── team/page.tsx            # Team management
│   ├── settings/page.tsx        # Settings
│   └── voice/page.tsx           # Voice configuration
├── app/                          # User Portal
│   ├── layout.tsx               # User layout (limited nav)
│   ├── page.tsx                 # User dashboard
│   ├── sessions/page.tsx        # View-only sessions
│   ├── api-keys/page.tsx        # View-only keys
│   └── settings/page.tsx        # Personal settings
└── layout.tsx                    # Root layout
```

### 2. Authentication Context

**File:** `src/contexts/AuthContext.tsx`

```typescript
interface User {
  id: string;
  email: string;
  name: string;
  tenantId: string;
  roles: string[];           // ['saas_admin', 'tenant_admin', 'user']
  permissions: string[];     // ['tenants:manage', 'billing:view', etc.]
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: () => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: string) => boolean;
  hasPermission: (permission: string) => boolean;
}
```

### 3. Portal API (FastAPI)

**Endpoints by Portal:**

**SaaS Admin Endpoints:**
```
GET    /api/v1/admin/dashboard          # Platform metrics
GET    /api/v1/admin/tenants            # List all tenants
GET    /api/v1/admin/tenants/:id        # Tenant details
POST   /api/v1/admin/tenants/:id/suspend
POST   /api/v1/admin/tenants/:id/reactivate
POST   /api/v1/admin/tenants/:id/impersonate
GET    /api/v1/admin/billing            # Global billing metrics
GET    /api/v1/admin/plans              # All plans
POST   /api/v1/admin/plans              # Create plan
GET    /api/v1/admin/monitoring         # System health
GET    /api/v1/admin/audit              # Audit logs
GET    /api/v1/admin/users              # All users
```

**Customer Endpoints:**
```
GET    /api/v1/dashboard                # Tenant dashboard
GET    /api/v1/sessions                 # Tenant sessions
GET    /api/v1/projects                 # Tenant projects
GET    /api/v1/keys                     # Tenant API keys
POST   /api/v1/keys                     # Create key
POST   /api/v1/keys/:id/rotate          # Rotate key
DELETE /api/v1/keys/:id                 # Revoke key
GET    /api/v1/usage                    # Usage metrics
GET    /api/v1/billing/subscription     # Subscription
POST   /api/v1/billing/subscription     # Change plan
GET    /api/v1/billing/invoices         # Invoices
GET    /api/v1/team/members             # Team members
POST   /api/v1/team/invite              # Invite member
GET    /api/v1/settings/profile         # Org profile
GET    /api/v1/settings/webhooks        # Webhooks
GET    /api/v1/voice/config             # Voice settings
```

### 4. Role-Based Navigation

**Navigation Configuration:**
```typescript
const navigationConfig = {
  saas_admin: [
    { name: 'Dashboard', href: '/admin', icon: Home },
    { name: 'Tenants', href: '/admin/tenants', icon: Building },
    { name: 'Billing', href: '/admin/billing', icon: CreditCard },
    { name: 'Plans', href: '/admin/plans', icon: Package },
    { name: 'Monitoring', href: '/admin/monitoring', icon: Activity },
    { name: 'Audit', href: '/admin/audit', icon: FileText },
    { name: 'Users', href: '/admin/users', icon: Users },
  ],
  tenant_admin: [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Sessions', href: '/dashboard/sessions', icon: MessageSquare },
    { name: 'Projects', href: '/dashboard/projects', icon: Folder },
    { name: 'API Keys', href: '/dashboard/api-keys', icon: Key },
    { name: 'Usage', href: '/dashboard/usage', icon: BarChart },
    { name: 'Billing', href: '/dashboard/billing', icon: CreditCard },
    { name: 'Team', href: '/dashboard/team', icon: Users },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
    { name: 'Voice', href: '/dashboard/voice', icon: Mic },
  ],
  user: [
    { name: 'Dashboard', href: '/app', icon: Home },
    { name: 'Sessions', href: '/app/sessions', icon: MessageSquare, permission: 'sessions:view' },
    { name: 'API Keys', href: '/app/api-keys', icon: Key, permission: 'api_keys:view' },
    { name: 'Settings', href: '/app/settings', icon: Settings },
  ],
};
```

## Data Models

### PostgreSQL Schema

```sql
-- Tenants
CREATE TABLE tenants (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'active', -- active, suspended, deleted
  plan_code VARCHAR(50) DEFAULT 'free',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Projects
CREATE TABLE projects (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  name VARCHAR(255) NOT NULL,
  environment VARCHAR(50) DEFAULT 'development', -- production, staging, development
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys
CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  project_id UUID REFERENCES projects(id),
  name VARCHAR(255) NOT NULL,
  key_hash VARCHAR(255) NOT NULL,
  prefix VARCHAR(20) NOT NULL,
  scopes TEXT[] DEFAULT '{}',
  is_active BOOLEAN DEFAULT true,
  expires_at TIMESTAMPTZ,
  last_used_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sessions
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  api_key_id UUID REFERENCES api_keys(id),
  status VARCHAR(50) DEFAULT 'active', -- active, closed
  model VARCHAR(100) DEFAULT 'ovos-voice-1',
  voice VARCHAR(100) DEFAULT 'am_onyx',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  closed_at TIMESTAMPTZ,
  duration_seconds INTEGER
);

-- Conversation Items
CREATE TABLE conversation_items (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id UUID NOT NULL REFERENCES sessions(id),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  role VARCHAR(50) NOT NULL, -- user, assistant, system
  content JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID REFERENCES tenants(id),
  actor_id VARCHAR(255) NOT NULL,
  action VARCHAR(100) NOT NULL,
  resource_type VARCHAR(100) NOT NULL,
  resource_id VARCHAR(255),
  details JSONB,
  ip_address INET,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Webhooks
CREATE TABLE webhooks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id),
  url VARCHAR(2048) NOT NULL,
  events TEXT[] NOT NULL,
  secret VARCHAR(255) NOT NULL,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### TypeScript Interfaces

```typescript
// Tenant
interface Tenant {
  id: string;
  name: string;
  email: string;
  status: 'active' | 'suspended' | 'deleted';
  planCode: string;
  createdAt: string;
}

// API Key
interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  scopes: string[];
  isActive: boolean;
  expiresAt?: string;
  lastUsedAt?: string;
  createdAt: string;
}

// Session
interface Session {
  id: string;
  status: 'active' | 'closed';
  model: string;
  voice: string;
  createdAt: string;
  closedAt?: string;
  durationSeconds?: number;
}

// Usage Metrics
interface UsageMetrics {
  apiRequests: number;
  audioMinutesInput: number;
  audioMinutesOutput: number;
  llmTokensInput: number;
  llmTokensOutput: number;
  periodStart: string;
  periodEnd: string;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Dashboard Data Aggregation
*For any* set of tenants and sessions in the database, the admin dashboard metrics SHALL equal the sum of individual tenant metrics.
**Validates: Requirements A1.1**

### Property 2: Auto-Refresh Without Reload
*For any* dashboard view, after the configured refresh interval (30s admin, 60s customer), the displayed data SHALL update without triggering a full page reload.
**Validates: Requirements A1.5, B1.5**

### Property 3: Tenant Suspension Cascade
*For any* tenant that is suspended, all associated API keys SHALL be invalidated and all active sessions SHALL be terminated.
**Validates: Requirements A2.4**

### Property 4: API Key Secret Display Once
*For any* newly created API key, the full secret SHALL be displayed exactly once and the stored value SHALL be a hash (not equal to the original secret).
**Validates: Requirements B4.2**

### Property 5: API Key Rotation Grace Period
*For any* rotated API key, both the old and new keys SHALL authenticate successfully during the 24-hour grace period.
**Validates: Requirements B4.3**

### Property 6: API Key Revocation Immediate
*For any* revoked API key, authentication attempts SHALL fail immediately after revocation.
**Validates: Requirements B4.4**

### Property 7: Role-Based Dashboard Routing
*For any* authenticated user, the initial redirect SHALL be to the appropriate dashboard based on their highest role (saas_admin → /admin, tenant_admin → /dashboard, user → /app).
**Validates: Requirements D1.2**

### Property 8: Permission-Based Navigation
*For any* authenticated user, the sidebar navigation SHALL display only items for which the user has the required permission.
**Validates: Requirements D2.1**

### Property 9: No Mock Data in Production
*For any* API call made by the portal, the request SHALL be sent to a real Portal API endpoint (no mock data fallbacks).
**Validates: Requirements E1.2**

### Property 10: Tenant Data Isolation
*For any* database query, the results SHALL only include records where tenant_id matches the authenticated user's tenant.
**Validates: Requirements E4.2**

### Property 11: Usage Metering Accuracy
*For any* API request, the system SHALL record a usage event in Lago with the correct tenant_id and metric code.
**Validates: Requirements E5.1**

## Error Handling

### API Error Response Format
```typescript
interface ApiError {
  error: {
    type: string;      // 'authentication_error', 'validation_error', etc.
    code: string;      // 'invalid_token', 'missing_field', etc.
    message: string;   // Human-readable message
    param?: string;    // Field that caused the error
  };
}
```

### Error Handling Strategy
1. **Network Errors**: Display offline indicator, queue actions for retry
2. **Authentication Errors**: Redirect to login with session expired message
3. **Authorization Errors**: Display 403 page with permission guidance
4. **Validation Errors**: Display inline field errors
5. **Server Errors**: Display error toast with retry option

## Testing Strategy

### Unit Testing (Vitest)
- Component rendering tests
- Hook behavior tests
- Utility function tests

### Property-Based Testing (fast-check)
- Dashboard aggregation correctness
- Permission filtering correctness
- API key hashing correctness
- Tenant isolation correctness

### Integration Testing (Playwright)
- Full authentication flow
- Role-based navigation
- CRUD operations
- Real API integration

### Test Configuration
```typescript
// vitest.config.ts
export default defineConfig({
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/__tests__/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
  },
});
```

### Property Test Example
```typescript
// Feature: portal-admin-complete, Property 10: Tenant Data Isolation
describe('Property 10: Tenant Data Isolation', () => {
  it('should only return data for authenticated tenant', () => {
    fc.assert(
      fc.property(
        fc.array(tenantArb),
        fc.uuid(),
        (tenants, authenticatedTenantId) => {
          const results = filterByTenant(tenants, authenticatedTenantId);
          return results.every(t => t.tenantId === authenticatedTenantId);
        }
      ),
      { numRuns: 100 }
    );
  });
});
```
