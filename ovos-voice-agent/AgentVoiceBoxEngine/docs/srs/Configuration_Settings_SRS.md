# Configuration Settings Specification
**Project**: AgentVoiceBox  
**Version**: 1.0.0  
**Date**: 2026-01-05  
**Standard**: ISO/IEC 29148:2018  
**Document Type**: Configuration Requirements Specification

---

## 1. Introduction

### 1.1 Purpose
This document provides a comprehensive specification of all configuration parameters for the AgentVoiceBox platform. Every environment variable, its data type, validation constraints, default values, and dependencies are documented to support:

- **Day 0 Infrastructure Setup**: via Setup Wizard UI
- **Production Deployment**: Kubernetes ConfigMaps/Secrets
- **Development Environments**: Local `.env` files
- **Automated Configuration Management**: Infrastructure-as-Code

### 1.2 Scope
This specification covers **100+ configuration parameters** across **12 service categories**:

1. Django Core (7 parameters)
2. PostgreSQL Database (6 parameters)
3. Redis Cache & Pub/Sub (4 parameters + worker connection settings)
4. Keycloak Authentication (4 parameters)
5. Temporal Workflows (3 parameters)
6. HashiCorp Vault (6 parameters)
7. Open Policy Agent (OPA) (4 parameters)
8. Apache Kafka (4 parameters)
9. Lago Billing (3 parameters)
10. LLM/STT/TTS Workers (30+ parameters)
11. Observability (4 parameters)
12. CORS & Rate Limiting (9 parameters)

### 1.3 Configuration Sources

**Priority Order** (highest to lowest):
1. Kubernetes Secrets (production)
2. Environment variables
3. `.env` file (development)
4. Default values (if specified)

**Validation**: All configuration is validated at startup using Pydantic. Missing required variables cause immediate failure with detailed error messages.

---

## 2. Django Core Settings

### 2.1 DJANGO_SECRET_KEY

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Validation** | Minimum 50 characters |
| **Default** | None |
| **Description** | Django secret key for cryptographic signing (sessions, CSRF, password reset tokens) |
| **Security** | **CRITICAL** - Must be unique per environment, stored in Vault |
| **Example** | `django_secret_key_50_chars_min_random_generated_string_here_12345` |

---

### 2.2 DJANGO_DEBUG

| Attribute | Value |
|-----------|-------|
| **Type** | `boolean` |
| **Required** | No |
| **Default** | `false` |
| **Description** | Enable/disable Django debug mode |
| **Production** | **MUST** be `false` |
| **Development** | Can be `true` for detailed error pages |

---

### 2.3 DJANGO_ALLOWED_HOSTS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (comma-separated list) |
| **Required** | ✅ Yes |
| **Validation** | Parsed into Python list |
| **Description** | Comma-separated list of allowed HTTP Host header values |
| **Example** | `localhost,127.0.0.1,agentvoicebox.example.com` |
| **Production** | Must include all public domain names |

---

### 2.4 DJANGO_SETTINGS_MODULE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Python module path to Django settings |
| **Valid Values** | `config.settings.development`, `config.settings.production`, `config.settings.testing` |
| **Example** | `config.settings.production` |

---

### 2.5 VOICE_AGENT_BASE_URL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (URL) |
| **Required** | ✅ Yes |
| **Description** | Public HTTP base URL for voice agent API |
| **Example** | `http://localhost:65020` (dev), `https://api.agentvoicebox.com` (prod) |
| **Usage** | Used for generating absolute URLs in responses, webhooks, redirects |

---

### 2.6 VOICE_AGENT_WS_BASE_URL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (WebSocket URL) |
| **Required** | ✅ Yes |
| **Description** | Public WebSocket base URL for real-time communication |
| **Example** | `ws://localhost:65020` (dev), `wss://api.agentvoicebox.com` (prod) |
| **Usage** | WebSocket connection endpoint for voice streaming, live transcription |

---

## 3. PostgreSQL Database Settings

### 3.1 DB_HOST

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | PostgreSQL server hostname or IP address |
| **Example** | `localhost` (dev), `postgres.internal` (k8s), `rds.amazonaws.com` (AWS) |

---

