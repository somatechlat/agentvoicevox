# AgentVoiceBox Portal Frontend

**Lit 3 + Bun SaaS Portal for AgentVoiceBox**

![Lit](https://img.shields.io/badge/Lit-3.3.2-324fff.svg)
![Bun](https://img.shields.io/badge/Bun-1.3.5-f9f1e1.svg)
![Vite](https://img.shields.io/badge/Vite-7.3.0-646cff.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.6.2-blue.svg)

---

## Overview

The AgentVoiceBox Portal is a self-service SaaS frontend built with:

- **Lit 3.3.2** - Lightweight web components
- **Bun 1.3.5** - High-performance JavaScript runtime
- **Vite 7.3.0** - Fast build tool with HMR
- **Tailwind CSS 3.4.13** - Utility-first CSS framework
- **Playwright 1.57.0** - E2E testing

---

## Quick Start

### Prerequisites
- Bun 1.3.5+ (https://bun.sh)

### Development

```bash
# Install dependencies
bun install

# Start development server (port 65027)
bun run dev

# Open http://localhost:65027
```

### Production Build

```bash
# Build for production
bun run build

# Preview production build
bun run preview
```

---

## Project Structure

```
portal-frontend/
├── src/
│   ├── components/           # Lit web components
│   │   ├── saas-layout.ts
│   │   ├── saas-glass-modal.ts
│   │   ├── saas-status-dot.ts
│   │   ├── saas-infra-card.ts
│   │   └── saas-config-modal.ts
│   ├── views/                # Page-level components
│   │   ├── view-login.ts
│   │   ├── view-setup.ts
│   │   └── view-auth-callback.ts
│   ├── services/             # API clients
│   │   ├── api-client.ts
│   │   ├── auth-service.ts
│   │   ├── admin-api.ts
│   │   ├── voice-api.ts
│   │   └── permissions.ts
│   └── main.ts               # Entry point
├── e2e/                      # Playwright E2E tests
├── index.html                # HTML entry
├── vite.config.ts            # Vite configuration
├── tailwind.config.js        # Tailwind configuration
├── tsconfig.json             # TypeScript configuration
├── package.json              # Dependencies (Bun)
└── bun.lock                  # Bun lockfile (ONLY lockfile)
```

---

## Scripts

| Command | Description |
|---------|-------------|
| `bun run dev` | Start dev server (port 65027) |
| `bun run build` | Production build |
| `bun run preview` | Preview production build |
| `bun run lint` | Run ESLint |
| `bun run type-check` | TypeScript type checking |
| `bun run test:e2e` | Run Playwright E2E tests |
| `bun run test:e2e:ui` | Run Playwright with UI |

---

## E2E Testing

```bash
# Install Playwright browsers
bunx playwright install

# Run all E2E tests
bun run test:e2e

# Run with UI mode
bun run test:e2e:ui

# Run specific test
bunx playwright test e2e/signup.spec.ts --project=chromium
```

---

## Environment Variables

```bash
# Django API Backend
VITE_API_URL=http://localhost:65020

# Keycloak Authentication
VITE_KEYCLOAK_URL=http://localhost:65006
VITE_KEYCLOAK_REALM=agentvoicebox
VITE_KEYCLOAK_CLIENT_ID=agentvoicebox-portal
```

---

## Tech Stack

| Category | Technology |
|----------|------------|
| Runtime | Bun 1.3.5 |
| Framework | Lit 3.3.2 |
| Router | @lit-labs/router 0.1.4 |
| Build | Vite 7.3.0 |
| Styling | Tailwind CSS 3.4.13 |
| E2E Testing | Playwright 1.57.0 |
| Type System | TypeScript 5.6.2 |

---

## VIBE Compliance

This frontend adheres to:
- **Rule 217**: Bun Frontend Sovereignty Mandate
- **Rule 95**: Bun Runtime Mandate (Zero npm Policy)
- **Rule 119**: Bun-Only Execution Layer

**Prohibited:**
- ❌ `npm install` / `npm run` / `npx`
- ❌ `package-lock.json` / `yarn.lock`
- ❌ `@types/node`
- ❌ Node.js base images

---

## License

Apache License 2.0
