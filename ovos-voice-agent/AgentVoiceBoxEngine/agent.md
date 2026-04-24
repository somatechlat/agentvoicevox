# Agent Directives & Vibe Coding Guidelines

If you are an AI Agent operating within this codebase, you MUST adhere to the following rules at all times. This project enforces a strictly monitored "Vibe Coding" framework.

## 1. Zero-Mock Policy
- **NO MOCKS:** Do not use `unittest.mock`, fake responses, or `TODO` placeholders in production logic.
- **REAL DATA:** Always test against the actual `ovos-bus` and `PostgreSQL` instances.

## 2. API Framework Rule
- **DJANGO NINJA ONLY:** All REST API endpoints must be implemented using `django-ninja` in the `backend/apps/voice/api.py` (or related) files.
- **NO FASTAPI:** FastAPI and Starlette are explicitly forbidden.

## 3. Frontend UI Rule
- **LIT 3 WEB COMPONENTS ONLY:** All UI elements in `portal-frontend/` must be Lit 3 custom elements.
- **NO ALPINE.JS:** Do not use Alpine.js.
- **NO TAILWIND (Unless requested):** We use Vanilla CSS for maximum flexibility.
- **AESTHETICS:** Maintain modern SaaS-grade aesthetics (glassmorphism, clean typography, tooltips).

## 4. Internationalization (i18n)
- All UI strings must be routed through the `t()` function located in `portal-frontend/src/utils/i18n.ts`. Do not hardcode raw strings into Lit render blocks.

## 5. Architectural Sovereignty
- **10GB HARD LIMIT:** Do not exceed the allocated container memory limits defined in `docker-compose.yml`. The total cluster is restricted to ~10GB.
- **PORT POLICY:** All services must operate strictly within the `65000-65099` port range.

*Violation of these rules will result in immediate rejection of the patch.*