### 3.2 DB_PORT

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `5432` |
| **Description** | PostgreSQL server port |
| **Valid Range** | 1-65535 |

---

### 3.3 DB_NAME

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | PostgreSQL database name |
| **Example** | `agentvoicebox` |
| **Production** | Use environment-specific names (e.g., `agentvoicebox_prod`) |

---

### 3.4 DB_USER

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | PostgreSQL database user |
| **Example** | `agentvoicebox` |
| **Security** | Use dedicated service account, not `postgres` superuser |

---

### 3.5 DB_PASSWORD

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | PostgreSQL database password |
| **Security** | **CRITICAL** - Store in Vault, rotate regularly |
| **Minimum Strength** | 16 characters, alphanumeric + symbols |

---

### 3.6 DB_CONN_MAX_AGE

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `60` |
| **Description** | Maximum lifetime for database connections (seconds) |
| **Valid Range** | 0 (disable pooling) - 3600 |
| **Recommendation** | `60` for web servers, `300` for workers |

---

## 4. Redis Settings

### 4.1 REDIS_URL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (Redis URL) |
| **Required** | ✅ Yes |
| **Format** | `redis://[password@]host:port/db` |
| **Example** | `redis://localhost:6379/0`, `redis://:password@redis.internal:6379/0` |
| **Security** | Use password authentication in production |

---

### 4.2 REDIS_CACHE_DB

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `1` |
| **Description** | Redis database index for Django cache |
| **Valid Range** | 0-15 (default Redis config) |

---

### 4.3 REDIS_SESSION_DB

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `2` |
| **Description** | Redis database index for user sessions |
| **Valid Range** | 0-15 |

---

### 4.4 REDIS_CHANNEL_DB

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `3` |
| **Description** | Redis database index for Django Channels (WebSocket coordination) |
| **Valid Range** | 0-15 |

---

### 4.5 Redis Worker Connection Settings

#### REDIS_MAX_CONNECTIONS

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Maximum Redis connections for worker processes |
| **Default** | `200` |
| **Valid Range** | 10-1000 |
| **Tuning** | Increase for high-concurrency workloads |

#### REDIS_SOCKET_TIMEOUT

| Attribute | Value |
|-----------|-------|
| **Type** | `float` |
| **Required** | ✅ Yes |
| **Description** | Redis socket timeout (seconds) |
| **Default** | `5.0` |
| **Valid Range** | 1.0-30.0 |

#### REDIS_SOCKET_CONNECT_TIMEOUT

| Attribute | Value |
|-----------|-------|
| **Type** | `float` |
| **Required** | ✅ Yes |
| **Description** | Redis socket connect timeout (seconds) |
| **Default** | `5.0` |
| **Valid Range** | 1.0-10.0 |

#### REDIS_RETRY_ON_TIMEOUT

| Attribute | Value |
|-----------|-------|
| **Type** | `boolean` |
| **Required** | ✅ Yes |
| **Description** | Retry Redis operations on timeout |
| **Default** | `true` |
| **Recommendation** | `true` for resilience |

#### REDIS_HEALTH_CHECK_INTERVAL

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Redis connection health check interval (seconds) |
| **Default** | `30` |
| **Valid Range** | 10-300 |

---

## 5. Keycloak Authentication Settings

### 5.1 KEYCLOAK_URL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (URL) |
| **Required** | ✅ Yes |
| **Description** | Keycloak server URL |
| **Example** | `http://localhost:8080` (dev), `https://auth.agentvoicebox.com` (prod) |
| **Usage** | OAuth2/OIDC authentication and token validation |

---

### 5.2 KEYCLOAK_REALM

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Keycloak realm name |
| **Example** | `agentvoicebox` |
| **Note** | Realm must be pre-configured in Keycloak |

---

### 5.3 KEYCLOAK_CLIENT_ID

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Keycloak OAuth client ID |
| **Example** | `agentvoicebox-backend` |
| **Note** | Client must be registered in Keycloak realm |

---

### 5.4 KEYCLOAK_CLIENT_SECRET

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (optional) |
| **Required** | No (required for confidential clients) |
| **Description** | Keycloak OAuth client secret |
| **Security** | **CRITICAL** - Store in Vault |
| **Note** | Not needed for public clients (frontend) |

---

