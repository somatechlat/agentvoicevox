# AgentVoiceBox Roadmap

**Document status:** Code-aligned planning baseline
**Revision date:** 2026-05-11

## 1. Purpose
This roadmap lists future work without describing it as implemented.

## 2. Current Baseline
Implemented baseline is Django Ninja `/api/v2`, Django Channels `/ws/v2`, experimental `/ws/v1/realtime`, Lit 3 portal, PostgreSQL/Redis, and OVOS bus integration.

## 3. Near-Term Priorities
1. Remove committed local secrets, auth states, generated caches, screenshots, and build artifacts from source control.
2. Run backend pytest/property tests and frontend type-check/build/Playwright tests to establish a verified baseline.
3. Complete or explicitly scope down the experimental OpenAI-like realtime gateway.
4. Reconcile optional worker and infrastructure manifests with the primary compose stack.
5. Harden production authentication so `AUTH_BYPASS=true` remains local-only.
6. Update generated Sphinx API pages after code changes.

## 4. Deferred Work
- Full OpenAI Realtime REST/WebSocket compatibility is not claimed until implemented and tested.
- WebRTC/SIP/call endpoints are not claimed until code exists and routes are registered.
