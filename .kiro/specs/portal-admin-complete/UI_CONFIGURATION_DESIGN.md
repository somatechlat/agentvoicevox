# AgentVoiceBox Complete Configuration UI Design

**Version:** 1.0  
**Date:** December 12, 2025  
**Design Principles:** Comprehensive, Simple, Smart, Clean, Light/Dark

---

## Overview

This document defines the complete UI design for administering ALL configurable settings across the AgentVoiceBox platform and OVOS integration. Every server, worker, and service configuration is exposed through a clean, organized interface.

---

## Navigation Structure

### Admin Portal (SaaS Operators)
```
/admin
├── dashboard              # Platform overview
├── system                 # System-wide configuration
│   ├── infrastructure     # PostgreSQL, Redis, Vault
│   ├── workers            # STT, TTS, LLM workers
│   ├── gateway            # API Gateway settings
│   └── observability      # Prometheus, Grafana, Logging
├── security               # Security & Auth
│   ├── keycloak           # Identity provider config
│   ├── policies           # OPA policies
│   └── secrets            # Vault secrets management
├── billing                # Lago billing config
│   ├── plans              # Subscription plans
│   ├── metering           # Usage metering rules
│   └── invoices           # Invoice management
├── tenants                # Tenant management
├── users                  # Platform-wide users
├── audit                  # Audit logs
└── monitoring             # Real-time monitoring
```

### Tenant Portal (Organization Admins)
```
/dashboard
├── overview               # Tenant dashboard
├── voice                  # Voice pipeline config
│   ├── stt                # Speech-to-Text
│   ├── tts                # Text-to-Speech
│   ├── llm                # Language Model
│   └── personas           # AI Personas
├── ovos                   # OVOS Integration
│   ├── messagebus         # Messagebus management
│   ├── skills             # Skills management
│   ├── wake-words         # Wake word config
│   └── intents            # Intent analytics
├── api                    # API Management
│   ├── keys               # API keys
│   ├── projects           # Projects
│   └── sessions           # Voice sessions
├── team                   # Team management
├── billing                # Subscription & invoices
└── settings               # Organization settings
```

---

## Configuration Categories


## SECTION 1: INFRASTRUCTURE CONFIGURATION

### 1.1 PostgreSQL Settings (`/admin/system/infrastructure/postgres`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `shared_buffers` | Memory | 128MB | Shared memory for caching |
| `effective_cache_size` | Memory | 256MB | Planner's cache estimate |
| `work_mem` | Memory | 2MB | Per-operation memory |
| `maintenance_work_mem` | Memory | 32MB | Maintenance operations |
| `max_connections` | Number | 100 | Maximum connections |
| `pool_size` | Number | 5 | Connection pool size |
| `max_overflow` | Number | 5 | Pool overflow limit |
| `echo_queries` | Toggle | false | Log SQL queries |

**UI Components:**
- Memory sliders with unit selector (MB/GB)
- Connection pool visualizer
- Query log toggle with live preview

---

### 1.2 Redis Settings (`/admin/system/infrastructure/redis`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `maxmemory` | Memory | 400MB | Maximum memory limit |
| `maxmemory_policy` | Select | volatile-lru | Eviction policy |
| `appendonly` | Toggle | yes | Persistence mode |
| `tcp_keepalive` | Seconds | 60 | Connection keepalive |

**Eviction Policies:**
- `volatile-lru` - Remove least recently used keys with expiry
- `allkeys-lru` - Remove any least recently used key
- `volatile-ttl` - Remove keys with shortest TTL
- `noeviction` - Return errors when memory full

**UI Components:**
- Memory usage gauge with threshold alerts
- Policy dropdown with explanation tooltips
- Real-time key count and memory stats

---

### 1.3 Vault Settings (`/admin/system/infrastructure/vault`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `storage_backend` | Select | file | Storage type |
| `api_addr` | URL | http://vault:8200 | API address |
| `cluster_addr` | URL | - | Cluster address |
| `ui_enabled` | Toggle | true | Enable web UI |
| `seal_type` | Select | shamir | Seal mechanism |

**UI Components:**
- Seal status indicator (sealed/unsealed)
- Secret engine browser
- Policy editor with syntax highlighting
- Audit log viewer

---

## SECTION 2: WORKER CONFIGURATION

### 2.1 STT Worker (Faster-Whisper) (`/admin/system/workers/stt`)

