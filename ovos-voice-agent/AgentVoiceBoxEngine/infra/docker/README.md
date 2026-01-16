# AgentVoiceBox Docker Deployment

This deployment uses two compose files:
1) **Shared services** in `infra/standalone/docker-compose.yml`
2) **Application stack** in `docker-compose.yml`

## 📋 Port Allocation (65000-65099 Range)

| Service | External Port | Internal Port | Container Name | RAM |
|---------|---------------|---------------|----------------|-----|
| **Vault** | 65003 | 8200 | `shared_vault` | 512MB |
| **PostgreSQL** | 65004 | 5432 | `shared_postgres` | 512MB |
| **Redis** | 65005 | 6379 | `shared_redis` | 512MB |
| **Keycloak** | 65006 | 8080 | `shared_keycloak` | 2GB |
| **Temporal** | 65007 | 7233 | `shared_temporal` | 1.5GB |
| **Django API** | 65020 | 8000 | `avb-django-api` | 1.5GB |
| **Portal Frontend** | 65027 | 65027 | `avb-portal-frontend` | 512MB |
| **Prometheus** | 65011 | 9090 | `avb-prometheus` | 512MB |
| **LLM Worker** | - | - | `avb-worker-llm` | 2GB |
| **STT Worker** | - | - | `avb-worker-stt` | 1.5GB |
| **TTS Worker** | - | - | `avb-worker-tts` | 1GB |

**Total RAM: ~15GB** (8GB infrastructure + 7GB application)

---

## 🚀 Quick Start

### Step 1: Initialize Volumes
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/agentVoiceBox/ovos-voice-agent/AgentVoiceBoxEngine/infra/docker
chmod +x init-volumes.sh
./init-volumes.sh
```

### Step 2: Start Shared Services
```bash
# Start shared services first
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/agentVoiceBox/ovos-voice-agent/AgentVoiceBoxEngine/infra/standalone
docker compose -p shared-services up -d

# Monitor startup
docker compose -p shared-services logs -f
```

### Step 3: Start Application Stack
```bash
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/agentVoiceBox/ovos-voice-agent/AgentVoiceBoxEngine
docker compose -p agentvoicebox up -d
docker compose -p agentvoicebox logs -f
```

### Optional: Deploy Script
If you prefer a scripted workflow, use `deploy.sh` (runs the same sequence):

```bash
./deploy.sh                    # Full deployment
./deploy.sh --app-only         # Start all services
./deploy.sh --status           # Service status
./deploy.sh --health           # Health checks
./deploy.sh --logs             # All logs
./deploy.sh --stop             # Stop all services
./deploy.sh --reset            # Remove all data
```

### Step 4: Verify Deployment
```bash
# Check all services
docker compose -p agentvoicebox ps

# Test health endpoints
curl http://localhost:65020/health/
curl http://localhost:65020/health/ready/

# Verify API docs
open http://localhost:65020/api/v2/docs

# Verify Portal
open http://localhost:65027

# Verify Keycloak Admin
open http://localhost:65006/admin
# Credentials: admin / adminpassword123
```

---

## 🔧 Configuration

### Environment Variables
Copy the example environment file and customize as needed:

```bash
cp .env.example .env
# Edit .env with your API keys and secrets
```

**Required for LLM Worker:**
- `GROQ_API_KEY` or `OPENAI_API_KEY`

**Optional (defaults provided):**
- `DJANGO_SECRET_KEY`
- `DB_PASSWORD`
- `KEYCLOAK_ADMIN_PASSWORD`
- `OLLAMA_BASE_URL`

### Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| Portal Frontend | http://localhost:65027 | Web UI |
| Django API | http://localhost:65020/api/v2 | REST API |
| API Docs | http://localhost:65020/api/v2/docs | OpenAPI |
| WebSockets | ws://localhost:65020/ws/v2/... | Real-time |
| Keycloak | http://localhost:65006 | Auth |
| PostgreSQL | localhost:65004 | DB |
| Redis | localhost:65005 | Cache |
| Vault | http://localhost:65003 | Secrets |
| Temporal | localhost:65007 | Workflows |
| Prometheus | http://localhost:65011 | Metrics |

---

## 📈 Observability Stack

Prometheus runs with the main stack:
- Prometheus: http://localhost:65011 (`avb-prometheus`)

---

## 🌐 WebSocket Endpoints

```javascript
// Events Stream
ws://localhost:65020/ws/v2/events?token=<JWT>

// Session Management
ws://localhost:65020/ws/v2/sessions/{session_id}?token=<JWT>

// Speech-to-Text
ws://localhost:65020/ws/v2/stt/transcription?token=<JWT>

// Text-to-Speech
ws://localhost:65020/ws/v2/tts/stream?token=<JWT>
```

**Authentication:** Pass Keycloak JWT as query parameter (`?token=`) or `Authorization: Bearer` header.

---

## 📊 Resource Allocation

### Shared Services (8GB)
```
PostgreSQL:      2GB (shared_admin/shared_secure_2024)
Redis:           1GB
Keycloak:        3GB (admin/adminpassword123)
Vault:           512MB (devtoken)
Temporal:        1.5GB
```

### Application Stack (7GB)
```
Django API:      1.5GB (REST + WebSocket)
Portal Frontend: 512MB (Lit 3 + Bun)
Prometheus:      512MB
LLM Worker:      2GB (Groq/OpenAI/Ollama)
STT Worker:      1.5GB (Whisper)
TTS Worker:      1GB (Kokoro)
```

### Limits and Requests
```
Shared Services (Limit / Request):
PostgreSQL:  2GB / 1GB
Redis:       1GB / 512MB
Keycloak:    3GB / 1.5GB
Vault:       512MB / 256MB
Temporal:    1.5GB / 768MB

