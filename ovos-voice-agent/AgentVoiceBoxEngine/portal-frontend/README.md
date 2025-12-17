<p align="center">
  <h1 align="center">AgentVoiceVox Portal</h1>
  <p align="center">
    <strong>Self-Service SaaS Portal for AgentVoiceVox</strong>
  </p>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Next.js-14-black.svg" alt="Next.js"/>
  <img src="https://img.shields.io/badge/TypeScript-5.0-blue.svg" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Tailwind-3.4-38bdf8.svg" alt="Tailwind"/>
  <img src="https://img.shields.io/badge/Tests-185%20passing-green.svg" alt="Tests"/>
</p>

---

## Overview

The AgentVoiceVox Portal is a dual-portal SaaS application providing:

- **Customer Portal**: Dashboard, API keys, billing, team management
- **Admin Portal**: Tenant management, billing admin, system monitoring

Built with Next.js 14, TypeScript, and Tailwind CSS with full accessibility (WCAG 2.1 AA) compliance.

---

## Features

### Customer Portal
- 📊 **Dashboard** - Real-time usage metrics, billing summary, system health
- 🔑 **API Keys** - Create, rotate, revoke keys with scope management
- 💳 **Billing** - Plan comparison, invoices, payment methods (Stripe)
- 👥 **Team** - Invite members, assign roles, manage permissions
- ⚙️ **Settings** - Profile, notifications, webhooks, security

### Admin Portal
- 📈 **Dashboard** - Platform metrics, revenue, alerts
- 🏢 **Tenants** - Search, filter, suspend, impersonate
- 💰 **Billing** - Invoices, refunds, credits, revenue reports
- 📋 **Plans** - Create, edit, deprecate pricing plans
- 🖥️ **Monitoring** - Service health, queues, database metrics
- 📝 **Audit** - Complete audit log with search and export

### Design System
- 🌙 **Dark/Light/System** themes with smooth transitions
- 🎨 **Verve-inspired** design language
- ♿ **WCAG 2.1 AA** accessibility compliance
- 📱 **Responsive** design for all screen sizes

---

## Quick Start

### Prerequisites
- Node.js 20+
- npm or yarn

### Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Open http://localhost:3000
```

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm run start
```

---

## Project Structure

```
portal-frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── (auth)/             # Auth pages (login, signup)
│   │   ├── (customer)/         # Customer portal pages
│   │   │   ├── dashboard/
│   │   │   ├── api-keys/
│   │   │   ├── billing/
│   │   │   ├── team/
│   │   │   └── settings/
│   │   └── (admin)/            # Admin portal pages
│   │       ├── admin/
│   │       ├── tenants/
│   │       ├── billing/
│   │       ├── plans/
│   │       ├── monitoring/
│   │       └── audit/
│   ├── components/
│   │   ├── ui/                 # Radix-based primitives
│   │   ├── layout/             # Layout components
│   │   └── auth/               # Auth components
│   ├── services/               # API clients, utilities
│   ├── contexts/               # React contexts
│   └── __tests__/              # Test suites
│       ├── unit/               # Unit tests
│       └── properties/         # Property-based tests
├── public/                     # Static assets
└── e2e/                        # Playwright E2E tests
```

---

## Testing

### Run All Tests

```bash
# Single run
npm run test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage
```

### Test Stack
- **Vitest** - Fast unit test runner
- **Testing Library** - React component testing
- **fast-check** - Property-based testing (26 properties)

### Test Coverage
- 185 tests passing
- 26 correctness properties verified
- 100+ iterations per property test
  
---

## Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server |
| `npm run build` | Production build |
| `npm run start` | Start production server |
| `npm run lint` | Run ESLint |
| `npm run type-check` | TypeScript type checking |
| `npm run test` | Run tests (single run) |
| `npm run test:watch` | Run tests in watch mode |
| `npm run test:coverage` | Generate coverage report |

---

## Environment Variables

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:25001
NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:25004
NEXT_PUBLIC_KEYCLOAK_REALM=agentvoicevox
NEXT_PUBLIC_KEYCLOAK_CLIENT_ID=agentvoicevox-portal
```

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript (strict mode) |
| Styling | Tailwind CSS 3.4 |
| Components | Radix UI primitives |
| State | TanStack React Query |
| Forms | react-hook-form + zod |
| Charts | Recharts |
| Testing | Vitest + Testing Library + fast-check |
| E2E | Playwright |

---

## License

Apache License 2.0 - see [LICENSE](../LICENSE) for details.