## 6. Temporal Workflow Settings

### 6.1 TEMPORAL_HOST

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (host:port) |
| **Required** | ✅ Yes |
| **Description** | Temporal server address and port |
| **Example** | `localhost:7233` (dev), `temporal.internal:7233` (prod) |
| **Default Port** | `7233` |

---

### 6.2 TEMPORAL_NAMESPACE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Temporal namespace for workflow isolation |
| **Example** | `agentvoicebox`, `agentvoicebox-prod` |
| **Best Practice** | Use environment-specific namespaces |

---

### 6.3 TEMPORAL_TASK_QUEUE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Default Temporal task queue name |
| **Example** | `default`, `voice-workflows` |
| **Usage** | Task queue for workflow execution |

---

## 7. HashiCorp Vault Settings

### 7.1 VAULT_ADDR

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (URL) |
| **Required** | ✅ Yes |
| **Description** | Vault server address |
| **Example** | `http://localhost:8200` (dev), `https://vault.internal:8200` (prod) |
| **Protocol** | HTTPS required for production |

---

### 7.2 VAULT_TOKEN

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (optional) |
| **Required** | No (dev mode only) |
| **Description** | Vault root token (development only) |
| **Security** | **NEVER** use in production |
| **Production** | Use AppRole authentication instead |

---

### 7.3 VAULT_ROLE_ID

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (optional) |
| **Required** | No (required for production AppRole auth) |
| **Description** | Vault AppRole role ID |
| **Security** | Store securely, not in repository |

---

### 7.4 VAULT_SECRET_ID

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (optional) |
| **Required** | No (required for production AppRole auth) |
| **Description** | Vault AppRole secret ID |
| **Security** | **CRITICAL** - Inject via CI/CD, rotate frequently |

---

### 7.5 VAULT_MOUNT_POINT

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | No |
| **Default** | `secret` |
| **Description** | Vault KV secrets engine mount point |
| **Example** | `secret`, `kv-v2` |

---

### 7.6 VAULT_FAIL_FAST

| Attribute | Value |
|-----------|-------|
| **Type** | `boolean` |
| **Required** | No |
| **Default** | `true` |
| **Description** | Fail application startup if Vault is unavailable |
| **Production** | **MUST** be `true` for security |
| **Development** | Can be `false` for local dev without Vault |

---

## 8. Open Policy Agent (OPA) Settings

### 8.1 OPA_URL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (URL) |
| **Required** | ✅ Yes |
| **Description** | OPA server URL |
| **Example** | `http://localhost:8181`, `http://opa.internal:8181` |
| **Default Port** | `8181` |

---

### 8.2 OPA_DECISION_PATH

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | OPA policy decision path |
| **Example** | `/v1/data/agentvoicebox/allow` |
| **Format** | Must include `/v1/data/` prefix |

---

### 8.3 OPA_TIMEOUT_SECONDS

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `3` |
| **Description** | OPA request timeout (seconds) |
| **Valid Range** | 1-10 |
| **Recommendation** | Keep low for fail-fast behavior |

---

### 8.4 OPA_ENABLED

| Attribute | Value |
|-----------|-------|
| **Type** | `boolean` |
| **Required** | No |
| **Default** | `true` |
| **Description** | Enable/disable OPA policy enforcement |
| **Production** | **MUST** be `true` |
| **Development** | Can be `false` for local testing |

---

## 9. Apache Kafka Settings

### 9.1 KAFKA_BOOTSTRAP_SERVERS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (comma-separated) |
| **Required** | ✅ Yes |
| **Description** | Kafka broker addresses |
| **Example** | `localhost:9092`, `kafka-1:9092,kafka-2:9092,kafka-3:9092` |
| **Format** | `host:port,host:port,...` |

---

### 9.2 KAFKA_CONSUMER_GROUP

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Kafka consumer group ID |
| **Example** | `agentvoicebox-backend` |
| **Note** | Unique per application instance |

---

### 9.3 KAFKA_ENABLED

| Attribute | Value |
|-----------|-------|
| **Type** | `boolean` |
| **Required** | No |
| **Default** | `false` |
| **Description** | Enable/disable Kafka event streaming |
| **Note** | Kafka is optional; can run without it |

---

