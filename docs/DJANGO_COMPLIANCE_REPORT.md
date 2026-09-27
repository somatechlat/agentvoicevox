# Django Compliance Report

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11

## 1. Purpose
This report records whether the repository follows the project rule that application backend code uses Django, Django Ninja, Django Channels, and Django ORM.

## 2. Findings
- REST API implementation uses Django Ninja through `backend/apps/core/api.py`.
- WebSocket implementation uses Django Channels through `backend/config/asgi.py` and `backend/realtime/routing.py`.
- Domain data models use Django ORM under `backend/apps/*/models.py`.
- The active frontend uses Lit 3, not React or Next.js.
- The active backend is not Flask or FastAPI.

## 3. Exceptions And Notes
- `uvicorn` is present as an ASGI server dependency. That is not FastAPI usage.
- Historical planning docs were removed from the repository; code and the current SRS are authoritative.
- Generated, cached, or local environment artifacts are not evidence of application architecture.

## 4. Conclusion
The active application code is aligned with the Django/Ninja/Channels/ORM architecture requirement. Documentation must continue to reject stale Flask/FastAPI/React/Next.js claims unless explicitly describing historical plans.