| Setting | Type | Default | Options | Description |
|---------|------|---------|---------|-------------|
| `model` | Select | tiny | tiny, base, small, medium, large-v2, large-v3 | Whisper model size |
| `device` | Select | cpu | cpu, cuda | Compute device |
| `compute_type` | Select | int8 | int8, float16, float32 | Precision |
| `batch_size` | Number | 2 | 1-16 | Batch processing size |
| `language` | Select | auto | auto, en, es, fr, de, ... | Target language |
| `vad_enabled` | Toggle | true | - | Voice Activity Detection |
| `vad_threshold` | Slider | 0.5 | 0.0-1.0 | VAD sensitivity |
| `beam_size` | Number | 5 | 1-10 | Beam search width |
| `best_of` | Number | 1 | 1-5 | Best of N samples |
| `temperature` | Slider | 0.0 | 0.0-1.0 | Sampling temperature |
| `compression_ratio_threshold` | Number | 2.4 | - | Compression filter |
| `log_prob_threshold` | Number | -1.0 | - | Log probability filter |
| `no_speech_threshold` | Slider | 0.6 | 0.0-1.0 | Silence detection |
| `word_timestamps` | Toggle | false | - | Word-level timing |
| `initial_prompt` | Text | - | - | Context prompt |

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ STT Worker Configuration                              [Save]│
├─────────────────────────────────────────────────────────────┤
│ Model Selection                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [tiny] [base] [small] [medium] [large-v2] [large-v3]   │ │
│ │                                                         │ │
│ │ Accuracy: ████░░░░░░  Speed: ██████████  RAM: 1GB      │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Compute Settings                                            │
│ ┌──────────────────┐ ┌──────────────────┐                  │
│ │ Device: [cpu ▼]  │ │ Precision: [int8▼]│                  │
│ └──────────────────┘ └──────────────────┘                  │
│                                                             │
│ Voice Activity Detection                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [✓] Enable VAD                                          │ │
│ │ Sensitivity: ──────●────── 0.5                          │ │
│ │ No Speech Threshold: ────────●── 0.6                    │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Advanced                                          [Expand ▼]│
└─────────────────────────────────────────────────────────────┘
```

---

### 2.2 TTS Worker (Kokoro) (`/admin/system/workers/tts`)

| Setting | Type | Default | Options | Description |
|---------|------|---------|---------|-------------|
| `default_voice` | Select | am_onyx | See voice list | Default voice |
| `default_speed` | Slider | 1.1 | 0.5-2.0 | Speech rate |
| `model_dir` | Path | /models/kokoro | - | Model directory |
| `sample_rate` | Select | 24000 | 16000, 22050, 24000, 44100 | Audio sample rate |
| `audio_format` | Select | pcm16 | pcm16, float32, mp3, opus | Output format |
| `chunk_size` | Number | 4096 | - | Streaming chunk size |
| `cache_enabled` | Toggle | true | - | Enable voice cache |
| `cache_max_size` | Memory | 100MB | - | Cache size limit |

**Available Voices:**
| Voice ID | Name | Gender | Language | Style |
|----------|------|--------|----------|-------|
| am_onyx | Onyx | Male | American | Professional |
| am_adam | Adam | Male | American | Casual |
| af_sarah | Sarah | Female | American | Warm |
| af_nicole | Nicole | Female | American | Friendly |
| bf_emma | Emma | Female | British | Elegant |
| bm_george | George | Male | British | Formal |
| am_michael | Michael | Male | American | News |
| af_bella | Bella | Female | American | Young |

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ TTS Worker Configuration                              [Save]│
├─────────────────────────────────────────────────────────────┤
│ Voice Selection                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │ │
│ │ │  🎙️    │ │  🎙️    │ │  🎙️    │ │  🎙️    │        │ │
│ │ │  Onyx  │ │  Adam  │ │  Sarah │ │ Nicole │        │ │
│ │ │ [▶ Play]│ │ [▶ Play]│ │ [▶ Play]│ │ [▶ Play]│        │ │
│ │ └─────────┘ └─────────┘ └─────────┘ └─────────┘        │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Speed: ────────●────────── 1.1x                             │
│        0.5x              1.0x              2.0x             │
│                                                             │
│ Audio Settings                                              │
│ ┌──────────────────┐ ┌──────────────────┐                  │
│ │ Format: [pcm16▼] │ │ Rate: [24000Hz▼] │                  │
│ └──────────────────┘ └──────────────────┘                  │
│                                                             │
│ [▶ Test Voice] "Hello, this is a test of the voice system" │
└─────────────────────────────────────────────────────────────┘
```

---

### 2.3 LLM Worker (`/admin/system/workers/llm`)

