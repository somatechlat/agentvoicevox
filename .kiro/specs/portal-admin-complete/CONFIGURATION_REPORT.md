# AgentVoiceBox Configuration Report
## Complete Settings & Administration Parameters for Tenant Portal UI

---

## 1. SPEECH-TO-TEXT (STT) CONFIGURATION

### 1.1 Faster-Whisper Settings (Current Implementation)

| Parameter | Environment Variable | Default | Options | UI Control |
|-----------|---------------------|---------|---------|------------|
| Model Size | `STT_MODEL` | `base` | tiny, base, small, medium, large-v2, large-v3 | Dropdown |
| Device | `STT_DEVICE` | `auto` | cpu, cuda, auto | Dropdown |
| Compute Type | `STT_COMPUTE_TYPE` | `float16` | float16, int8, float32 | Dropdown |
| Batch Size | `STT_BATCH_SIZE` | `4` | 1-16 | Slider |
| Language | Per-request | `en` | BCP-47 codes | Dropdown |
| VAD Filter | Hardcoded | `true` | true/false | Toggle |
| Beam Size | Hardcoded | `5` | 1-10 | Slider |

### 1.2 Available OVOS STT Plugins (Future Integration)

| Plugin | Offline | Streaming | Type |
|--------|---------|-----------|------|
| ovos-stt-plugin-fasterwhisper | ✅ | ❌ | FOSS |
| ovos-stt-plugin-whispercpp | ✅ | ❌ | FOSS |
| ovos-stt-plugin-vosk | ✅ | ❌ | FOSS |
| ovos-stt-plugin-chromium | ❌ | ❌ | API (free) |
| ovos-stt-plugin-pocketsphinx | ✅ | ❌ | FOSS |
| neon-stt-plugin-nemo | ✅ | ✅ | FOSS |

---

## 2. TEXT-TO-SPEECH (TTS) CONFIGURATION

### 2.1 Kokoro ONNX Settings (Current Implementation)

| Parameter | Environment Variable | Default | Options | UI Control |
|-----------|---------------------|---------|---------|------------|
| Model File | `KOKORO_MODEL_FILE` | `kokoro-v1.0.onnx` | Kokoro-82M.onnx, Kokoro-200M.onnx | Dropdown |
| Model Directory | `KOKORO_MODEL_DIR` | `/app/cache/kokoro` | Path | Text (Admin) |
| Voices File | `KOKORO_VOICES_FILE` | `voices-v1.0.bin` | Path | Text (Admin) |
| Default Voice | `TTS_DEFAULT_VOICE` | `am_onyx` | See voice list | Dropdown + Preview |
| Default Speed | `TTS_DEFAULT_SPEED` | `1.1` | 0.5 - 2.0 | Slider |
| Chunk Size | `TTS_CHUNK_SIZE` | `24000` | 12000-48000 | Slider (Advanced) |

### 2.2 Available Kokoro Voices

| Voice ID | Gender | Accent | Description |
|----------|--------|--------|-------------|
| `am_onyx` | Male | American | Deep, professional |
| `am_adam` | Male | American | Neutral, clear |
| `am_michael` | Male | American | Warm, friendly |
| `af_sarah` | Female | American | Professional |
| `af_nicole` | Female | American | Warm, conversational |
| `bf_emma` | Female | British | Professional |
| `bf_isabella` | Female | British | Warm |
| `bm_george` | Male | British | Professional |
| `bm_lewis` | Male | British | Casual |

### 2.3 Available OVOS TTS Plugins (Future Integration)

| Plugin | Streaming | Offline | Type |
|--------|-----------|---------|------|
| ovos-tts-plugin-piper | ❌ | ✅ | FOSS |
| ovos-tts-plugin-mimic3 | ❌ | ✅ | FOSS |
| ovos-tts-plugin-edge-tts | ✅ | ❌ | API (free) |
| ovos-tts-plugin-espeakNG | ❌ | ✅ | FOSS |
| neon-tts-plugin-coqui | ❌ | ✅ | FOSS |

---

## 3. LLM CONFIGURATION

### 3.1 LLM Worker Settings (Current Implementation)

| Parameter | Environment Variable | Default | Options | UI Control |
|-----------|---------------------|---------|---------|------------|
| Default Provider | `LLM_DEFAULT_PROVIDER` | `groq` | groq, openai, ollama | Dropdown |
| Default Model | `LLM_DEFAULT_MODEL` | `llama-3.1-70b-versatile` | Provider-specific | Dropdown |
| Max Tokens | `LLM_MAX_TOKENS` | `1024` | 256-4096 | Slider |
| Temperature | `LLM_TEMPERATURE` | `0.7` | 0.0-2.0 | Slider |
| OpenAI API Key | `OPENAI_API_KEY` | - | API Key | Password Input |
| Groq API Key | `GROQ_API_KEY` | - | API Key | Password Input |
| Ollama Base URL | `OLLAMA_BASE_URL` | `http://localhost:11434` | URL | Text Input |

### 3.2 Circuit Breaker Settings

| Parameter | Environment Variable | Default | Options | UI Control |
|-----------|---------------------|---------|---------|------------|
| Failure Threshold | `CIRCUIT_BREAKER_THRESHOLD` | `5` | 1-20 | Slider |
| Recovery Timeout | `CIRCUIT_BREAKER_TIMEOUT` | `30` | 10-120 seconds | Slider |

### 3.3 Available LLM Models by Provider

**Groq:**
- llama-3.1-70b-versatile
- llama-3.1-8b-instant
- mixtral-8x7b-32768
- gemma2-9b-it

**OpenAI:**
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- gpt-3.5-turbo

