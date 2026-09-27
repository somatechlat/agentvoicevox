# AgentVoiceBox Task Baseline

**Document status:** Code-aligned task list
**Revision date:** 2026-09-27

## 1. Immediate Tasks
- [ ] **P0 Security (open):** rotate/purge committed secrets (`backend/.env`, Lago RSA, e2e JWTs); fail-closed auth middleware; drop unauthenticated `X-Tenant-ID` trust.
- [x] Implement real `run_stt_worker` (faster-whisper + Redis stream + channel layer).
- [x] Implement real `run_tts_worker` (Kokoro ONNX + Redis stream + PCM16 chunks).
- [x] Replace STT/TTS Temporal activity fail-closed stubs with real providers.
- [x] Enqueue session/STT/TTS consumers to Redis worker streams (no fake “In production” comments).
- [ ] Run `python manage.py check` from `backend/` after Docker stack is up.
- [ ] Run backend pytest suite (needs PostgreSQL on 65004).
- [ ] Run frontend `bun run type-check` and `bun run build`.
- [ ] Run Playwright after stack is available.
- [ ] Wire `/ws/v1/realtime` audio path (same STT/TTS engines) — still experimental.
- [ ] Voice cloning P1: OpenVoice V2 worker (`docs/iso/VOICE_CLONING_REQUIREMENTS.md`).
- [ ] Admin parity modules (`docs/iso/ADMIN_FEATURE_PARITY.md`).

## 2. Documentation Tasks
- [x] Voice cloning research + ISO shall-reqs (`docs/iso/`, `research/`).
- [x] ElevenLabs admin parity research + ISO doc.
- [x] Align `RULES.md` paths with `AgentVoiceBoxEngine` tree.
- [ ] Map ISO req IDs to implementation tasks after P0 security.

## 3. Known runtime dependencies (not fake)
- `workers/stt/requirements.txt` → faster-whisper
- `workers/tts/requirements.txt` → kokoro-onnx + model files (`kokoro-v1.0.onnx`, `voices-v1.0.bin`) at `TTS_WORKER.MODEL_DIR`
- Models are **not** vendored in git; they must be provisioned at deploy time.

## 2. Documentation Tasks
- [x] Replace stale framework and route claims with code-aligned baselines.
- [x] Remove `.kiro` planning tree after moving current rules into canonical docs.
- [x] Add Docker full-system test TODO.
- [x] Remove 5 exact duplicate documentation files.
- [x] Rewrite `infra/lago-deployments/README.md` to Lago-only content.
- [x] Merge MCP content into `ARCHITECTURE.md`.
- [x] Fix stale Playwright claims in SRS_ISO_AGENT_VOICE_BOX and AGENT_VOICE_BOX_SRS.
- [x] Update revision dates on all modified docs.
- [x] Regenerate Sphinx API output after code changes.
- [x] Add `apps.mcp` to Sphinx toctree.
- [x] Remove `apps.llm.rst` and `apps.stt.rst` ghost modules.
- [x] Create `MIDDLEWARE.md`, `INTEGRATIONS.md`, `WORKFLOWS.md`, `SECURITY.md`, `TESTING.md`.
- [x] Add known issues section to `portal-frontend/README.md`.