### 9.4 KAFKA_SECURITY_PROTOCOL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (enum) |
| **Required** | No |
| **Default** | `PLAINTEXT` |
| **Valid Values** | `PLAINTEXT`, `SSL`, `SASL_PLAINTEXT`, `SASL_SSL` |
| **Production** | Use `SASL_SSL` for encryption + authentication |

---

## 10. Lago Billing Settings

### 10.1 LAGO_API_URL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (URL) |
| **Required** | ✅ Yes |
| **Description** | Lago billing API URL |
| **Example** | `http://localhost:3000`, `https://api.lago.example.com` |
| **Default Port** | `3000` (Lago default) |

---

### 10.2 LAGO_API_KEY

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (optional) |
| **Required** | No (required for production) |
| **Description** | Lago API key for authentication |
| **Security** | **CRITICAL** - Store in Vault |

---

### 10.3 LAGO_WEBHOOK_SECRET

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (optional) |
| **Required** | No (required for webhook validation) |
| **Description** | Secret for validating Lago webhook signatures |
| **Security** | Store in Vault |
| **Usage** | HMAC validation of incoming webhooks |

---

## 11. LLM Provider Settings

### 11.1 GROQ_API_KEY

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | No (required if using Groq) |
| **Description** | Groq API key for LLM access |
| **Security** | **CRITICAL** - Store in Vault |

---

### 11.2 GROQ_API_BASE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (URL) |
| **Required** | ✅ Yes |
| **Description** | Groq API base URL |
| **Default** | `https://api.groq.com/openai/v1` |

---

### 11.3 OPENAI_API_KEY

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | No (required if using OpenAI) |
| **Description** | OpenAI API key |
| **Security** | **CRITICAL** - Store in Vault |

---

### 11.4 OPENAI_API_BASE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (URL) |
| **Required** | ✅ Yes |
| **Description** | OpenAI API base URL |
| **Default** | `https://api.openai.com/v1` |

---

### 11.5 OLLAMA_BASE_URL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (URL) |
| **Required** | ✅ Yes |
| **Description** | Ollama self-hosted LLM base URL |
| **Example** | `http://localhost:11434`, `http://ollama.internal:11434` |

---

### 11.6 LLM_DEFAULT_PROVIDER

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (enum) |
| **Required** | ✅ Yes |
| **Valid Values** | `groq`, `openai`, `ollama` |
| **Description** | Default LLM provider |
| **Example** | `groq` |

---

### 11.7 LLM_DEFAULT_MODEL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Default LLM model name |
| **Example** | `llama-3.1-70b-versatile` (Groq), `gpt-4` (OpenAI) |

---

### 11.8 LLM_MAX_TOKENS

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Default max tokens for LLM completion |
| **Default** | `1024` |
| **Valid Range** | 1-32768 (model-dependent) |

---

### 11.9 LLM_TEMPERATURE

| Attribute | Value |
|-----------|-------|
| **Type** | `float` |
| **Required** | ✅ Yes |
| **Description** | Default LLM sampling temperature |
| **Default** | `0.7` |
| **Valid Range** | 0.0-2.0 |
| **Recommendation** | `0.7` for balanced creativity/determinism |

---

### 11.10 LLM_CIRCUIT_BREAKER_THRESHOLD

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Consecutive failures before circuit breaker opens |
| **Default** | `5` |
| **Valid Range** | 3-20 |

---

### 11.11 LLM_CIRCUIT_BREAKER_TIMEOUT

| Attribute | Value |
|-----------|-------|
| **Type** | `float` |
| **Required** | ✅ Yes |
| **Description** | Circuit breaker open duration (seconds) |
| **Default** | `30.0` |
| **Valid Range** | 10.0-300.0 |

---

### 11.12 LLM_MAX_HISTORY_ITEMS

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Max conversation history items sent to LLM |
| **Default** | `40` |
| **Valid Range** | 5-100 |
| **Note** | Higher values = more context but more tokens |

---

### 11.13 LLM_PROVIDER_PRIORITY

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (comma-separated) |
| **Required** | ✅ Yes |
| **Description** | LLM provider failover priority list |
| **Example** | `groq,openai,ollama` |
| **Usage** | First provider is primary, others are fallbacks |