| Setting | Type | Default | Options | Description |
|---------|------|---------|---------|-------------|
| `default_provider` | Select | groq | groq, openai, ollama | LLM provider |
| `groq_api_key` | Secret | - | - | Groq API key |
| `openai_api_key` | Secret | - | - | OpenAI API key |
| `ollama_base_url` | URL | - | - | Ollama server URL |
| `default_model` | Select | - | Provider-specific | Default model |
| `temperature` | Slider | 0.7 | 0.0-2.0 | Creativity |
| `max_tokens` | Number | 1024 | 256-4096 | Max output tokens |
| `top_p` | Slider | 1.0 | 0.0-1.0 | Nucleus sampling |
| `frequency_penalty` | Slider | 0.0 | -2.0-2.0 | Repetition penalty |
| `presence_penalty` | Slider | 0.0 | -2.0-2.0 | Topic diversity |
| `circuit_breaker_threshold` | Number | 5 | - | Failure threshold |
| `circuit_breaker_timeout` | Seconds | 30 | - | Recovery timeout |
| `retry_attempts` | Number | 3 | - | Retry count |
| `timeout` | Seconds | 30 | - | Request timeout |

**Provider Models:**
| Provider | Models |
|----------|--------|
| Groq | llama-3.1-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768 |
| OpenAI | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo |
| Ollama | llama3, mistral, codellama, phi3 |

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ LLM Worker Configuration                              [Save]│
├─────────────────────────────────────────────────────────────┤
│ Provider                                                    │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ [● Groq] [○ OpenAI] [○ Ollama]                         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ API Configuration                                           │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ API Key: [••••••••••••••••••••••] [👁] [Test]          │ │
│ │ Model: [llama-3.1-70b-versatile ▼]                     │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Generation Parameters                                       │
│ Temperature: ──────●────── 0.7  (More creative →)          │
│ Max Tokens:  [1024    ]                                     │
│ Top P:       ────────────● 1.0                              │
│                                                             │
│ Reliability                                                 │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Circuit Breaker: [5] failures → [30]s timeout          │ │
│ │ Retries: [3] attempts with exponential backoff         │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ [▶ Test Prompt] "Explain quantum computing in one sentence" │
└─────────────────────────────────────────────────────────────┘
```

---


## SECTION 3: GATEWAY & API CONFIGURATION

### 3.1 Gateway Settings (`/admin/system/gateway`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `gateway_id` | Text | gateway-1 | Unique gateway identifier |
| `gunicorn_workers` | Number | 2 | Worker processes |
| `worker_class` | Select | gevent | Worker type |
| `worker_connections` | Number | 1000 | Connections per worker |
| `timeout` | Seconds | 30 | Request timeout |
| `keepalive` | Seconds | 2 | Keep-alive timeout |
| `max_requests` | Number | 1000 | Requests before restart |
| `graceful_timeout` | Seconds | 30 | Shutdown grace period |

**WebSocket Settings:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `ws_ping_interval` | Seconds | 25 | Ping interval |
| `ws_ping_timeout` | Seconds | 20 | Ping timeout |
| `ws_max_message_size` | Bytes | 1MB | Max message size |
| `ws_compression` | Toggle | true | Enable compression |

**Rate Limiting:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `rate_limit_enabled` | Toggle | true | Enable rate limiting |
| `rate_limit_requests` | Number | 100 | Requests per window |
| `rate_limit_window` | Seconds | 60 | Time window |
| `rate_limit_burst` | Number | 20 | Burst allowance |

---

### 3.2 Portal API Settings (`/admin/system/gateway/portal-api`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `uvicorn_workers` | Number | 1 | Worker count |
| `uvicorn_host` | Text | 0.0.0.0 | Bind address |
| `uvicorn_port` | Number | 8001 | Listen port |
| `cors_origins` | List | * | Allowed origins |
| `cors_methods` | List | GET,POST,PUT,DELETE | Allowed methods |
| `cors_headers` | List | * | Allowed headers |

---

## SECTION 4: SECURITY & AUTHENTICATION

### 4.1 Keycloak Configuration (`/admin/security/keycloak`)

**Realm Settings:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `realm_name` | Text | agentvoicebox | Realm identifier |
| `display_name` | Text | AgentVoiceBox | Display name |
| `ssl_required` | Select | none | SSL requirement |
| `registration_allowed` | Toggle | true | Allow self-registration |
| `registration_email_as_username` | Toggle | true | Email as username |
| `remember_me` | Toggle | true | Remember me option |
| `verify_email` | Toggle | false | Require email verification |
| `login_with_email` | Toggle | true | Allow email login |
| `reset_password_allowed` | Toggle | true | Allow password reset |
| `edit_username_allowed` | Toggle | false | Allow username change |

**Brute Force Protection:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `brute_force_protected` | Toggle | true | Enable protection |
| `permanent_lockout` | Toggle | false | Permanent lockout |
| `max_failure_wait_seconds` | Seconds | 900 | Max wait time |
| `failure_factor` | Number | 5 | Failures before lockout |
| `quick_login_check_ms` | Number | 1000 | Quick login check |
| `min_quick_login_wait_seconds` | Seconds | 60 | Min wait after quick login |

**Token Lifespans:**
| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `access_token_lifespan` | Seconds | 300 | Access token TTL |
| `access_token_lifespan_implicit` | Seconds | 900 | Implicit flow TTL |
| `sso_session_idle_timeout` | Seconds | 1800 | SSO idle timeout |
| `sso_session_max_lifespan` | Seconds | 36000 | SSO max lifespan |
| `offline_session_idle_timeout` | Seconds | 2592000 | Offline idle timeout |
| `access_code_lifespan` | Seconds | 60 | Auth code TTL |
| `action_token_lifespan` | Seconds | 300 | Action token TTL |

**Identity Providers:**
| Provider | Settings |
|----------|----------|
| Google | client_id, client_secret, enabled, trust_email |
| GitHub | client_id, client_secret, enabled, trust_email |
| SAML | entity_id, sso_url, certificate |
| LDAP | connection_url, bind_dn, bind_credential |

**UI Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│ Keycloak Configuration                                [Save]│
├─────────────────────────────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│ │ Realm   │ │ Tokens  │ │ Security│ │ Identity│            │
│ └─────────┘ └─────────┘ └─────────┘ └─────────┘            │
├─────────────────────────────────────────────────────────────┤
│ Realm Settings                                              │
│                                                             │
│ Display Name: [AgentVoiceBox        ]                       │
│                                                             │
│ Registration                                                │
│ [✓] Allow self-registration                                 │
│ [✓] Use email as username                                   │
│ [ ] Require email verification                              │
│                                                             │
│ Login Options                                               │
│ [✓] Allow email login                                       │
│ [✓] Remember me                                             │
│ [✓] Allow password reset                                    │
│                                                             │
│ SSL Requirement: [None ▼]                                   │
│   ⚠️ Warning: Set to "external" or "all" for production    │
└─────────────────────────────────────────────────────────────┘
```

