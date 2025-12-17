<p align="center">
  <img src="https://raw.githubusercontent.com/OpenVoiceOS/ovos-media/main/logos/ovos-logo.png" alt="AgentVoiceVox Logo" width="200"/>
</p>

<h1 align="center">AgentVoiceVox</h1>

<p align="center">
  <strong>Enterprise Voice AI Platform with OpenAI Realtime API Compatibility</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api-reference">API</a> •
  <a href="#deployment">Deployment</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License"/>
  <img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python"/>
  <img src="https://img.shields.io/badge/Next.js-14-black.svg" alt="Next.js"/>
  <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="Docker"/>
  <img src="https://img.shields.io/badge/OpenAI%20API-compatible-orange.svg" alt="OpenAI Compatible"/>
</p>

---

## What is AgentVoiceVox?

AgentVoiceVox is a **production-ready, self-hosted voice AI platform** that provides OpenAI Realtime API compatibility using 100% open-source infrastructure. Deploy your own voice agents with complete data sovereignty, no vendor lock-in, and predictable costs.

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR APPLICATION                         │
│                    (OpenAI SDK Compatible)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       AgentVoiceVox                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────────────┐    │
│  │   STT   │  │   LLM   │  │   TTS   │  │  SaaS Portal    │    │
│  │ Whisper │  │  Groq   │  │ Kokoro  │  │  (Multi-tenant) │    │
│  └─────────┘  └─────────┘  └─────────┘  └─────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Why AgentVoiceVox?

| Problem | AgentVoiceVox Solution |
|---------|------------------------|
| 💸 **High API costs** | Self-host everything, pay only for compute |
| 🔒 **Data privacy concerns** | Your data never leaves your infrastructure |
| 🌐 **Vendor lock-in** | OpenAI-compatible API, swap providers anytime |
| 📈 **Unpredictable scaling costs** | Fixed infrastructure costs, unlimited usage |
| 🏢 **Enterprise compliance** | SOC2/GDPR/HIPAA-ready architecture |

---

## Features

### 🎙️ Voice Processing Pipeline
- **Speech-to-Text**: Faster-Whisper (GPU/CPU) with <500ms latency
- **Text-to-Speech**: Kokoro ONNX with streaming, 20+ voices
- **LLM Integration**: OpenAI, Groq, Anthropic, Ollama (self-hosted)

### 🏗️ Enterprise Architecture
- **Multi-tenant SaaS**: Complete tenant isolation, per-tenant quotas
- **Horizontal Scaling**: Stateless gateways, 50K connections per instance
- **High Availability**: Redis Cluster, PostgreSQL replication, auto-failover

### 🔐 Security & Compliance
- **Authentication**: Keycloak SSO (SAML/OIDC), API keys with Argon2id
- **Authorization**: Role-based access control (RBAC)
- **Secrets Management**: HashiCorp Vault integration
- **Policy Engine**: OPA (Open Policy Agent) for fine-grained access control
- **Encryption**: TLS 1.3 in transit, AES-256 at rest
- **Audit Logging**: Complete audit trail with 7-year retention

### 💰 Billing & Monetization
- **Usage Metering**: API calls, audio minutes, LLM tokens
- **Billing Engine**: Lago integration with Stripe/PayPal
- **Pricing Models**: Free tier, usage-based, enterprise plans

### 📊 Observability
- **Metrics**: Prometheus with p50/p95/p99 latency histograms
- **Dashboards**: Pre-built Grafana dashboards
- **Logging**: Structured JSON with correlation IDs
- **Tracing**: OpenTelemetry support

### 🖥️ Multi-Portal Architecture

The platform includes three distinct portal experiences:

| Portal | Path | Purpose |
|--------|------|---------|
| **Admin Portal** | `/admin/*` | System administration, infrastructure monitoring, security settings |
| **Customer Portal** | `/dashboard/*` | Voice configuration, STT/TTS/LLM settings, personas, skills |
| **User Portal** | `/app/*` | End-user sessions, API keys, personal settings |

---

## Quick Start

### Prerequisites
- Docker & Docker Compose v2.20+
- 10GB RAM minimum (16GB recommended)
- (Optional) NVIDIA GPU for faster inference

### 1. Clone & Configure

```bash
git clone https://github.com/somatechlat/agentvoicevox.git
cd agentvoicevox

# Copy environment template
cp settings.example.env .env

# Add your LLM API key (at least one required)
echo "GROQ_API_KEY=your-key-here" >> .env
# or
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### 2. Start the Platform

```bash
# Start all services
docker compose -p agentvoicevox up -d

# Check service health
docker compose -p agentvoicevox ps
```

### 3. Access Services

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| **Portal** | http://localhost:25007 | Sign up or use demo |
| **API Gateway** | ws://localhost:25000/v1/realtime | API key from portal |
| **Keycloak Admin** | http://localhost:25004 | admin / admin |
| **Grafana** | http://localhost:25009 | admin / admin |
| **Lago Billing** | http://localhost:25005 | Configure in portal |

### 4. Test the API

```python
# pip install openai
from openai import OpenAI

