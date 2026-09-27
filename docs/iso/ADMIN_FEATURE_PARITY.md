# ISO-Style Requirements — Admin & Feature Parity (ElevenLabs-class)

**Document ID:** AVB-ISO-ADM-001  
**Revision date:** 2026-09-27  
**Status:** Baseline for development  
**Source of truth:** `research/elevenlabs-admin/REPORT.md`  
**Related:** `docs/iso/VOICE_CLONING_REQUIREMENTS.md`

---

## 1. Scope

### 1.1 Purpose
Define admin/UI functional requirements so AgentVoiceBox provides **simple but powerful** voice management comparable in *structure* to ElevenLabs, implemented with OSS/OVOS.

### 1.2 Out of scope
- Music generation, Dubbing Studio timeline (deferred)

---

## 2. Information architecture (shall)

Portal sidebar **shall** implement:

| ID | Module | Must |
|----|--------|------|
| ADM-IA01 | Play (TTS playground) | Must |
| ADM-IA02 | Voices → Explore/Library + My Voices | Must |
| ADM-IA03 | Voice Clone (IVC; PVC later) | Must |
| ADM-IA04 | Agents (OVOS-backed conversational) | Must |
| ADM-IA05 | API Keys | Must |
| ADM-IA06 | Usage & Billing | Must |
| ADM-IA07 | Settings (workspace, models, defaults) | Must |

---

## 3. Voice object (shall)

| ID | Requirement |
|----|-------------|
| ADM-V01 | Each voice shall have stable `voice_id` usable in API and UI. |
| ADM-V02 | Voice shall expose: name, language(s), preview audio, visibility (private/shared), engine, created_by, tags. |
| ADM-V03 | Voice cards shall support preview playback and filter/search. |
| ADM-V04 | Shared library shall be discoverable separately from My Voices. |

---

## 4. TTS controls (shall — label parity)

| ID | Control | Default | Notes |
|----|---------|---------|-------|
| ADM-T01 | Speed | 1.0 | Range 0.7–1.2 |
| ADM-T02 | Stability | 50 | |
| ADM-T03 | Similarity | 75 | |
| ADM-T04 | Style exaggeration | 0 | |
| ADM-T05 | Speaker Boost | On | Disabled when model lacks it |
| ADM-T06 | Model picker (use-case cards) | — | Gate controls per model |

---

## 5. Playground (must ship)

| ID | Requirement |
|----|-------------|
| ADM-P01 | Text box + voice select + settings + Generate. |
| ADM-P02 | Streaming or chunked audio playback. |
| ADM-P03 | Download audio; history of last generations (session). |
| ADM-P04 | Show estimated credit/character cost if metering enabled. |

---

## 6. Cloning UI (must)

| ID | Requirement |
|----|-------------|
| ADM-C01 | Wizard: upload sample → consent → (PVC: verify identity) → progress → ready. |
| ADM-C02 | Clear status; never infinite spinner without error state. |
| ADM-C03 | Preview after ready; delete/rename voice. |
| ADM-C04 | Plan gate: IVC/PVC eligibility messaging (if plans enabled). |

---

## 7. Agents UI (must)

| ID | Requirement |
|----|-------------|
| ADM-G01 | Create agent: name, persona/prompt, voice, language. |
| ADM-G02 | Bind OVOS skills/tools; list active tools. |
| ADM-G03 | Test voice chat (realtime when backend ready). |
| ADM-G04 | Version or snapshot config (should). |

---

## 8. Workspace & roles (should)

| ID | Requirement |
|----|-------------|
| ADM-W01 | Admin can invite/remove members. |
| ADM-W02 | Full vs Basic seat concept if multi-user billing on. |
| ADM-W03 | Resource Manager cannot manage Agents (parity). |

---

## 9. API keys & usage (must)

| ID | Requirement |
|----|-------------|
| ADM-K01 | Create/revoke scoped API keys (mask secrets). |
| ADM-K02 | Usage meters: TTS chars, STT minutes, clone jobs. |
| ADM-K03 | Link to Lago invoices when billing enabled. |

---

## 10. Pronunciation (should — P2)

| ID | Requirement |
|----|-------------|
| ADM-R01 | Alias dictionaries + phoneme (IPA) entries. |
| ADM-R02 | Attach dictionary to voice/agent. |

---

## 11. Explicit non-goals (P1)

- Dubbing Studio multi-track  
- Music / SFX marketplace  
- Voice Library payouts marketplace  

---

## 12. UX principles (normative)

1. **Simple:** one primary action per screen.  
2. **Powerful:** advanced settings behind progressive disclosure.  
3. **Honest:** no UI for features that fail closed or are stubs.  
4. **Same language** for synthetic output as user input where applicable.

---

## 13. Traceability

| Req | Evidence |
|-----|----------|
| ADM-T01–T06 | `research/elevenlabs-admin/findings/F2.md` |
| ADM-IA* / cloning | `findings/F1.md` IVC/PVC, products |
| Credits | `findings/F1.md` pricing/credits |
| Roles | `findings/F1.md` workspaces/members |