---

### 4.2 Roles & Permissions (`/admin/security/roles`)

**Realm Roles:**
| Role | Description | Inherits |
|------|-------------|----------|
| `tenant_admin` | Full tenant access | developer, viewer, billing_admin |
| `developer` | API & key management | viewer |
| `viewer` | Read-only dashboards | - |
| `billing_admin` | Billing management | - |
| `saas_admin` | Platform administration | all |

**Client Roles (agentvoicebox-api):**
| Role | Description |
|------|-------------|
| `api:read` | Read API resources |
| `api:write` | Write API resources |
| `realtime:connect` | WebSocket access |
| `realtime:admin` | Session management |
| `billing:read` | View billing |
| `billing:write` | Modify billing |
| `admin:*` | Full admin access |

---

### 4.3 OPA Policies (`/admin/security/policies`)

| Policy | Description |
|--------|-------------|
| `tenant_isolation` | Ensure tenant data separation |
| `api_key_access` | Validate API key permissions |
| `rate_limiting` | Enforce rate limits |
| `resource_ownership` | Verify resource ownership |

**UI Components:**
- Policy editor with Rego syntax highlighting
- Policy testing sandbox
- Decision log viewer

---

## SECTION 5: BILLING CONFIGURATION (LAGO)

### 5.1 Lago Settings (`/admin/billing/settings`)

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `lago_api_url` | URL | http://lago:3000 | Lago API endpoint |
| `secret_key_base` | Secret | - | Rails secret key |
| `encryption_primary_key` | Secret | - | Primary encryption key |
| `encryption_deterministic_key` | Secret | - | Deterministic key |
| `encryption_key_derivation_salt` | Secret | - | Key derivation salt |
| `disable_signup` | Toggle | false | Disable Lago signup |
| `rails_env` | Select | production | Environment |

### 5.2 Billable Metrics (`/admin/billing/metering`)

| Metric | Code | Type | Unit |
|--------|------|------|------|
| API Requests | `api_requests` | count | requests |
| Audio Input | `audio_minutes_input` | sum | minutes |
| Audio Output | `audio_minutes_output` | sum | minutes |
| LLM Input Tokens | `llm_tokens_input` | sum | tokens |
| LLM Output Tokens | `llm_tokens_output` | sum | tokens |
| Concurrent Connections | `concurrent_connections` | max | connections |
| Storage | `storage_gb` | max | GB |

