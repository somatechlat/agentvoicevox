# Research Brief: Open-Source Voice Cloning for AgentVoiceBox

**Date:** 2026-09-27
**Depth:** standard (3–5 sub-agents, 1 follow-up round, 15+ sources)
**Audience:** AgentVoiceBox maintainers building an open-source ElevenLabs alternative on OVOS + Django + Redis + Kokoro/Piper/Whisper.

## Question

What open-source voice-cloning systems can AgentVoiceBox realistically integrate, what does cloning *require* (models, GPU, data, latency, license), and what are the product/architecture implications?

## Scope

**In:**
- Actual OSS projects (OpenVoice, Coqui XTTS, F5-TTS, GPT-SoVITS, RVC, Seed-VC, OpenVoice V2, etc.)
- Few-shot / zero-shot / voice-conversion vs full TTS-with-speaker
- License (MIT/Apache vs non-commercial vs RSL)
- Hardware (VRAM, CPU-only viability), sample requirements, quality
- How they would plug into Django/Redis/OVOS worker architecture
- Legal/ethical implications (consent, deepfakes, voice likeness)

**Out:**
- Writing code or integrating now
- Closed APIs (ElevenLabs, Azure) except as comparison baselines
- Music/singing cloning unless highly relevant

## Assumptions
- Stack: Django Ninja + Channels + Redis streams + OVOS bus + local Kokoro/Whisper/Piper
- Target: multi-tenant SaaS, Spanish + English first
- Need: clone from 30s–5min sample, usable in realtime TTS path
- Preference: commercially usable OSS license if possible; if not, document risk

## Angles
1. Landscape of OSS voice cloning (2024–2026): OpenVoice, XTTS, F5-TTS, GPT-SoVITS, RVC/Seed-VC
2. Technical requirements: model size, VRAM, inference latency, sample duration, few-shot vs fine-tune
3. Licensing & legal: commercial use, consent, voice rights, EU AI Act-ish implications
4. Integration patterns for AgentVoiceBox workers (clone job → voice artifact → TTS runtime)
5. Alternatives if full cloning is too heavy: voice conversion on existing TTS; embedding-based multi-speaker; RVC post-process
