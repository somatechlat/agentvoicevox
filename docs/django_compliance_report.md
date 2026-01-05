# Django Compliance Report

Scope: Python files that are not inside Django backend apps or Django runtime infrastructure.
Rule: All Python files must be part of Django infra/framework.

## Violations (non-Django locations)
1. (removed) ovos_voice_agent/__init__.py
2. (migrated) ovos-voice-agent/audio_codecs.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/realtime/services/audio_codecs.py`
3. (migrated) ovos-voice-agent/config.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/config/voice_agent.py`
4. (migrated) ovos-voice-agent/rate_limiter.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/realtime/services/rate_limiter.py`
5. (migrated) ovos-voice-agent/llm_integration.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/realtime/services/llm_integration.py`
6. (migrated) ovos-voice-agent/function_calling.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/realtime/services/function_calling.py`
7. (removed) ovos-voice-agent/AgentVoiceBoxEngine/workers/__init__.py
8. (migrated) ovos-voice-agent/AgentVoiceBoxEngine/workers/llm_worker.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/workflows/management/commands/run_llm_worker.py`
9. (migrated) ovos-voice-agent/AgentVoiceBoxEngine/workers/tts_worker.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/workflows/management/commands/run_tts_worker.py`
10. (migrated) ovos-voice-agent/AgentVoiceBoxEngine/workers/stt_worker.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/workflows/management/commands/run_stt_worker.py`
11. (migrated) ovos-voice-agent/AgentVoiceBoxEngine/workers/worker_config.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/workflows/redis_client.py`
12. (migrated) ovos-voice-agent/AgentVoiceBoxEngine/workers/worker_redis.py -> `ovos-voice-agent/AgentVoiceBoxEngine/backend/apps/workflows/redis_client.py`
13. (migrated) seed_lago command moved to Django management command

## Django Infra (compliant)
- All Python under `ovos-voice-agent/AgentVoiceBoxEngine/backend/` (apps, config, integrations, migrations, tests).

## Required Remediation (next actions)
- Review for any remaining non-Django Python files and remove or migrate.

## Notes
- Migrated modules now rely on Django settings for all configuration (no hardcoded defaults).
