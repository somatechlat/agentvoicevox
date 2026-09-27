# ISO-Style Requirements — Voice Cloning (AgentVoiceBox)

**Document ID:** AVB-ISO-VC-001  
**Revision date:** 2026-09-27  
**Status:** Baseline for development (no code until this is approved)  
**Source of truth:** `research/voice-cloning/REPORT.md`  
**Related:** `docs/iso/ADMIN_FEATURE_PARITY.md`, `docs/iso/PLATFORM_FUNCTIONAL_REQUIREMENTS.md`

---

## 1. Scope

### 1.1 Purpose
Specify shall-requirements for open-source voice cloning in AgentVoiceBox.

### 1.2 Applicability
Multi-tenant SaaS; Spanish and English first; OVOS + Django + Redis workers.

---

## 2. Normative references

| Ref | Document |
|-----|----------|
| [R1] | `research/voice-cloning/REPORT.md` |
| [R2] | OpenVoice V2 MIT LICENSE (MyShell) |
| [R3] | MeloTTS repository (MIT) |
| [R4] | EU AI Act Article 50 (transparency) |
| [R5] | `research/voice-cloning/findings/F1–F5.md` |

---

## 3. Terms
See REPORT.md §2 (tone-color cloning, IVC, PVC, VC, weight license).

---

## 4. Requirements

### 4.1 Functional — Instant clone (IVC-class)

| ID | Requirement (shall) | Priority |
|----|---------------------|----------|
| VC-F01 | System shall accept a reference audio sample of **1–120 seconds** and create an Instant Voice usable in TTS. | Must |
| VC-F02 | System shall extract and store a **speaker embedding** (e.g. OpenVoice SE) under tenant ownership. | Must |
| VC-F03 | System shall apply tone-color conversion on MeloTTS (or approved base TTS) output using stored embedding. | Must |
| VC-F04 | System shall generate preview audio (≥5 s) automatically after clone job success. | Must |
| VC-F05 | System shall mark clone jobs with status: `queued` \| `running` \| `ready` \| `failed` (never leave `PROCESSING` forever). | Must |
| VC-F06 | System shall support **English and Spanish** text for cloned voices. | Must |

### 4.2 Functional — Professional clone (PVC-class)

| ID | Requirement | Priority |
|----|-------------|----------|
| VC-F10 | System shall accept **≥15 minutes** of high-quality audio for fine-tune clone (target ~30 min). | Should |
| VC-F11 | System shall require **identity verification** (voice captcha or equivalent) before PVC training. | Must |
| VC-F12 | System shall produce a fine-tuned or adapted artifact usable at inference (P2/P3 engine). | Should |

### 4.3 Consent, safety, compliance

| ID | Requirement | Priority |
|----|-------------|----------|
| VC-S01 | System shall require explicit **consent** attestation that the speaker owns/authorized the voice. | Must |
| VC-S02 | System shall record an **audit log** of who cloned which voice and when. | Must |
| VC-S03 | System shall apply **machine-readable synthetic-audio marking** where technically feasible (EU AI Act Art. 50). | Should |
| VC-S04 | System shall expose user-facing **AI interaction disclosure** on first voice-agent contact. | Must |
| VC-S05 | System shall **not** use model weights whose license forbids commercial SaaS use (e.g. XTTS CPML, Fish NC). | Must |
| VC-S06 | System shall **never** install the PyPI package `myshell-openvoice` (malware squat). | Must |
| VC-S07 | System shall strip or replace third-party watermarks only if license permits; otherwise document watermark. | Must |

### 4.4 Architecture / workers

| ID | Requirement | Priority |
|----|-------------|----------|
| VC-A01 | Clone jobs shall run in an isolated worker process (not Django request cycle). | Must |
| VC-A02 | Worker shall use Redis stream/job queue (e.g. `avb:clone:jobs`). | Must |
| VC-A03 | Voice artifacts shall be stored per-tenant with path/key isolation. | Must |
| VC-A04 | Engine shall be pluggable: `openvoice_v2` (P1), `cosyvoice` (P2), `fine_tune` (P3). | Must |
| VC-A05 | Container shall install OpenVoice from **Git source** (`pip install -e .`), not PyPI. | Must |
| VC-A06 | Health check shall gate traffic until models are warm. | Should |

### 4.5 Non-functional

| ID | Requirement | Priority |
|----|-------------|----------|
| VC-N01 | Clone job (IVC) P95 wall time ≤ **10 minutes** on target GPU class. | Should |
| VC-N02 | Cloned TTS realtime factor ≤ **0.5** (faster than real time) on GPU. | Should |
| VC-N03 | Failed jobs shall return structured errors (no `str(exc)` to end users). | Must |

---

## 5. Engine selection (normative for P1)

**P1 engine:** OpenVoice V2 + MeloTTS  

**Evidence:** MIT; ES/EN; tone-color converter API; worker-friendly [R1][R2][R3].  

**Constraint:** Tone-color only — product copy shall not claim full accent/emotion clone [R1].

---

## 6. Acceptance criteria (clone demo)

1. Upload 30 s Spanish sample → consent accepted → job `ready`.  
2. TTS with cloned voice returns playable audio.  
3. Same for English.  
4. Audit entry exists.  
5. Non-authorized tenant cannot use the embedding.

---

## 7. Explicit non-goals (P1)

- Full accent/emotion cloning  
- Cross-lingual zero-shot beyond ES/EN  
- Singing voice conversion  

---

## 8. Traceability

| Req | Evidence |
|-----|----------|
| VC-F01–F03 | `research/voice-cloning/findings/F1.md` [6] OpenVoice API |
| VC-S05–S06 | F1 [4][11], F2 XTTS CPML |
| VC-S03–S04 | `findings/F3.md` EU AI Act |
| VC-A05 | F1 PyPI quarantine |
