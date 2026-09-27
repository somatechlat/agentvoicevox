# Open-Source Voice Cloning for AgentVoiceBox

**Document status:** Research baseline (ISO-style)
**Revision date:** 2026-09-27
**Source of truth:** Primary GitHub/papers/docs fetched 2026-09-27 (`findings/F1–F5.md`)
**Related:** `research/elevenlabs-admin/REPORT.md` · `docs/iso/VOICE_CLONING_REQUIREMENTS.md`

---

## 1. Scope

### 1.1 Purpose
Document what open-source voice cloning AgentVoiceBox can integrate, what cloning requires (models, GPU, data, license), and product/architecture implications for an OVOS + Django + Redis stack.

### 1.2 Out of scope
- Code implementation (this phase is documentation only)
- Closed APIs except as baselines
- Music/singing cloning

### 1.3 Question
What OSS voice-cloning systems can we realistically integrate into AgentVoiceBox as a multi-tenant SaaS (ES/EN first)?

---

## 2. Terms and definitions

| Term | Definition |
|------|------------|
| **Tone-color cloning** | Transfer of speaker *timbre* onto another TTS output (OpenVoice) |
| **IVC (Instant Voice Cloning)** | Few-shot inference conditioning; &lt;2 min audio; no weight fine-tune |
| **PVC (Professional Voice Cloning)** | Weight fine-tune on ~30 min high-quality audio |
| **VC (Voice Conversion)** | Transform *existing* audio into another speaker (RVC, Seed-VC) |
| **Zero-shot** | Usable from a short reference without training |
| **Code license** | License of the repository source |
| **Weight license** | License of pretrained model weights (may differ from code) |

---

## 3. Executive findings

### 3.1 Does “full OpenVoice” exist as a ready cloner?

**Yes and no.** OpenVoice **V2** (April 2024) is real, MIT, free commercial, and supports **English + Spanish** natively via MeloTTS. It is **not** full speaker cloning in the ElevenLabs PVC sense.

From official QA:

> “OpenVoice only clones the tone color of the reference speaker. It does NOT clone the accent or emotion.” [1]

| Capability | OpenVoice V2 |
|------------|--------------|
| Timbre / tone color | Yes (flow-based converter) |
| Accent / emotion / prosody | **No** — comes from MeloTTS base speaker |
| True multi-style PVC | No |
| Spanish | **Yes** (MeloTTS ES) |
| Commercial use | **MIT — free** [2] |
| Official Docker | **No** (community forks only) [3] |
| V3 | **Does not exist** (as of 2026-09-27) |
| PyPI `myshell-openvoice` | **Malware squat — NEVER install** [4] |

**Architecture:** MeloTTS (or other TTS) → waveform → `ToneColorConverter` + speaker embedding (`se_extractor.get_se`) → converted audio.

**Performance:** ~12× real-time on A10G (~85 ms per 1 s speech); CPU fallback works.

**Watermark:** official `convert()` embeds wavmark `@MyShell` — strip/replace for production SaaS.

### 3.2 Landscape (all options)

| Project | What it is | License | ES | Commercial | Notes |
|---------|------------|---------|----|------------|-------|
| **OpenVoice V2** | Tone-color clone + MeloTTS | MIT | Yes | **Yes** | Best “open everything” starting point |
| **MeloTTS** | Multi-speaker TTS | MIT | Yes | Yes | Dockerfile official; CPU real-time |
| **CosyVoice 3** | Few-shot TTS + streaming | Apache-2.0 | **Yes** | **Yes** | Strongest commercial ES/EN TTS+clone fit |
| **F5-TTS** | Zero-shot TTS | MIT code / **weights often NC** | Community | Risky | Official Docker `ghcr.io/swivid/f5-tts:main` |
| **GPT-SoVITS** | Few-shot + fine-tune TTS | MIT | Weak base | Yes | 5s zero-shot / 1min ft; 8–14GB VRAM |
| **XTTS-v2** | Zero-shot TTS | Code MPL / **weights CPML NC** | Yes | **No** | Blocks paid SaaS |
| **RVC** | Voice conversion | MIT | n/a | Yes | Needs ~10 min audio; real-time VC |
| **Seed-VC** | Zero-shot / ft VC | **GPL-3.0** | n/a | Contagious | 1–30s ref; ~430ms |
| **Fish Speech S2** | Large TTS | **Research/NC** | Yes | **No** | Best public quality but not commercial |
| **Kokoro** | Open TTS | Apache (weights) | Limited | Yes | **No practical finetune/cloning path** |

### 3.3 Sample-duration ladder

| Audio you have | Realistic option |
|----------------|------------------|
| 1–30 s | Seed-VC zero-shot; GPT-SoVITS 5s |
| 1–2 min | OpenVoice IVC-style; GPT-SoVITS fine-tune |
| ~30 min | ElevenLabs-class PVC (fine-tune) — GPT-SoVITS / custom |
| ~10 min | RVC conversion |
| ~1 h | StyleTTS2 fine-tune (quality ceiling) |