---

## 12. STT (Speech-to-Text) Worker Settings

### 12.1 STT_MODEL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (enum) |
| **Required** | ✅ Yes |
| **Valid Values** | `tiny`, `base`, `small`, `medium`, `large`, `large-v2`, `large-v3` |
| **Description** | Whisper model size |
| **Default** | `base` |
| **Recommendation** | `base` for speed, `medium`/`large` for accuracy |

---

### 12.2 STT_DEVICE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (enum) |
| **Required** | ✅ Yes |
| **Valid Values** | `cpu`, `cuda`, `auto` |
| **Description** | Device for STT processing |
| **Default** | `auto` |
| **Note** | `auto` selects GPU if available |

---

### 12.3 STT_COMPUTE_TYPE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (enum) |
| **Required** | ✅ Yes |
| **Valid Values** | `int8`, `float16`, `float32` |
| **Description** | STT computation precision |
| **Default** | `float16` |
| **Trade-off** | `float16` = speed, `float32` = accuracy |

---

### 12.4 STT_BATCH_SIZE

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Max concurrent STT transcriptions |
| **Default** | `4` |
| **Valid Range** | 1-32 |
| **Tuning** | Adjust based on CPU/GPU capacity |

---

### 12.5 STT_SAMPLE_RATE

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Target sample rate for STT (Hz) |
| **Default** | `16000` |
| **Valid Values** | `8000`, `16000`, `22050`, `44100` |
| **Recommendation** | `16000` for voice, Whisper standard |

---

## 13. TTS (Text-to-Speech) Worker Settings

### 13.1 TTS_MODEL_DIR

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (path) |
| **Required** | ✅ Yes |
| **Description** | Kokoro ONNX model directory |
| **Example** | `/app/cache/kokoro`, `/models/tts` |
| **Note** | Must be writable for model downloads |

---

### 13.2 TTS_MODEL_FILE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (filename) |
| **Required** | ✅ Yes |
| **Description** | Kokoro ONNX model filename |
| **Default** | `kokoro-v1.0.onnx` |

---

### 13.3 TTS_VOICES_FILE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (filename) |
| **Required** | ✅ Yes |
| **Description** | Kokoro voices binary filename |
| **Default** | `voices-v1.0.bin` |

---

### 13.4 TTS_DEFAULT_VOICE

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Default TTS voice ID |
| **Default** | `am_onyx` |
| **Valid Values** | `am_onyx`, `am_puck`, `am_echo`, etc. (Kokoro voices) |

---

### 13.5 TTS_DEFAULT_SPEED

| Attribute | Value |
|-----------|-------|
| **Type** | `float` |
| **Required** | ✅ Yes |
| **Description** | Default TTS playback speed multiplier |
| **Default** | `1.1` |
| **Valid Range** | 0.5-2.0 |
| **Recommendation** | `1.0-1.2` for natural speech |

---

### 13.6 TTS_CHUNK_SIZE

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | TTS audio chunk size (samples) |
| **Default** | `24000` |
| **Note** | Affects streaming latency |

---

## 14. Worker Redis Streams

### 14.1 LLM Worker Streams

#### LLM_STREAM_REQUESTS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis stream name for LLM requests |
| **Default** | `llm:requests` |

#### LLM_GROUP_WORKERS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis consumer group for LLM workers |
| **Default** | `llm-workers` |

#### LLM_RESPONSE_CHANNEL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis channel prefix for LLM responses |
| **Default** | `llm:response` |

---

### 14.2 STT Worker Streams

#### STT_STREAM_AUDIO

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis stream name for STT audio input |
| **Default** | `audio:stt` |

#### STT_GROUP_WORKERS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis consumer group for STT workers |
| **Default** | `stt-workers` |

#### STT_CHANNEL_TRANSCRIPTION

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis channel prefix for transcription results |
| **Default** | `transcription` |

---

### 14.3 TTS Worker Streams

#### TTS_STREAM_REQUESTS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis stream name for TTS requests |
| **Default** | `tts:requests` |

#### TTS_GROUP_WORKERS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis consumer group for TTS workers |
| **Default** | `tts-workers` |

#### TTS_CHANNEL_TTS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis channel prefix for TTS control |
| **Default** | `tts` |

