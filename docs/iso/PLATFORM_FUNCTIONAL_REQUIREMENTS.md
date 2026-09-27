# ISO-Style Requirements — Realtime Voice Platform (AgentVoiceBox)

**Document ID:** AVB-ISO-RT-001  
**Revision date:** 2026-09-27  
**Status:** Baseline for development  
**Related:** Voice cloning + Admin parity ISO docs; `ARCHITECTURE.md`

---

## 1. Scope

End-to-end **realtime voice reply** capability (server speaks back), using OSS stack (Whisper STT, Kokoro/MeloTTS TTS, OVOS skills, Django Channels, Redis).

---

## 2. Requirements

### 2.1 Realtime speech pipeline

| ID | Requirement | Priority |
|----|-------------|----------|
| RT-F01 | System shall transcribe committed audio via real STT worker (fail-closed only if STT unconfigured). | Must |
| RT-F02 | System shall generate assistant text via streaming LLM where provider supports it. | Must |
| RT-F03 | System shall synthesize speech audio and deliver `response.audio` deltas or files to the client. | Must |
| RT-F04 | First audible TTS chunk P95 ≤ **1.5 s** after end of user speech (GPU warm). | Should |
| RT-F05 | System shall support barge-in / response cancel. | Should |
| RT-F06 | Client shall play PCM (or documented codec) without silent failures. | Must |

### 2.2 Fake-code policy

| ID | Requirement | Priority |
|----|-------------|----------|
| RT-S01 | System shall **not** ship stub methods that return success without doing work. | Must |
| RT-S02 | Docker compose shall **not** reference management commands that do not exist. | Must |
| RT-S03 | Billing shall **not** charge for media that was not processed. | Must |

### 2.3 Security

| ID | Requirement | Priority |
|----|-------------|----------|
| RT-X01 | Authentication shall fail **closed** when credentials missing. | Must |
| RT-X02 | Tenant shall not be selectable via unauthenticated `X-Tenant-ID`. | Must |
| RT-X03 | API keys compared with constant-time compare. | Must |
| RT-X04 | No secrets in repository. | Must |
| RT-X05 | Bounded audio buffers and rate limits on WS. | Must |

---

## 3. Acceptance (realtime demo)

1. Play 2 s speech to playground → transcript event.  
2. Receive text + audio reply.  
3. End-to-end latency logged.  
4. No `stt_provider_not_configured` when STT is configured.

---

## 4. Traceability

| Req | Evidence |
|-----|----------|
| RT-F01–F03 | Architecture audit 2026-09-27; stubs at `activities/stt.py`, `tts.py` |
| RT-S02 | `docker-compose.yml` missing `run_stt_worker`/`run_tts_worker` |
| RT-X01–X02 | `authentication.py`, `tenant.py` fail-open findings |