Application (Limit / Request):
Django API:      1.5GB / 768MB
Portal Frontend: 512MB / 128MB
Prometheus:      512MB / 256MB
LLM Worker:      2GB / 1GB
STT Worker:      1.5GB / 768MB
TTS Worker:      1GB / 512MB
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Portal Frontend                          │
│                    Port: 65027                              │
│                    Container: avb-portal-frontend           │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Django API Gateway                       │
│              REST: /api/v2/*  ·  WS: /ws/v2/*              │
│                    Port: 65020                              │
│                    Container: avb-django-api                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Shared Infrastructure Services                 │
│  PostgreSQL · Redis · Keycloak · Vault · Temporal · OPA    │
│  Ports: 65003-65007, 65011                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Worker Services                          │
│  LLM (Groq/OpenAI/Ollama) · STT (Whisper) · TTS (Kokoro)  │
│  Containers: avb-worker-llm, avb-worker-stt, avb-worker-tts│
└─────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Management Commands

### View Status
```bash
# All services
docker compose -p agentvoicebox ps

# Specific service
docker compose -p agentvoicebox ps django-api
```

### View Logs
```bash
# All services
docker compose -p agentvoicebox logs -f

# Specific service
docker compose -p agentvoicebox logs -f django-api
```

### Restart Services
```bash
# Restart specific service
docker compose -p agentvoicebox restart django-api

# Restart all
docker compose -p agentvoicebox restart
```

### Stop Services
```bash
# Stop all services
docker compose -p agentvoicebox down

# Stop everything (including volumes)
docker compose -p agentvoicebox down -v
```

### View Resource Usage
```bash
# All containers
docker stats

# Specific container
docker stats avb-django-api
```

---

## 🔍 Troubleshooting

### 1. Port Conflicts
```bash
# Check what's using ports
lsof -i :65020
lsof -i :65027

# Kill conflicting process
kill -9 <PID>
```

### 2. Network Issues
```bash
# Check networks
docker network ls

# Inspect network
docker network inspect infra_docker_avb-network

# Create if missing
docker network create --subnet=172.26.0.0/16 infra_docker_avb-network
```

### 3. Service Health Issues
```bash
# Check service status
docker compose -p agentvoicebox ps

# View recent logs
docker compose -p agentvoicebox logs --tail=50 django-api

# Restart service
docker compose -p agentvoicebox restart django-api

# Check container health
docker inspect avb-django-api | grep -A 10 Health
```

### 4. Database Connection Issues
```bash
# Test PostgreSQL
docker exec -it shared_postgres psql -U shared_admin -d shared -c "SELECT 1;"

# Test Redis
docker exec -it shared_redis redis-cli PING

# Check Django DB connection
docker exec -it avb-django-api python manage.py check --database default
```

### 5. Worker Issues
```bash
# Check worker logs
docker compose -p agentvoicebox logs -f worker-llm

# Verify Redis connectivity from worker
docker exec -it avb-worker-llm python -c "import redis; r=redis.Redis.from_url('redis://redis:6379/4'); print(r.ping())"
```

### 6. Keycloak Issues
```bash
# Check Keycloak logs
cd /Users/macbookpro201916i964gb1tb/Documents/GitHub/agentVoiceBox/ovos-voice-agent/AgentVoiceBoxEngine/infra/standalone
docker compose -p shared-services logs -f keycloak

# Verify Keycloak is responding
curl http://localhost:65006/health/ready

# Access admin console
open http://localhost:65006/admin
# Credentials: admin / adminpassword123
```

---

## 📝 Environment-Specific Configurations

### Development (Default)
- Debug mode: OFF (hardened)
- CORS: Allowed for localhost ports
- Logging: Console format
- Health checks: Enabled
- Resource limits: As specified

### Production Considerations
For production deployment, you should:

1. **Secrets Management**
   - Use Vault for all credentials
   - Remove secrets from docker-compose.yml
   - Use Docker secrets or external secret management

2. **TLS/SSL**
   - Add reverse proxy (nginx) with certificates
   - Enable HTTPS for all services
   - Use Let's Encrypt or corporate certificates

3. **Network Security**
   - Restrict container communication
   - Use firewall rules
   - Implement network policies

4. **Monitoring & Alerting**
   - Set up Prometheus alerts
   - Implement log aggregation (ELK/EFK)

5. **Backup Strategy**
   - Regular PostgreSQL backups
   - Redis persistence verification
   - Keycloak realm backups

6. **High Availability**
   - Multiple replicas for critical services
   - Load balancer configuration
   - Database replication

---

## 🎯 Success Criteria

Deployment is successful if:

✅ All services start without errors  
✅ Health checks pass for all services  
✅ API responds with valid JSON on http://localhost:65020/health/  
✅ Portal frontend loads on http://localhost:65027  
✅ API docs accessible on http://localhost:65020/api/v2/docs  
✅ Keycloak admin console accessible  
✅ PostgreSQL accepts connections  
✅ Redis responds to PING  
✅ WebSocket endpoints accept connections  
✅ No critical errors in logs  

---

## 📚 Additional Resources

- **Main Documentation:** `../../README.md`
- **Local Development:** `../../docs/LOCAL_DEVELOPMENT.md`
- **Architecture:** `../../ARCHITECTURE.md`
- **API Reference:** http://localhost:65020/api/v2/docs (when running)

---

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review service logs with `docker compose -p agentvoicebox logs -f`
3. Verify all prerequisites are met
4. Ensure ports 65000-65099 are available
5. Check Docker Desktop resource limits (15GB+ RAM recommended)

---

**Deployment Status:** Ready for execution  
**Last Updated:** January 8, 2026  
**Configuration Version:** 1.0.0 (Tilt Mirror)