#### TTS_CHANNEL_AUDIO_OUT

| Attribute | Value |
|-----------|-------|
| **Type** | `string` |
| **Required** | ✅ Yes |
| **Description** | Redis stream prefix for TTS audio output |
| **Default** | `audio:out` |

---

## 15. Observability Settings

### 15.1 LOG_LEVEL

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (enum) |
| **Required** | No |
| **Default** | `INFO` |
| **Valid Values** | `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` |
| **Description** | Application logging level |
| **Validation** | Case-insensitive, auto-uppercased |
| **Production** | `INFO` or `WARNING` |
| **Development** | `DEBUG` |

---

### 15.2 LOG_FORMAT

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (enum) |
| **Required** | No |
| **Default** | `json` |
| **Valid Values** | `json`, `console` |
| **Description** | Log output format |
| **Production** | `json` for structured logging |
| **Development** | `console` for readability |

---

### 15.3 SENTRY_DSN

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (optional) |
| **Required** | No |
| **Description** | Sentry error tracking DSN |
| **Example** | `https://examplePublicKey@o0.ingest.sentry.io/0` |
| **Security** | Not highly sensitive, but keep private |

---

### 15.4 PROMETHEUS_ENABLED

| Attribute | Value |
|-----------|-------|
| **Type** | `boolean` |
| **Required** | No |
| **Default** | `true` |
| **Description** | Enable Prometheus metrics endpoint |
| **Production** | `true` |
| **Note** | Exposes `/metrics` endpoint |

---

## 16. CORS Settings

### 16.1 CORS_ALLOWED_ORIGINS

| Attribute | Value |
|-----------|-------|
| **Type** | `string` (comma-separated URLs) |
| **Required** | ✅ Yes |
| **Description** | Allowed CORS origins |
| **Example** | `http://localhost:3000,http://localhost:5173,https://app.agentvoicebox.com` |
| **Validation** | Parsed into Python list |
| **Production** | Only include production frontend URLs |

---

### 16.2 CORS_ALLOW_CREDENTIALS

| Attribute | Value |
|-----------|-------|
| **Type** | `boolean` |
| **Required** | No |
| **Default** | `true` |
| **Description** | Allow credentials (cookies, auth headers) in CORS requests |
| **Production** | `true` for cookie-based auth |

---

## 17. Rate Limiting Settings

### 17.1 Global Rate Limits

#### RATE_LIMIT_DEFAULT

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `60` |
| **Description** | Default rate limit (requests per minute) |
| **Valid Range** | 10-1000 |

#### RATE_LIMIT_API_KEY

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `120` |
| **Description** | Rate limit for API key authenticated requests |
| **Valid Range** | 10-1000 |

#### RATE_LIMIT_ADMIN

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | No |
| **Default** | `300` |
| **Description** | Rate limit for admin users |
| **Valid Range** | 100-10000 |

---

### 17.2 Realtime Session Rate Limits

#### REALTIME_REQUESTS_PER_MINUTE

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Realtime session requests per minute |
| **Default** | `100` |
| **Valid Range** | 10-1000 |

#### REALTIME_TOKENS_PER_MINUTE

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Realtime session tokens per minute |
| **Default** | `10000` |
| **Valid Range** | 1000-100000 |

#### REALTIME_RATE_LIMIT_WINDOW_SECONDS

| Attribute | Value |
|-----------|-------|
| **Type** | `integer` |
| **Required** | ✅ Yes |
| **Description** | Rate limit window duration (seconds) |
| **Default** | `60` |
| **Valid Values** | `60`, `300`, `3600` |

---

## 18. Configuration Validation Matrix

### 18.1 Startup Validation

All required configuration parameters are validated at application startup using Pydantic. The validation process:

1. **Load** environment variables from `.env` file (if present)
2. **Merge** with system environment variables
3. **Validate** data types, required fields, constraints
4. **Fail** immediately with detailed error message if invalid
5. **Export** validated settings to Django configuration

**Example Validation Error:**
```
==========================================================
CONFIGURATION ERROR: Missing or invalid environment variables
==========================================================
  - django_secret_key: Field required
  - db_host: Field required
  - log_level: Invalid log level: TRACE. Must be one of {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
==========================================================
```

