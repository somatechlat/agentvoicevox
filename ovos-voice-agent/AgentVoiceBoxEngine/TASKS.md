# AgentVoiceBox Task Baseline

**Document status:** Code-aligned task list
**Revision date:** 2026-05-11

## 1. Immediate Tasks
- [ ] Remove or rotate committed secrets and local auth artifacts.
- [ ] Remove generated caches and build artifacts from tracking.
- [ ] Repair Docker full-system test setup using `DOCKER_TEST_TODO.md`.
- [ ] Run `python manage.py check` from `backend/`.
- [ ] Run backend pytest suite.
- [ ] Run frontend `bun run type-check` and `bun run build`.
- [ ] Run relevant Playwright tests after the stack is available.
- [ ] Decide whether `/ws/v1/realtime` is experimental-only or should be completed against a tested compatibility matrix.

## 2. Documentation Tasks
- [x] Replace stale framework and route claims with code-aligned baselines.
- [x] Remove `.kiro` planning tree after moving current rules into canonical docs.
- [x] Add Docker full-system test TODO.
- [ ] Regenerate Sphinx API output after code changes.
- [ ] Add a release-ready security note after secret cleanup.
