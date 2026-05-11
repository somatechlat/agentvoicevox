# AgentVoiceBox Marketing Baseline

**Document status:** Code-aligned public messaging baseline
**Revision date:** 2026-05-11
**Source of truth:** Implemented repository code.

## 1. Product Description
AgentVoiceBox is an open-source voice AI platform stack built with Django, Django Ninja, Django Channels, Lit 3, PostgreSQL, Redis, and OVOS integration. It provides administrative APIs and a web portal for managing tenants, users, projects, API keys, sessions, billing records, voice settings, themes, audit logs, notifications, and realtime voice-related workflows.

## 2. Current Implemented Capabilities
- Multi-tenant data model using Django ORM.
- REST API under `/api/v2` with OpenAPI documentation.
- WebSocket routes under `/ws/v2` and an experimental `/ws/v1/realtime` gateway.
- Lit 3 administration portal.
- OVOS message-bus configuration bridge.
- Billing integration structures for Lago.
- Keycloak, Vault, Temporal, Kafka, OPA, Prometheus, and Grafana integration points or deployment files.

## 3. Claims That Must Not Be Made Without Separate Verification
- Full OpenAI Realtime API compatibility.
- Guaranteed elimination of all external service costs.
- Production SLA, compliance certification, or audited security posture.
- Unlimited scale or millions of concurrent users.
- Fully autonomous 24/7 business operation.

## 4. Approved Positioning
AgentVoiceBox is best described as a self-hostable voice AI platform foundation with Django/Lit administration, OVOS integration, and SaaS-oriented modules. Production readiness depends on deployment hardening, secret management, test results, and operational review.
