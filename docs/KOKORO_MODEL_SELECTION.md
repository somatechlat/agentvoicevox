# Kokoro Model Selection Note

**Document status:** Code-aligned baseline
**Revision date:** 2026-05-11

## 1. Purpose
This note records the current documentation baseline for Kokoro/TTS references in AgentVoiceBox.

## 2. Current Code Position
The primary compose stack delegates active STT/TTS behavior to OVOS listener/audio services. The backend contains voice model/persona/custom voice data structures and OVOS configuration patching, but this document does not assert that a specific Kokoro model file is loaded by the primary runtime unless verified in code and runtime configuration.

## 3. Requirement
Any future Kokoro model recommendation must cite the exact code path, container image, environment variable, or deployment file that loads it.