### 3.4 Legal / SaaS implications

1. **Code ≠ weights.** XTTS/F5 weights can forbid commercial use even if code is MIT/MPL.
2. **EU AI Act Art. 50** (applies 2026-08-02): machine-readable marking of synthetic audio; deployer disclosure of deepfakes; AI-interaction disclosure at first contact [3].
3. **Consent is not enough** for high-quality clones: ElevenLabs requires **identity verification** (voice captcha) even with consent; third parties share via verified links.
4. Voice likeness is **personality/publicity right** (US state laws e.g. CA AB 602).
5. **SaaS must enforce:** opt-in consent, identity verification for PVC, audit log, optional watermark, abuse policy.

### 3.5 Integration implications for AgentVoiceBox

| Concern | Recommendation |
|---------|----------------|
| MVP clone | **OpenVoice V2 (MIT)** as `openvoice-worker` container: MeloTTS + ToneColorConverter |
| Stronger quality later | **CosyVoice 3 (Apache-2.0)** if GPU budget allows |
| Avoid | XTTS weights (NC), Fish S2 (NC), PyPI `myshell-openvoice` (malware) |
| Queue | Custom Redis stream `avb:clone:jobs` (no off-the-shelf queue workers found) |
| Artifacts | Store **speaker embedding** (OpenVoice SE) + optional conditioning vectors per tenant voice |
| Latency | TTFB target: warm model; health-gate before streams (~50s warmup reported for large TTS) |
| Multi-tenant | Isolate voice embeddings; disable cross-request speaker cache (vLLM prefix cache leak risk) |
| Realtime path | Clone offline → bake voice → realtime TTS (Kokoro/MeloTTS/OpenVoice convert) |

---

## 4. Decision matrix (for AgentVoiceBox)

### 4.1 Phase recommendation

| Phase | Clone product | Engine | Why |
|-------|---------------|--------|-----|
| **P1** | “Voice color” clone (0–2 min) | **OpenVoice V2 + MeloTTS** | MIT, ES/EN, simple Python API, worker-friendly |
| **P2** | Better quality / streaming TTS | **CosyVoice 3** or F5 (license-check weights) | Apache-2.0 + streaming |
| **P3** | PVC-style professional clone | Fine-tune worker (GPT-SoVITS or CosyVoice) | Matches ElevenLabs PVC tier |

### 4.2 What we do NOT have today

- No weight fine-tune pipeline in-repo
- No consent/verification flow
- No embedding vault for multi-tenant voices
- No real `CustomVoice` job worker (currently stuck `PROCESSING`)

### 4.3 Docker / integration notes

- **MeloTTS:** official Dockerfile — beachhead for OpenVoice image.
- **OpenVoice:** no official Dockerfile; use git install (`pip install -e .`), **not** PyPI.
- Community: `ground-creative/openvoice-docker` (CUDA + OpenAI-like API) — evaluate, do not trust blindly.
- F5 official image exists but weight license may block commercial SaaS.

---

## 5. Open questions

1. Confirm Spanish quality of OpenVoice+MeloTTS vs CosyVoice3 on target hardware (GPU class on server).
2. Whether watermark stripping is required for ToS compliance of MyShell checkpoints (read LICENSE vs wavmark notice).
3. GPL Seed-VC compatibility with Django SaaS (likely: isolate as separate process/service).
4. Exact VRAM for CosyVoice3 streaming worker on our fleet.

---

## 6. Sources (access date 2026-09-27)

[1] OpenVoice QA — tone color only — https://github.com/myshell-ai/OpenVoice/blob/main/docs/QA.md  
[2] OpenVoice LICENSE MIT — https://raw.githubusercontent.com/myshell-ai/OpenVoice/main/LICENSE  
[3] OpenVoice USAGE / V2 — https://github.com/myshell-ai/OpenVoice  
[4] PyPI MyShell-OpenVoice quarantined — https://pypi.org/project/MyShell-OpenVoice/  
[5] OpenVoice paper arXiv 2312.01479 — https://arxiv.org/html/2312.01479v6  
[6] MeloTTS — https://github.com/myshell-ai/MeloTTS  
[7] F5-TTS Docker — https://github.com/swivid/F5-TTS  
[8] GPT-SoVITS — https://github.com/RVC-Boss/GPT-SoVITS  
[9] Seed-VC — https://github.com/Plachtaa/seed-vc  
[10] CosyVoice — https://github.com/FunAudioLLM/CosyVoice  
[11] XTTS license CPML — Coqui Public Model License (weights)  
[12] EU AI Act transparency (Art. 50) — official EUR-Lex  
[13] Full evidence: `findings/F1.md`–`F5.md` (55+ cited claims)

---

## 7. ISO mapping

Requirements derived from this research live in:  
**`docs/iso/VOICE_CLONING_REQUIREMENTS.md`** (shall-statements for development).
