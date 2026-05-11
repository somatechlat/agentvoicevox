# AgentVoiceBox Portal Frontend

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11

## 1. Purpose
The portal frontend is the browser administration interface for AgentVoiceBox.

## 2. Implemented Technology
- Lit 3 Web Components.
- TypeScript.
- Vite.
- Playwright E2E tests.
- API services in `src/services`.

This frontend is not Next.js, React, or Alpine.js.

## 3. Implemented Source Structure
- `src/main.ts`: application entrypoint.
- `src/components`: shared custom elements.
- `src/views`: route-level custom elements.
- `src/services`: API, auth, admin, voice, permissions, formatting, serialization, JWT utilities.
- `src/utils/i18n.ts`: local i18n utility.
- `src/styles/globals.css`: global styling.
- `e2e`: Playwright tests.

## 4. Runtime Configuration
Primary local URL: http://localhost:65027.
Primary API target: http://localhost:65020.

## 5. Commands
```bash
bun install
bun run dev
bun run build
bun run type-check
bun run test:e2e
```

## 6. Requirements
- UI changes shall use Lit custom elements.
- User-facing API calls shall go through service modules where practical.
- Authentication behavior shall match `src/services/auth-service.ts`.
- Documentation shall not describe React/Next.js routes as active implementation.