---

### 18.2 Production Readiness Checklist

Before deploying to production, verify:

**Security:**
- ✅ `DJANGO_SECRET_KEY` - Unique, 50+ chars
- ✅ `DJANGO_DEBUG` = `false`
- ✅ `DB_PASSWORD` - Stored in Vault
- ✅ `KEYCLOAK_CLIENT_SECRET` - Stored in Vault
- ✅ `VAULT_FAIL_FAST` = `true`
- ✅ `OPA_ENABLED` = `true`
- ✅ All API keys (GROQ, OPENAI, LAGO) - Stored in Vault

**Network:**
- ✅ `DJANGO_ALLOWED_HOSTS` - Includes all public domains
- ✅ `CORS_ALLOWED_ORIGINS` - Only production frontend URLs
- ✅ All service URLs use HTTPS (not HTTP)
- ✅ `VOICE_AGENT_BASE_URL` - Public HTTPS URL
- ✅ `VOICE_AGENT_WS_BASE_URL` - Public WSS URL

**Performance:**
- ✅ `DB_CONN_MAX_AGE` - Appropriate for workload
- ✅ `REDIS_MAX_CONNECTIONS` - Tuned for concurrency
- ✅ `LLM_CIRCUIT_BREAKER_THRESHOLD` - Configured
- ✅ Rate limits configured for expected traffic

**Observability:**
- ✅ `LOG_FORMAT` = `json`
- ✅ `LOG_LEVEL` = `INFO` or `WARNING`
- ✅ `SENTRY_DSN` - Configured
- ✅ `PROMETHEUS_ENABLED` = `true`

---

## 19. Environment-Specific Configuration

### 19.1 Development

**File:** `backend/.env` (local only, `.gitignore`d)

**Key Settings:**
```bash
DJANGO_DEBUG=true
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
VOICE_AGENT_BASE_URL=http://localhost:65020
VOICE_AGENT_WS_BASE_URL=ws://localhost:65020

DB_HOST=localhost
REDIS_URL=redis://localhost:6379/0
KEYCLOAK_URL=http://localhost:65006
TEMPORAL_HOST=localhost:7233

VAULT_FAIL_FAST=false
OPA_ENABLED=false
KAFKA_ENABLED=false

LOG_FORMAT=console
LOG_LEVEL=DEBUG
```

---

### 19.2 Production

**Source:** Kubernetes Secrets + ConfigMaps

**Key Settings:**
```bash
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=api.agentvoicebox.com,*.agentvoicebox.com
VOICE_AGENT_BASE_URL=https://api.agentvoicebox.com
VOICE_AGENT_WS_BASE_URL=wss://api.agentvoicebox.com

DB_HOST=postgres.internal
REDIS_URL=redis://:password@redis.internal:6379/0
KEYCLOAK_URL=https://auth.agentvoicebox.com
TEMPORAL_HOST=temporal.internal:7233

VAULT_FAIL_FAST=true
OPA_ENABLED=true
KAFKA_ENABLED=true

LOG_FORMAT=json
LOG_LEVEL=INFO
SENTRY_DSN=https://...@sentry.io/...
```

---

## 20. UI Configuration Mapping

### 20.1 Setup Wizard Sections

The Setup Wizard UI (`view-setup.ts`) exposes these configuration groups:

| UI Section | Configuration Parameters | Count |
|------------|-------------------------|-------|
| **PostgreSQL Database** | `DB_*` | 6 |
| **Redis Cache** | `REDIS_*` | 9 |
| **Keycloak Auth** | `KEYCLOAK_*` | 4 |
| **Temporal Workflows** | `TEMPORAL_*` + worker streams | 12 |
| **Vault Secrets** | `VAULT_*` | 6 |
| **OPA Policies** | `OPA_*` | 4 |
| **Kafka Events** | `KAFKA_*` | 4 |
| **Lago Billing** | `LAGO_*` | 3 |
| **LLM Providers** | `GROQ_*`, `OPENAI_*`, `OLLAMA_*`, `LLM_*` | 14 |
| **STT Worker** | `STT_*` | 5 |
| **TTS Worker** | `TTS_*` | 6 |
| **App Settings** | `DJANGO_*`, `CORS_*`, `RATE_LIMIT_*`, `LOG_*` | 15 |

