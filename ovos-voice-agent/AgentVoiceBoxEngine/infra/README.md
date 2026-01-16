# Infrastructure Deployment Overview

**ISO/IEC 29148:2018 Compliant - AgentVoiceBox v1.0.0**

## 1. Purpose
This document unifies the infrastructure deployment guidance for **Standalone** and **SaaS** environments.
It replaces the previous split documentation to avoid duplication and ensure a single canonical reference.

## 2. Deployment Modes

### 2.1 Standalone (Local or Single-Instance)
**Use case**: Local development or single-instance deployments.

**Services and Ports**
| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL 16 | 65004 | Primary database |
| Redis 7 | 65005 | Cache and sessions |
| Keycloak 24 | 65006 | Authentication |
| Vault 1.15 | 65003 | Secrets management |
| Temporal 1.23 | 65007 | Workflow engine |

**RAM Budget**: 8GB

**Usage**
```bash
cd infra/standalone
docker compose up -d
docker compose ps
```

---

### 2.2 SaaS (Multi-Tenant Production)
**Use case**: Production multi-tenant deployment with cloud-managed services.

**Directory Structure**
```
saas/
├── docker/                 # Docker Compose for SaaS
│   └── docker-compose.yml
├── k8s/                    # Kubernetes manifests
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── django-api.yaml
│   ├── portal-frontend.yaml
│   └── workers.yaml
└── helm/                   # Helm charts (future)
    └── agentvoicebox/
```

**Key Differences from Standalone**
| Aspect | Standalone | SaaS |
|--------|------------|------|
| Tenancy | Single | Multi-tenant |
| Database | Local Postgres | Cloud-managed (RDS/CloudSQL) |
| Cache | Local Redis | Cloud-managed (ElastiCache/Memorystore) |
| Auth | Local Keycloak | Keycloak cluster / Auth0 |
| Secrets | Local Vault | Cloud KMS + Vault cluster |
| Scaling | Fixed | Horizontal Pod Autoscaler |

**Port Authority (65xxx Range)**
| Service | Port | Notes |
|---------|------|-------|
| Django API | 65020 | Load balanced |
| Portal Frontend | 65027 | CDN-backed |
| Worker LLM | - | Internal only |
| Worker STT | - | Internal only |
| Worker TTS | - | Internal only |

**Deployment**
```bash
kubectl apply -f k8s/
```

**External Configuration (Required)**
```yaml
database:
  host: ${RDS_ENDPOINT}
  port: 5432

redis:
  host: ${ELASTICACHE_ENDPOINT}
  port: 6379

keycloak:
  url: ${KEYCLOAK_CLUSTER_URL}
  realm: agentvoicebox
```

---

## 3. Lago Billing Cluster (Isolated)
Lago runs in a separate isolated network and **does not** share the 65xxx range.

**Reference**: `infra/lago-deployments/README.md`

---

## 4. Related Docs
- Docker deployment (shared services + app stack): `infra/docker/README.md`
- Local development: `../docs/LOCAL_DEVELOPMENT.md`
- Platform overview: `../README.md`
