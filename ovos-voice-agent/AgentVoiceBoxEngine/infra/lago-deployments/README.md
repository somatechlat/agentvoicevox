# AgentVoiceBox Infrastructure Specification

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11

## 1. Purpose
This document summarizes infrastructure present in the repository and distinguishes the primary local stack from optional deployment references.

## 2. Primary Local Stack
The primary local stack is `ovos-voice-agent/AgentVoiceBoxEngine/docker-compose.yml`.

Implemented services:
- `postgres`: PostgreSQL, host port `65004`, 1536M memory limit.
- `redis`: Redis, host port `65005`, 256M memory limit.
- `django-api`: Django application, host port `65020`, 2048M memory limit.
- `portal-frontend`: Lit/Vite frontend, host port `65027`, 512M memory limit.
- `ovos-bus`: OVOS message bus, host port `65081`, 256M memory limit.
- `ovos-core`: OVOS core, internal network, 2048M memory limit.
- `ovos-listener`: OVOS listener, internal network, 1536M memory limit.
- `ovos-audio`: OVOS audio, internal network, 1536M memory limit.

The compose file documents a 10 GB budget.

## 3. Optional Infrastructure Files
The repository also contains optional or supporting infrastructure for:
- Docker deployments under `infra/docker` and `infra/saas/docker`.
- Kubernetes manifests under `infra/saas/k8s`.
- Standalone shared services under `infra/standalone`.
- Lago deployment files under `infra/lago-deployments`.
- Vault policies and setup scripts.
- Prometheus and Grafana configuration.

These files are not automatically equivalent to the primary local runtime unless explicitly invoked.

## 4. Requirements
- Infrastructure documentation shall state which compose or manifest file it describes.
- Port and memory claims shall match the referenced file.
- Optional services shall be labeled optional.

## 5. Lago Deployment Note
Lago files in this directory are optional billing infrastructure references. They are not required for the primary local `docker-compose.yml` startup unless explicitly launched.