**Total:** 88+ configurable parameters

---

### 20.2 API Endpoints for Configuration

The Setup Wizard will interact with these backend APIs:

**Read Configuration:**
- `GET /api/v2/admin/settings` - Get all current settings
- `GET /api/v2/admin/settings/{category}` - Get category settings

**Update Configuration:**
- `PUT /api/v2/admin/settings` - Update all settings
- `PATCH /api/v2/admin/settings/{category}` - Update category

**Test Connections:**
- `POST /api/v2/admin/settings/test-postgres` - Test database connection
- `POST /api/v2/admin/settings/test-redis` - Test Redis connection
- `POST /api/v2/admin/settings/test-keycloak` - Test Keycloak connection
- etc.

**Validation:**
- All updates trigger Pydantic validation
- Invalid settings rejected with detailed error message
- Settings persisted to `.env` file or ConfigMap (deployment-specific)

---

## Appendices

### A. Complete Environment Variable List

**Total Count:** 100+ parameters

**Categories:**
1. Django Core: 7
2. PostgreSQL: 6
3. Redis: 9
4. Keycloak: 4
5. Temporal: 3
6. Vault: 6
7. OPA: 4
8. Kafka: 4
9. Lago: 3
10. LLM: 14
11. STT: 5
12. TTS: 6
13. Worker Streams: 10
14. Observability: 4
15. CORS: 2
16. Rate Limiting: 6

---

### B. Security Best Practices

1. **Never commit** `.env` files to version control
2. **Always use** Vault for production secrets
3. **Rotate** database passwords, API keys quarterly
4. **Enable** OPA and Vault fail-fast in production
5. **Use** HTTPS/WSS for all production URLs
6. **Set** strong passwords (16+ chars, alphanumeric + symbols)
7. **Limit** allowed hosts and CORS origins to known domains
8. **Configure** rate limits to prevent abuse

---

### C. Troubleshooting Guide

**Problem:** Application won't start

**Solutions:**
1. Check validation errors in console output
2. Verify all required env vars are set
3. Test service connectivity (DB, Redis, Keycloak)
4. Check Vault availability (if `VAULT_FAIL_FAST=true`)

**Problem:** Keycloak authentication fails

**Solutions:**
1. Verify `KEYCLOAK_URL` is accessible
2. Check realm name matches
3. Confirm client ID/secret are correct
4. Test token validation manually

**Problem:** Workers not processing jobs

**Solutions:**
1. Check Redis connectivity
2. Verify Redis stream names match configuration
3. Confirm consumer groups are created
4. Check worker logs for errors

---

## 13. Worker Streams Configuration

These settings configure Redis Streams for inter-service communication between Django API and workers.

### 13.1 LLM Stream Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `LLM_STREAM_REQUESTS` | `string` | `llm:requests` | Redis stream name for LLM request queue |
| `LLM_GROUP_WORKERS` | `string` | `llm-workers` | Redis consumer group name for LLM workers |
| `LLM_RESPONSE_CHANNEL` | `string` | `llm:response` | Redis pub/sub channel for LLM responses |

### 13.2 STT Stream Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `STT_STREAM_AUDIO` | `string` | `audio:stt` | Redis stream name for audio chunks to STT |
| `STT_GROUP_WORKERS` | `string` | `stt-workers` | Redis consumer group name for STT workers |
| `STT_CHANNEL_TRANSCRIPTION` | `string` | `transcription` | Redis pub/sub channel for transcription results |

### 13.3 TTS Stream Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `TTS_STREAM_REQUESTS` | `string` | `tts:requests` | Redis stream name for TTS requests |
| `TTS_GROUP_WORKERS` | `string` | `tts-workers` | Redis consumer group name for TTS workers |
| `TTS_CHANNEL_TTS` | `string` | `tts` | Redis pub/sub channel for TTS control |
| `TTS_CHANNEL_AUDIO_OUT` | `string` | `audio:out` | Redis pub/sub channel for synthesized audio |

---

**Document Version:** 1.1.0  
**Last Updated:** 2026-01-12  
**Maintained By:** SOMA Engineering Team  
**Review Cycle:** Quarterly or when new parameters added
