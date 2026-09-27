# ElevenLabs Admin & Product Surface — Parity Specification for AgentVoiceBox

**Document status:** Research baseline (ISO-style)
**Revision date:** 2026-09-27
**Source of truth:** elevenlabs.io docs/pricing fetched 2026-09-27 (`findings/F1.md`, `F2.md`)
**Related:** `docs/iso/ADMIN_FEATURE_PARITY.md`

---

## 1. Scope

### 1.1 Purpose
Define the **admin and voice-management product surface** of ElevenLabs so AgentVoiceBox can implement a **simple but powerful** equivalent with OVOS/open models.

### 1.2 Out of scope
- Implementing UI (this phase is documentation only)
- Full Dubbing Studio / Music (deprioritized)

---

## 2. Product model (what ElevenLabs sells)

| Surface | Role | AgentVoiceBox mapping |
|---------|------|------------------------|
| **ElevenCreative** | No-code TTS/voice/studio | Portal: Voices + Play + Library |
| **ElevenAgents** | Conversational voice agents | Agents + Realtime voice (OVOS) |
| **ElevenAPI** | REST + SDKs | `/api/v2` + OpenAPI clients |
| **Reception AI** | Phone receptionist | Deferred (optional) |

---

## 3. Voice object & library

- Each voice has a **unique ID** (API + dashboard).
- **Voice Library** 10,000+ shared voices; **My Voices** private.
- Create: **clone from audio** or **generate from text description**.
- Library UI: cards + filters + “More actions” sharing.

**AgentVoiceBox shall:** store `voice_id`, name, language(s), preview URL, visibility (private/shared), engine (MeloTTS/OpenVoice/CosyVoice), embedding ref.

---

## 4. Cloning (product definition)

| Type | ElevenLabs | Audio needed | Our OSS mapping |
|------|------------|--------------|-----------------|
| **IVC** Instant | Few-shot conditioning | &lt;2 min | OpenVoice tone-color + SE embedding |
| **PVC** Professional | Weight fine-tune | ~30 min | Fine-tune worker (P2/P3) |

Ethical gates in ElevenLabs: **voice captcha / identity verification**, optional **speaker separation**.

**AgentVoiceBox shall:** require consent checkbox + identity verification for PVC; log clone audit; never clone third parties without verified consent.

---

## 5. Speech models (user-selectable)

| ElevenLabs model | Notes | Our stack |
|------------------|-------|-----------|
| eleven_v3 | 70+ langs, audio tags, no SSML breaks | Defer |
| eleven_multilingual_v2 | 29 langs, high quality | Target quality |
| eleven_flash_v2_5 | ~75ms realtime | Realtime TTS goal |
| Scribe v2 / Realtime | STT | Whisper / faster-whisper / OVOS listener |

**Voice settings (clone these labels in UI):**

| Control | Default | Notes |
|---------|---------|-------|
| Speed | 1.0 (0.7–1.2) | |
| Stability | ~50 | |
| Similarity | ~75 | |
| Style exaggeration | 0 | |
| Speaker Boost | On | **Disabled on v3** — gate per model |

---

## 6. Credits & plans (parity concept)

- **One shared credit pool** across products.
- Example rates: TTS 1/char · STT 330/min · SFX 200/gen · VC/Isolator 1000/min · Dubbing 2k–10k/min.
- Monthly reset; **rollover up to 2 months** (max balance 3× quota).
- Plan gates: commercial license @Starter · IVC @Starter · PVC @Creator · PCM/192kbps @Pro · seats @Scale · SSO @Enterprise.

**AgentVoiceBox shall:** meter usage events already modeled in `apps/billing`; map plan gates to `plan_enforcement`; Lago for invoicing.

---

## 7. Workspace / roles

| Role | Scope |
|------|-------|
| **Full Seat** | All products |
| **Basic Seat** | Agents/API; Creative capped (e.g. 50k credits/cycle) |
| **Admin** | Members, permissions, subscription (always Full Seat) |
| **User Manager** | Enterprise: invite/remove (not resources) |
| **Resource Manager** | Enterprise: voices/studio — **not Agents** |

**AgentVoiceBox shall:** Tenant + role model; Resource Manager ≠ agent admin.

---

## 8. Agents (ElevenAgents pillars)

1. LLM (or custom)  
2. Workflows / Procedures  
3. Knowledge base + RAG  
4. Tools (client, webhook, code, MCP, system)  
5. Conversation flow / turn-taking  
6. Voice (large library, 31 langs)  
7. Personalization (dynamic variables)  
8. Privacy (retention, ZRM, redaction)  
9. Versioning + experiments  

OVOS maps to skills/intents; Django owns multi-tenant agent config.

---

## 9. Developer / API

- REST + Python/TS SDKs  
- Streaming TTS  
- WebSocket realtime  
- API keys with scopes  
- Usage dashboards  

**AgentVoiceBox shall:** `/api/v2/tts`, `/api/v2/stt`, `/ws/v1/realtime` (audio), scoped API keys, usage meter API.

---

## 10. Essential admin IA (minimal but powerful)

```
Sidebar
├── Play (TTS playground)          ← must ship first
├── Voices
│   ├── Explore / Library
│   └── My Voices (+ Clone)
├── Agents                         ← OVOS-backed
├── API Keys
├── Usage & Billing
└── Settings (workspace, models)
```

**Defer:** Dubbing Studio (maintenance mode at ElevenLabs), multi-track Studio, Music.

**Pronunciation:** alias + phoneme dictionaries (Pronunciations Editor) — P2.

---

## 11. UI controls to copy exactly (labels)

- Speed · Stability · Similarity · Style exaggeration · Speaker Boost  
- Model picker **cards** (use-case driven)  
- Voice **cards** with preview + share  
- Pronunciation dictionaries  

---

## 12. Gap vs AgentVoiceBox today

| Module | ElevenLabs | AgentVoiceBox now |
|--------|------------|------------------|
| Voice library | Full | Models/CRUD only |
| Cloning | IVC+PVC | Fake PROCESSING |
| TTS stream | Yes | Stub |
| STT | Scribe | Stub |
| Agents | Full | Text partial |
| Credits | Shared pool | Partial Lago |
| Admin simple UX | Yes | Setup form broken |

---

## 13. Sources (2026-09-27)

Full citations: `research/elevenlabs-admin/findings/F1.md` (25), `F2.md` (12) — elevenlabs.io `/docs/overview`, `/docs/eleven-api/concepts/voice-cloning.md`, `/docs/overview/models`, `/pricing`, workspace members docs.
