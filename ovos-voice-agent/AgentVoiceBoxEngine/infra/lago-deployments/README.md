# Lago Billing - Production Multi-Tenant Cluster Deployment

**COMPLETELY ISOLATED** from AgentVoiceBox main infrastructure (65xxx range).
Multi-tenant architecture supporting millions of transactions.

> [!IMPORTANT]
> All configuration via Django environment variables. Secrets stored in Vault.

## Port Allocation (63690-63699)

| Service | Port | Purpose |
|---------|------|---------|
| Lago API | 63690 | REST API |
| Lago Front | 63691 | Dashboard UI |
| Lago PostgreSQL | 63692 | Database |
| Lago Redis | 63693 | Cache/Queue |
| Lago PDF | 63694 | Invoice PDF Generator |

## Quick Start

```bash
# Start Lago cluster
docker compose -p lago up -d

# View logs
docker compose -p lago logs -f

# Stop cluster
docker compose -p lago down
```

## Access

- **Dashboard**: http://localhost:63691
- **API**: http://localhost:63690
- **API Docs**: http://localhost:63690/api/v1/docs

## Default Credentials

| Service | User | Password |
|---------|------|----------|
| PostgreSQL | lago | lago_production_2024 |
| Lago Admin | (sign up via dashboard) | - |

## Services

| Container | Image | Memory | Purpose |
|-----------|-------|--------|---------|
| `lago-api` | getlago/api:v1.39.0 | 1.5GB | Main API |
| `lago-worker` | getlago/api:v1.39.0 | 1GB | Sidekiq jobs |
| `lago-clock` | getlago/api:v1.39.0 | 256MB | Scheduled tasks |
| `lago-front` | getlago/front:v1.39.0 | 512MB | Dashboard |
| `lago-pdf` | getlago/lago-gotenberg:7 | 512MB | PDF generation |
| `lago-db` | postgres:14-alpine | 2GB | Database |
| `lago-redis` | redis:6-alpine | 512MB | Cache |

**Total RAM**: ~6GB

## Integration with AgentVoiceBox

Configure in Django settings via environment variables:

```bash
# .env
LAGO_API_URL=http://localhost:63690
LAGO_API_KEY=${VAULT}  # Retrieved from Vault
LAGO_WEBHOOK_SECRET=${VAULT}  # Retrieved from Vault
```

## Network

Isolated network: `lago_network`

Does NOT share network with AgentVoiceBox infrastructure (65xxx range).