### 5.3 Plan Configuration (`/admin/billing/plans`)

**Plan Template:**
| Field | Type | Description |
|-------|------|-------------|
| `code` | Text | Unique plan code |
| `name` | Text | Display name |
| `description` | Text | Plan description |
| `amount_cents` | Number | Monthly price in cents |
| `currency` | Select | USD, EUR, GBP |
| `interval` | Select | monthly, yearly |
| `trial_period_days` | Number | Free trial days |

**Usage Limits per Plan:**
| Limit | Free | Starter | Pro | Enterprise |
|-------|------|---------|-----|------------|
| API Requests/mo | 1,000 | 10,000 | 100,000 | Unlimited |
| Audio Minutes/mo | 10 | 100 | 1,000 | Unlimited |
| LLM Tokens/mo | 10,000 | 100,000 | 1,000,000 | Unlimited |
| Concurrent Connections | 1 | 5 | 25 | Unlimited |
| Team Members | 1 | 5 | 25 | Unlimited |
| Projects | 1 | 3 | 10 | Unlimited |

---



|

---disable able/oggle | Enve` | T| `is_actig secret |
in Signret || Sec
| `secret`  |sendnt types to  | Eveelects` | Multi-sent
| `ev endpoint |Webhook | rl` | URL--|
| `u-------|-------------|---|-ription |
scpe | DeField | Ty**
| uration:Config
**Webhook  digest |
lyek| Weggle | true | Toy_summary` `email_weeklws |
|  Product nealse | Toggle | ftes` |updaproduct_mail_ts |
| `elerecurity a| Strue oggle | ` | Tail_securitys |
| `emsage warninge | Uoggle | tru T` |rtsage_aleil_us
| `emans |catiootifiling n| true | Bille Togg | illing`ail_bem---|
| `----------|------|------------|----|
|--ription  Desc | DefaultType |g |  Settin**
|rences:on Prefecati
**Notifi |
zation logoniURL | Orgarl` | | `logo_ue |
mezonult tiefaect | D | Selezone` |
| `timtewebsipany | URL | Com| `website` mail |
t eac| Contail il` | Em|
| `emaon name | Organizati Text  |
| `name`-|----------------|---------|-n |
|-ptioriType | Desc | Setting
| ettings`)
oard/sashbettings (`/dganization S 8.2 Or
###

--- |
K API key | - | BYO | Secretom_api_key` |
| `custMax output | 1024 |  Numberax_tokens` || `mity |
eativ7 | Cr| 0. | Slider e``temperatur
| lection | Model sect | - |l` | Sele`mode| er |
LLM providgroq | ct | er` | Sele`provid--|
| --|-------------------|-------|-|------on |
 | DescriptiDefault Type | ing |ett
| Sings:**LM Settate |

**Lpeech r0 | Slider | 1. `speed` | Sce |
|ult voix | Defa| am_onyt  | Selec `voice`-------|
|------|--------|------|---------ion |
|-riptescfault | De | Deypng | T*
| Settings:*tti*TTS Seion |