client = OpenAI(
    api_key="your-api-key-from-portal",
    base_url="http://localhost:25000/v1"
)

# Use exactly like OpenAI's API
response = client.chat.completions.create(
    model="agentvoicevox-1",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### 5. WebSocket Realtime API

```javascript
// OpenAI Realtime API compatible
const ws = new WebSocket('ws://localhost:25000/v1/realtime', {
  headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
});

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: 'session.update',
    session: { voice: 'am_onyx', instructions: 'You are a helpful assistant.' }
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data.type);
};
```

---

## Architecture

```
                                    Internet
                                       │
                                       ▼
                    ┌──────────────────────────────────────┐
                    │         NGINX / Load Balancer        │
                    │     (WebSocket-aware, SSL/TLS)       │
                    └──────────────────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │  Gateway Pod 1   │    │  Gateway Pod 2   │    │  Gateway Pod N   │
    │  (50K conn each) │    │  (50K conn each) │    │  (50K conn each) │
    └──────────────────┘    └──────────────────┘    └──────────────────┘
              │                        │                        │
              └────────────────────────┼────────────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │   Redis Cluster  │    │    PostgreSQL    │    │   Redis Streams  │
    │  (Session State) │    │   (Persistence)  │    │  (Work Queues)   │
    └──────────────────┘    └──────────────────┘    └──────────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              ▼                        ▼                        ▼
    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
    │   STT Workers    │    │   LLM Workers    │    │   TTS Workers    │
    │ (Faster-Whisper) │    │ (Groq/OpenAI)    │    │  (Kokoro ONNX)   │
    └──────────────────┘    └──────────────────┘    └──────────────────┘
```

### Component Overview

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Gateway** | Flask + Gevent | WebSocket termination, auth, routing |
| **Portal Frontend** | Next.js 14 + Tailwind | Multi-tenant SaaS dashboard |
| **STT Worker** | Faster-Whisper | Speech-to-text transcription |
| **TTS Worker** | Kokoro ONNX | Text-to-speech synthesis |
| **LLM Worker** | Groq/OpenAI/Ollama | Language model inference |
| **Session Store** | Redis 7 | Distributed session state |
| **Database** | PostgreSQL 16 | Persistent storage |
| **Identity** | Keycloak 24 | SSO, user management, RBAC |
| **Secrets** | HashiCorp Vault | Secrets management |
| **Policy** | OPA | Fine-grained authorization |
| **Billing** | Lago | Usage metering, invoicing |
| **Monitoring** | Prometheus + Grafana | Metrics, dashboards |

---

## Project Structure

```
AgentVoiceVox/
├── app/                        # Flask backend application
│   ├── models/                 # SQLAlchemy models (tenant, session)
│   ├── routes/                 # REST API endpoints
│   ├── services/               # Business logic (billing, metering, audit)
│   ├── transports/             # WebSocket handlers
│   ├── observability/          # Logging, metrics, tracing
│   └── tts/                    # TTS provider abstraction
├── portal/                     # Portal backend API
├── portal-frontend/            # Next.js SaaS portal
│   ├── src/app/                # App Router pages
│   │   ├── admin/              # Admin portal (system, security, infra)
│   │   ├── dashboard/          # Customer portal (voice config)
│   │   └── app/                # User portal (sessions, API keys)
│   ├── src/components/         # UI components (Radix + Tailwind)
│   ├── src/contexts/           # React contexts (Auth)
│   └── src/services/           # API clients
├── workers/                    # STT/TTS/LLM worker processes
├── migrations/                 # Alembic database migrations
├── keycloak/                   # Keycloak realm configuration
├── lago/                       # Lago billing seed data
├── vault/                      # Vault configuration
├── policies/                   # OPA Rego policies
├── observability/              # Prometheus/Grafana configs
├── docker/                     # Docker configurations
├── tests/                      # Python test suites
├── docker-compose.yml          # Development stack
├── docker-compose.ssl.yml      # SSL-enabled stack
└── Makefile                    # Development commands
```

---

## API Reference

### REST Endpoints

```
POST   /v1/realtime/sessions      Create session (get ephemeral token)
GET    /v1/realtime/sessions/:id  Get session details
DELETE /v1/realtime/sessions/:id  Close session

POST   /v1/audio/transcriptions   One-shot STT
POST   /v1/audio/speech           One-shot TTS
GET    /v1/tts/voices             List available voices

GET    /health                    Health check
GET    /metrics                   Prometheus metrics
```

### WebSocket Events (OpenAI Compatible)

**Client → Server:**
```json
{ "type": "session.update", "session": { "voice": "am_onyx" } }
{ "type": "input_audio_buffer.append", "audio": "<base64>" }
{ "type": "input_audio_buffer.commit" }
{ "type": "response.create" }
{ "type": "response.cancel" }
```

**Server → Client:**
```json
{ "type": "session.created", "session": { "id": "sess_xxx" } }
{ "type": "conversation.item.created", "item": { ... } }
{ "type": "response.audio.delta", "delta": "<base64>" }
{ "type": "response.done" }
{ "type": "error", "error": { "type": "rate_limit_error" } }
```

### Available Voices

| Voice ID | Description | Language |
|----------|-------------|----------|
| `am_onyx` | Deep male voice | English |
| `af_bella` | Warm female voice | English |
| `am_adam` | Neutral male voice | English |
| `af_sarah` | Professional female | English |
| `am_michael` | Friendly male | English |

---

## Port Allocation

| Port | Service |
|------|---------|
| 25000 | Gateway API (WebSocket/REST) |
| 25001 | Portal Backend API |
| 25002 | PostgreSQL |
| 25003 | Redis |
| 25004 | Keycloak |
| 25005 | Lago API |
| 25007 | Portal Frontend |
| 25008 | Prometheus |
| 25009 | Grafana |

---

## Development

### Backend Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
make install-dev

# Run tests
make test

# Format code
make format

# Lint
make lint
```

### Frontend Setup

```bash
cd portal-frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Run tests
npm run test

# Type check
npm run type-check
```

### Docker Commands

```bash
# Start full stack
make docker-up

# View logs
make docker-logs

# Stop and cleanup
make docker-down

# Run with SSL
docker compose -f docker-compose.yml -f docker-compose.ssl.yml up -d
```

---

## Configuration

### Environment Variables

```bash
# Required - At least one LLM provider
GROQ_API_KEY=gsk_xxx                    # Groq API key
OPENAI_API_KEY=sk-xxx                   # OpenAI API key

# Database
DATABASE__URI=postgresql+psycopg://user:pass@host:5432/db

# Redis
REDIS__URL=redis://localhost:6379/0

# Keycloak
KEYCLOAK_URL=http://keycloak:8080
KEYCLOAK_REALM=agentvoicevox

# TTS Configuration
TTS_DEFAULT_VOICE=am_onyx               # Default voice
TTS_DEFAULT_SPEED=1.1                   # Speech speed (0.5-2.0)

# STT Configuration
STT_MODEL=tiny                          # tiny, base, small, medium, large
STT_DEVICE=cpu                          # cpu or cuda
```

---

## Performance

### Latency Targets (p99)

| Operation | Target | Typical |
|-----------|--------|---------|
| WebSocket message | <50ms | 15ms |
| STT transcription | <500ms | 200ms |
| TTS first byte | <200ms | 80ms |
| LLM first token | <300ms | 150ms |
| End-to-end | <1.5s | 800ms |

### Resource Requirements

| Deployment | RAM | CPU | GPU | Connections |
|------------|-----|-----|-----|-------------|
| **Development** | 10GB | 4 cores | Optional | 100 |
| **Small** | 32GB | 8 cores | 1x T4 | 10,000 |
| **Medium** | 64GB | 16 cores | 2x T4 | 50,000 |
| **Large** | 128GB+ | 32+ cores | 4x A10 | 100,000+ |

---

## Testing

### Backend Tests

```bash
# Unit tests
make test

# With coverage
pytest --cov=app tests/

# Property-based tests
pytest tests/ -k "property"
```

### Frontend Tests

```bash
cd portal-frontend

# Unit tests (Vitest)
npm run test

# E2E tests (Playwright)
npm run test:e2e

# Coverage
npm run test:coverage
```

---

## Roadmap

- [x] OpenAI Realtime API compatibility
- [x] Multi-tenant SaaS architecture
- [x] Keycloak SSO integration
- [x] Lago billing integration
- [x] Customer self-service portal
- [x] Admin portal with infrastructure monitoring
- [x] HashiCorp Vault integration
- [x] OPA policy engine
- [ ] Kubernetes Helm charts
- [ ] Multi-region deployment
- [ ] Custom voice cloning
- [ ] RAG integration
- [ ] Mobile SDKs (iOS/Android)

---

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

Built with these amazing open-source projects:

- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) - Fast STT inference
- [Kokoro](https://github.com/thewh1teagle/kokoro-onnx) - High-quality TTS
- [Keycloak](https://www.keycloak.org/) - Identity management
- [Lago](https://www.getlago.com/) - Usage-based billing
- [HashiCorp Vault](https://www.vaultproject.io/) - Secrets management
- [Open Policy Agent](https://www.openpolicyagent.org/) - Policy engine
- [OpenVoiceOS](https://openvoiceos.org/) - Voice assistant framework

---

<p align="center">
  <strong>Built with ❤️ by SomaTech</strong>
</p>

<p align="center">
  <a href="https://github.com/somatechlat/agentvoicevox/stargazers">⭐ Star us on GitHub</a>
</p>
