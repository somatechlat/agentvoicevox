# Software Requirements Specification (SRS)
**Project:** AgentVoiceBox  
**Standard:** ISO/IEC 29148:2018 Compliant  
**Version:** 1.1.0 (Production Hardened)

## 1. Introduction
### 1.1 Purpose
This document provides the complete Software Requirements Specification (SRS) for AgentVoiceBox, a sovereign, containerized voice AI gateway utilizing the OpenVoiceOS (OVOS) intelligence bus. It is intended for developers, AI agent maintainers, and system administrators.

### 1.2 Scope
AgentVoiceBox replaces all cloud-bound voice logic (OpenAI Realtime/Whisper) with a 100% locally hosted OVOS cognitive stack. The platform exposes a Django Ninja REST API and a Lit 3 Web Component frontend for exhaustive multi-tenant and system-level administration. The cluster is guaranteed to operate under a strict 10 GB memory constraint.

### 1.3 Definitions, Acronyms, and Abbreviations
- **OVOS:** Open Voice OS.
- **VAD:** Voice Activity Detection.
- **STT/TTS:** Speech-to-Text / Text-to-Speech.
- **SaaS:** Software as a Service.
- **Lit:** Lit Web Components (Frontend Framework).

## 2. Overall Description
### 2.1 Product Perspective
AgentVoiceBox is a standalone container cluster functioning as a drop-in sovereign replacement for external voice APIs. It operates strictly within the `65000-65099` port range.

### 2.2 Product Functions
- **Real-Time Voice Interfacing:** Accepts OGG/WAV streams and routes them via the OVOS Message Bus to cognitive engines.
- **Voice Cloning:** Allows upload and management of audio samples to generate new TTS models on-the-fly.
- **Exhaustive Administration:** Provides a SaaS-grade Portal to configure every parameter of the `mycroft.conf` spec (Skills, VAD, Location, Core, Audio).
- **Internationalization (i18n):** Native multi-language support (English/Spanish).

### 2.3 User Characteristics
- **System Administrators:** Non-technical operators who require a clear, tooltip-guided UI to configure the OVOS engine.
- **AI Agents:** Automated systems utilizing the `OVOSConfigBridge` API endpoints to patch settings dynamically.

### 2.4 Constraints
- **Resource Limitation:** Total cluster RAM must not exceed 10.0 GB. Swap memory must equal standard memory (`memswap_limit = memory`) to prevent disk thrashing.
- **Framework Constraint:** NO FastAPI, NO Alpine.js, NO SQLAlchemy for standard models. All APIs must be Django Ninja; all UIs must be Lit 3; all models must be Django ORM.

## 3. Specific Requirements
### 3.1 External Interface Requirements
#### 3.1.1 User Interfaces
- **Portal:** Built with Lit 3. Uses a glassmorphic aesthetic with comprehensive `<ui-tooltip>` integration.

#### 3.1.2 Software Interfaces
- **Message Bus:** Interaction with `ovos-bus` via websockets on port 8181.
- **Database:** PostgreSQL on port 65004 for agent state persistence.

### 3.2 System Features
#### 3.2.1 OVOS Dynamic Configuration
- **Description:** The system must intercept `/v1/voice/ovos/config` PATCH requests and synchronously route them to the OVOS bus (`configuration.patch`).
- **Response Time:** Sub-800ms synchronous block.

#### 3.2.2 Live i18n
- **Description:** The UI must support instant language toggling without a page reload, using reactive state controllers.

### 3.3 Nonfunctional Requirements
#### 3.3.1 Performance
- Max allowed cluster RAM: 10GB.
- Max latency for config patch: 1000ms.

#### 3.3.2 Security
- Authentication bypass allowed ONLY in local testing environments (`AUTH_BYPASS=true`).
- Production deployments must rely on Keycloak/Oauth2 via the Django gateway.
