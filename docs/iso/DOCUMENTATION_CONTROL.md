# Documentation Control — ISO Suite Index

**Document ID:** AVB-ISO-DOC-001  
**Revision date:** 2026-09-27  
**Status:** Active  

## 1. Purpose
Single index of ISO-style requirements and research evidence for AgentVoiceBox voice cloning + admin parity + realtime platform.

## 2. Controlled documents

| ID | File | Purpose | Status |
|----|------|---------|--------|
| AVB-ISO-VC-001 | `docs/iso/VOICE_CLONING_REQUIREMENTS.md` | Voice cloning shall-reqs | Baseline |
| AVB-ISO-ADM-001 | `docs/iso/ADMIN_FEATURE_PARITY.md` | ElevenLabs-class admin/UX | Baseline |
| AVB-ISO-RT-001 | `docs/iso/PLATFORM_FUNCTIONAL_REQUIREMENTS.md` | Realtime voice + security | Baseline |
| AVB-ISO-DOC-001 | `docs/iso/DOCUMENTATION_CONTROL.md` | This index | Active |
| AVB-RSCH-VC | `research/voice-cloning/REPORT.md` | OSS cloning research | Complete |
| AVB-RSCH-EL | `research/elevenlabs-admin/REPORT.md` | ElevenLabs surface research | Complete |

## 3. Evidence packs (not normative; source for shall-reqs)

| Path | Contents |
|------|----------|
| `research/voice-cloning/brief.md` | Research contract |
| `research/voice-cloning/findings/F1–F5.md` | 55+ cited claims (OpenVoice, landscape, legal, integration, alternatives) |
| `research/elevenlabs-admin/findings/F1–F2.md` | 37 cited claims (product + UX) |

## 4. Review rules
- Documentation **must match code** (repo `RULES.md`).
- Unimplemented features **must** be labeled planned/optional.
- After each implementation phase, update ISO docs revision date and status.

## 5. Completeness checklist (2026-09-27)

- [x] OpenVoice investigated (not just landscape)
- [x] All major OSS cloning options researched
- [x] Legal/license implications documented
- [x] Integration/containers documented
- [x] ElevenLabs admin + voice-management features documented
- [x] ISO shall-requirements written
- [x] Index / documentation control present
- [ ] Developer implementation plan tasks (next: map ISO IDs to `TASKS.md`)
- [ ] No code until this suite is accepted (per user)
