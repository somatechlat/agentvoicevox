# Agent Directives Specification

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11
**Source of truth:** Current AgentVoiceBox source code.

## 1. Purpose
This document defines implementation rules for agents working in this codebase. It uses ISO-style structure for clarity and must remain aligned with the active Django/Lit implementation.

## 2. Architectural Rules
- REST APIs shall use Django Ninja.
- REST routers shall live in the relevant Django app and be registered through `backend/apps/core/api.py`.
- WebSocket handlers shall use Django Channels and be routed through `backend/realtime/routing.py`.
- UI code shall use Lit 3 Web Components under `portal-frontend/`.
- Database models shall use Django ORM and Django migrations.

## 3. Prohibited Active-Code Patterns
- Do not add FastAPI, Flask, or Starlette application services.
- Do not add React, Next.js, or Alpine.js portal UI code.
- Do not add SQLAlchemy models for active SaaS platform data.
- Do not document unimplemented routes or compatibility claims as implemented.

## 4. Runtime Constraints
- The primary local compose stack targets the 10 GB memory budget documented in `docker-compose.yml`.
- Host-exposed ports in the primary local stack shall stay in the `65000-65099` range unless the compose file and documentation are deliberately revised together.
- OVOS may use internal container ports such as `8181`; public documentation shall distinguish internal ports from host-exposed ports.

## 5. Documentation Rules
- Code is the source of truth.
- SRS files must be updated in the same change as architecture-affecting code.
- Experimental functionality must be labeled experimental.
- Optional infrastructure must be labeled optional.