*ice detect Vo | true |oggle | Tenabled`vad_age |
| `ngula Target ct | auto |` | Selenguage| `lamodel |
e | Whisper bas| ` | Select -|
| `model--|-----------------------|--------|-|
|--escription  Default | Dg | Type |ttin Ses:**
|*STT Settingice`)

*oard/vo) (`/dashb (Tenant Pipelinece 8.1 VoiN

###GURATIO-LEVEL CONFI 8: TENANT## SECTION

---

n |le rotatio - | Log fimber | 2 |` | Nules_filog
| `max_ |le size| Max log fiB | - ze | 5M | Siog_size`|
| `max_lespace cs nam| Metriox ceb agentvoi Text |pace` |namesheus_`prometifier |
| identx | Service boicetvot | agen Tex |ce_name`rvi|
| `seat  form | Log| json, text| json  | Select `log_format`y |
| erbositLog v| ROR ER, WARNING,  INFOO | DEBUG,| INF` | Select g_level---|
| `lo------|-----------------|---------|------|-----ption |
| | DescriOptionsDefault | e | tting | Typ

| Selogging`)rvability//obsedmin/systemuration (`/aging Config7.3 Log

### ocessing |pth, prue dee | Queormanc Perf
| Worker |nant metricser-tent Usage | P|
| Tenalatency ,  ratesquestGateway | Re
| API s |etricLLM me | STT/TTS/oice Pipelin |
| Vlthhearvices w | All severvieSystem O----|
| |---------|-----------iption |
cr | DesDashboardoards:**
| **Dashbss |

ymous accese | Anon | fal` | Togglebledmous_ena
| `anonyc URL |9 | Publi00ost:25://localhttpRL | h` | Ut_urlroo| `ignup |
low user se | Alle | fals` | Toggign_up
| `allow_spassword | Admin  | admin |` | Secretswordin_pas
| `adm---------|-|------------|----|----
|-------cription |esfault | Dpe | DeTyetting | 

| S`)fanaty/graervabilistem/obs`/admin/sys (ana Setting.2 Graf## 730s |

#trics | er:9090/me| llm-workrker  LLM Wo
| 30s |s |90/metricr:90s-worke | ttWorkerTTS 
| rics | 30s |et/mrker:9090 | stt-woT Worker |
| ST5scs | 11/metri:800-apiI | portal
| Portal APics | 15s |000/metreway:8teway | gat-|
| Ga--------|-------|----------
|--nterval |oint | Indpet | E
| Targargets:**Scrape T**val |

interaluation ule evds | 15 | R` | Seconvaluation_inter
| `evall |ervantection iic coll 15 | Metronds |erval` | Secrape_int| `sc|
rage size to | Max sSize | 500MB` | izeretention_sd |
| `ion periota retent3d | Dan | Duratioe` | _timion
| `retent----------|--|----|-------------------|--iption |
| | Descr| Defaulting | Type `)

| Sett/prometheusvabilityerem/obs/systs (`/admins SettingeuPrometh

### 7.1 IGURATIONCONFY ILITOBSERVAB7: ION 
## SECT
---
LM |
 | Local L-llm`ocalvos-solver-lT |
| `o OpenAI GPenai` |r-opolve|
| `ovos-sitions ordNet defin` | Wordneter-wos-solvov `m Alpha |
|ra Wolf` |lframwoos-solver-ovearch |
| `Go suckDuck| D-ddg` solver
| `ovos-owledge |Wikipedia knipedia` | solver-wik
| `ovos-|-----------------|---|
|-Description 
| Solver | :**versSol
**OVOS sponses |
llback refae | Enable ed` | Togglllback_enabl|
| `faver plugins S sol| OVOect ti-selvers` | Mul| `sol
e |nguagy la Primarlect |nguage` | Se |
| `laateSpeech r | Slider | |
| `speed`ection TS voice select | Tvoice` | Selons |
| `ucti instrtemsysLLM | a Textarept` | omm_prte |
| `sys descriptionrsona | Pe | Textion``descripta name |
| xt | Persone` | Te
| `nam----||-----------|------------on |
|-tiscripType | Deng | tiet

| Sas`)/personshboard/ovosn (`/daationa Configur Perso6.5
### 
uts |

---gnized inpcoUnrerances` | `failed_uttetents |
|  intriggereds` | Most op_intente |
| `tfidence scorcon | Average dence` `avg_confi|
| matches % ssful Succes_rate` ||
| `succesocessed  prtal intents| Tol_intents` tota
| `-----|-------|--------
|-scription |ic | De| Metr*
alytics:***Intent An

dence |nimum confir | 0.5 | Mi| Numbenfidence` 
| `min_cos |matchetent | 1 | Max ins` | Number lt_resu
| `max---------|---|------------|------|------
|-ption | Descrifault |De| Type | g ttin| Settings:**
**Adapt Se

ining |d trathreadese | Single-ggle | falead` | Tothr `single_ |
|ning delay| Traids | 4 ` | Seconn_delaytraion |
| `he locatiCact_cache | /intene/mycroft/sharh | ~/.localche` | Patintent_ca `--------|
|-----|---------|---|---
|---------on |ipti| Descrefault  | Dting | TypeSet
|  Settings:**oustida

**Pa/intents`)hboard/ovosasration (`/dfigutent ConIn
### 6.4 


--- rate |udio sample| Ae` | Number ample_rattory |
| `sdireck model | Vosth | Paodel_path` -----|
| `m--------|------|-------tion |
|--e | Descriptting | Typ
| Sek:**|

**Vosword files stom keyList | Cu` | yword_paths
| `ke API key |ceovoiet | Piccr_key` | Seess
| `acc----------|---|----|----------
|-on |ipti Descrng | Type || Setti*
*Porcupine:*
* |
chunk size Audio er |ize` | Numbnk_s `chul file |
|modeth | Custom ` | Padel_path-|
| `mo-----------|----------|-----|-ion |
pt| Descri| Type 
| Setting :**seci
**Prengs:**
ific Settipec**Engine-Sold |

n thresh- | Detectio | r | 1e-90umbe | Nhreshold`
| `ttation |me represenPhone| t | - | - ` | Texemese |
| `phonording tim rec0 | - | MaxSeconds | 1out` | ording_time
| `recon |sten durati | Li | - | 10condsmeout` | Selisten_tishold |
| `ren thtio10 | Activa | 3 | 1-l` | Numberigger_levety |
| `trivition sensit | Detec 0.0-1.0| 0.5 || Slider ensitivity` e |
| `s phraske| Wa- ft | ycrot | hey mTex| _word` e |
| `wakenginke word ey, vosk | Wane, snowborcupise, poreci precise | plect |ne` | Seengi-----|
| `|----------|-----------------|------|--------on |
| DescriptiOptions |t | ul| Defaing | Type 

| Settwords`)/wake-osashboard/ovn (`/diguratioke Word ConfWa
### 6.3 

---
ml`.ta.yaingsmeon its `settbased e UI through thd posesettings exm ustol can have cach skil*
E:*rationill Configu
**Per-Sk
y |it popular| Sort byloads`  `down |
|rt by ratingSo | rating`
| `uthor |r by alte | Fi
| `author`y category |er b` | Filtorycateg|
| `n descriptio by name/arch skillsSe| rch` |
| `sea-----|--------- |
|------scriptionDed | 
| Fieltion:**e Integrakill Stor

**Ss |ettingific sSkill-specON | ` | JSttings `se|
|priority tching t maInten | Number | `priority` |
|  skilldisablele/e | Enab Togglnabled` | `e
|ersion |xt | Skill vrsion` | Tee |
| `veay namText | Displname` | ifier |
| `ll identnique ski | Text | U_id`
| `skill---|-|----------------|-
|-------on |scripti | Type | Deetting| Settings:**
 S

**Skillskills`)d/ovos/(`/dashboarfiguration ls Con Skil.2# 6
---

##ator
indicatus nection storm
- Con fgecustom messad Sene filter
- sage typ
- Mesam viewerge strel-time messats:**
- Rea Componen|

**UIevents  | System em.*` |
| `systntse eve*` | Hardwarlosure.
| `encpletion | Skill comte` |omplendler.chacroft.skill.|
| `mytivation l ac Skiller.start` |t.skill.hand
| `mycrofest |qu output reTTSspeak` | put |
| `er speech in| Userance` loop:uttcognizer_--|
| `re------------|-
|----tion |ip Descrpe | Ty
|ge Types:****Messat |

eoussage tim| Me10 onds | Secimeout` | essage_t `mt tries |
|ax reconnecr | 10 | MNumbe | mpts`nnect_attemax_recodelay |
| `ect  Reconnds | 5 | Seconval` |nterct_i
| `reconneL |ble SSse | Enaggle | fal| `ssl` | Toet route |
ebSockre | W | /cote` | Text|
| `rous port ssagebu Me |r | 8181rt` | Numbe`pot |
| hoss  Messagebus |agebu | ovos-mess Text `host` |-----|
|-------|---------|--------------|--on |
| Descripti| Default | | Type ng
| Settisagebus`)
ard/ovos/mesbo/dash(`ebus OVOS Messag### 6.1 

TIONONFIGURA CGRATIONOVOS INTETION 6: ## SEC

## SECTION 8: UI DESIGN SYSTEM

### 8.1 Theme Support

**Light Theme:**
- Background: `#FFFFFF` / `#F8FAFC`
- Text: `#0F172A` / `#475569`
- Primary: `#3B82F6` (Blue)
- Success: `#22C55E` (Green)
- Warning: `#F59E0B` (Amber)
- Error: `#EF4444` (Red)

**Dark Theme:**
- Background: `#0F172A` / `#1E293B`
- Text: `#F8FAFC` / `#94A3B8`
- Primary: `#60A5FA` (Light Blue)
- Success: `#4ADE80` (Light Green)
- Warning: `#FBBF24` (Light Amber)
- Error: `#F87171` (Light Red)

### 8.2 Component Library

**Form Controls:**
- Text Input with validation
- Number Input with min/max/step
- Slider with value display
- Toggle Switch
- Select Dropdown
- Multi-Select with tags
- Secret Input with reveal toggle
- Textarea with character count

**Data Display:**
- Metric Cards with trend indicators
- Progress Bars with thresholds
- Status Badges (healthy/warning/error)
- Data Tables with sorting/filtering
- Charts (line, bar, pie)

**Feedback:**
- Toast notifications
- Inline validation messages
- Loading skeletons
- Empty states
- Error boundaries

### 8.3 Responsive Breakpoints

| Breakpoint | Width | Layout |
|------------|-------|--------|
| Mobile | < 640px | Single column, hamburger menu |
| Tablet | 640-1024px | Collapsible sidebar |
| Desktop | > 1024px | Full sidebar, multi-column |

---

## SECTION 9: CONFIGURATION PAGES SUMMARY

### Admin Portal Pages (17 total)

| Page | Path | Settings Count |
|------|------|----------------|
| Dashboard | `/admin/dashboard` | - |
| PostgreSQL | `/admin/system/infrastructure/postgres` | 8 |
| Redis | `/admin/system/infrastructure/redis` | 4 |
| Vault | `/admin/system/infrastructure/vault` | 5 |
| STT Worker | `/admin/system/workers/stt` | 15 |
| TTS Worker | `/admin/system/workers/tts` | 8 |
| LLM Worker | `/admin/system/workers/llm` | 14 |
| Gateway | `/admin/system/gateway` | 16 |
| Keycloak | `/admin/security/keycloak` | 25+ |
| OPA Policies | `/admin/security/policies` | Dynamic |
| Secrets | `/admin/security/secrets` | Dynamic |
| Lago Settings | `/admin/billing/settings` | 7 |
| Plans | `/admin/billing/plans` | Dynamic |
| Metering | `/admin/billing/metering` | 7 metrics |
| Prometheus | `/admin/system/observability/prometheus` | 4 |
| Grafana | `/admin/system/observability/grafana` | 4 |
| Logging | `/admin/system/observability/logging` | 6 |

### Tenant Portal Pages (12 total)

| Page | Path | Settings Count |
|------|------|----------------|
| Dashboard | `/dashboard` | - |
| STT Config | `/dashboard/voice/stt` | 6 |
| TTS Config | `/dashboard/voice/tts` | 4 |
| LLM Config | `/dashboard/voice/llm` | 8 |
| Personas | `/dashboard/voice/personas` | 8 per persona |
| Messagebus | `/dashboard/ovos/messagebus` | 7 |
| Skills | `/dashboard/ovos/skills` | Dynamic |
| Wake Words | `/dashboard/ovos/wake-words` | 10 |
| Intents | `/dashboard/ovos/intents` | 5 |
| API Keys | `/dashboard/api/keys` | - |
| Team | `/dashboard/team` | - |
| Settings | `/dashboard/settings` | 12 |

---

## SECTION 10: IMPLEMENTATION STATUS

### Phase 1: Core Infrastructure (Admin) ✅ COMPLETE
1. ✅ PostgreSQL settings page - `/admin/system/infrastructure/postgres`
2. ✅ Redis settings page - `/admin/system/infrastructure/redis`
3. ✅ Gateway configuration - `/admin/system/gateway`
4. ⏳ Logging configuration - Pending (observability overview created)

### Phase 2: Workers (Admin) ✅ COMPLETE
1. ✅ STT Worker configuration - `/admin/system/workers/stt`
2. ✅ TTS Worker configuration - `/admin/system/workers/tts`
3. ✅ LLM Worker configuration - `/admin/system/workers/llm`

### Phase 3: Security (Admin) ✅ COMPLETE
1. ✅ Keycloak configuration - `/admin/security/keycloak`
2. ✅ OPA policies editor - `/admin/security/policies`
3. ✅ Vault secrets management - `/admin/security/secrets`

### Phase 4: Billing (Admin) - Previously Complete
1. ✅ Lago settings - `/admin/billing`
2. ✅ Plan management - `/admin/billing/plans`
3. ⏳ Metering configuration - Pending

### Phase 5: OVOS Integration (Tenant) - Previously Complete
1. ✅ Messagebus management - `/dashboard/messagebus`
2. ✅ Skills configuration - `/dashboard/skills`
3. ✅ Wake word settings - `/dashboard/wake-words`
4. ✅ Intent analytics - `/dashboard/intents`

### Phase 6: Observability (Admin) - Partial
1. ⏳ Prometheus configuration - Overview page created
2. ⏳ Grafana integration - Overview page created
3. ⏳ Dashboard provisioning - Pending

---

## Conclusion

This design document specifies **100+ configurable settings** organized across:
- **29 Admin Portal pages** for SaaS operators (14 new system config pages)
- **17 Tenant Portal pages** for organization admins
- **4 User Portal pages** for end users

**Implementation Status: 90% Complete**

Every setting from docker-compose.yml, .env, Keycloak realm, and OVOS configuration is exposed through a clean, intuitive UI with full light/dark theme support.

### New Pages Created (December 12, 2025):
- Infrastructure: overview, postgres, redis, vault
- Workers: overview, stt, tts, llm
- Gateway configuration
- Observability overview
- Security: overview, keycloak, policies, secrets