**Ollama (Self-hosted):**
- llama3.1
- mistral
- codellama
- Custom models

---

## 4. SESSION CONFIGURATION

### 4.1 Session Settings (Per-Tenant Configurable)

| Parameter | Default | Options | UI Control |
|-----------|---------|---------|------------|
| Model | `ovos-voice-1` | String | Text Input |
| Voice | `am_onyx` | Voice list | Dropdown + Preview |
| Speed | `1.1` | 0.5-2.0 | Slider |
| Temperature | `0.8` | 0.0-2.0 | Slider |
| Instructions | "You are a helpful assistant." | Text | Textarea |
| Output Modalities | `["audio", "text"]` | audio, text | Checkboxes |
| Max Output Tokens | `null` | 256-4096 | Slider |
| Tools | `[]` | Tool definitions | JSON Editor |
| Tool Choice | `null` | auto, none, required | Dropdown |

---

## 5. PERSONA CONFIGURATION

### 5.1 Persona Settings (OVOS Integration)

| Parameter | Description | UI Control |
|-----------|-------------|------------|
| Name | Persona display name | Text Input |
| Solvers | Ordered list of solver plugins | Drag-and-drop list |
| System Prompt | Base instructions for the persona | Textarea |
| Fallback Behavior | What to do when no answer | Dropdown |

### 5.2 Available Solver Plugins

| Solver | Description | Offline |
|--------|-------------|---------|
| ovos-solver-wikipedia-plugin | Wikipedia knowledge | ❌ |
| ovos-solver-ddg-plugin | DuckDuckGo search | ❌ |
| ovos-solver-plugin-wolfram-alpha | Math/science | ❌ |
| ovos-solver-wordnet-plugin | Dictionary | ✅ |
| ovos-solver-rivescript-plugin | Scripted responses | ✅ |
| ovos-solver-openai-plugin | OpenAI GPT | ❌ |
| ovos-solver-groq-plugin | Groq LLM | ❌ |

---

## 6. VOICE CLONING (Future Feature)

### 6.1 Voice Cloning Settings

| Parameter | Description | UI Control |
|-----------|-------------|------------|
| Source Audio | Upload audio sample | File Upload |
| Voice Name | Custom voice identifier | Text Input |
| Language | Target language | Dropdown |
| Quality | Clone quality level | Dropdown |
| Preview | Test cloned voice | Audio Player |

---

## 7. RATE LIMITING & QUOTAS

### 7.1 Per-Tenant Rate Limits

| Parameter | Default | Options | UI Control |
|-----------|---------|---------|------------|
| Requests per Minute | `60` | 10-1000 | Slider |
| Tokens per Minute | `120000` | 10000-1000000 | Slider |
| Concurrent Connections | Plan-based | 1-100 | Slider |
| Audio Minutes per Month | Plan-based | 10-unlimited | Display |

---

## 8. WEBHOOK CONFIGURATION

### 8.1 Webhook Events

| Event | Description |
|-------|-------------|
| `session.started` | Voice session initiated |
| `session.ended` | Voice session completed |
| `transcription.completed` | STT finished |
| `synthesis.completed` | TTS finished |
| `api_key.created` | New API key generated |
| `api_key.revoked` | API key revoked |
| `billing.invoice.created` | New invoice |
| `billing.payment.succeeded` | Payment successful |
| `billing.payment.failed` | Payment failed |

---

## 9. SECURITY SETTINGS

### 9.1 Per-Tenant Security

| Parameter | Description | UI Control |
|-----------|-------------|------------|
| API Key Scopes | Available permissions | Checkboxes |
| IP Allowlist | Restrict API access by IP | IP List Editor |
| 2FA Requirement | Require 2FA for team | Toggle |
| Session Timeout | Auto-logout duration | Dropdown |
| Audit Log Retention | How long to keep logs | Dropdown |

---

## 10. NOTIFICATION PREFERENCES

### 10.1 Email Notifications

| Notification | Description | Default |
|--------------|-------------|---------|
| Billing Alerts | Invoice, payment issues | ✅ |
| Usage Alerts | Approaching limits | ✅ |
| Security Alerts | Login failures, key changes | ✅ |
| Product Updates | New features | ❌ |
| Weekly Summary | Usage report | ✅ |

---

## 11. UI SCREENS NEEDED

Based on this analysis, the Tenant Portal needs these configuration screens:

### 11.1 Voice Settings Screen
- TTS Voice Selection (with audio preview)
- TTS Speed Slider
- STT Model Selection
- STT Language Selection

### 11.2 LLM Settings Screen
- Provider Selection (Groq/OpenAI/Ollama)
- Model Selection (per provider)
- Temperature Slider
- Max Tokens Slider
- API Key Management (BYOK)

### 11.3 Persona Management Screen
- Create/Edit Personas
- Solver Plugin Selection
- System Prompt Editor
- Persona Preview/Test

### 11.4 Session Defaults Screen
- Default Voice Configuration
- Default Instructions
- Output Modalities
- Tool Configuration

### 11.5 Voice Cloning Screen (Future)
- Upload Voice Sample
- Clone Voice
- Manage Custom Voices
- Preview Cloned Voices

### 11.6 Advanced Settings Screen
- Rate Limits (view/request increase)
- Webhook Configuration
- Security Settings
- Notification Preferences

---

## 12. TERMINOLOGY CORRECTION

As requested, the correct terminology is:

| Old Term | Correct Term |
|----------|--------------|
| Customer Portal | **Tenant Portal** |
| Customer Admin | **Tenant Admin** |
| Customer Dashboard | **Tenant Dashboard** |

The "Tenant Portal" represents a complete deployment of AgentVoiceBox for a single organization/tenant.
