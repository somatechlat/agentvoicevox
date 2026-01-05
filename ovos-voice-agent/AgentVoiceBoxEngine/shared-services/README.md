# Shared Services Infrastructure

This directory contains shared infrastructure services that can be used by all applications in the workspace.

## Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 65004 | Shared database server |
| Redis | 65005 | Shared cache and session store |
| Keycloak | 65006 | Shared authentication (OAuth2/OIDC) |
| Vault | 65003 | Shared secrets management |

## RAM Budget (4GB Total)

- PostgreSQL: 1GB
- Redis: 512MB
- Keycloak: 1.5GB
- Vault: 256MB

## Quick Start

```bash
# Start shared services
docker compose -p shared-services up -d

# Check status
docker compose -p shared-services ps

# View logs
docker compose -p shared-services logs -f

# Stop services
docker compose -p shared-services down
```

## Databases Created

The PostgreSQL init script creates these databases:
- `keycloak` - Keycloak authentication data
- `agentvoicebox` - AgentVoiceBox application data
- `temporal` - Temporal workflow data
- `temporal_visibility` - Temporal visibility data

## Keycloak Configuration

- Admin Console: http://localhost:65006/admin
- Admin User: `admin`
- Admin Password: `adminpassword123`
- Realm: `agentvoicebox`

### Google OAuth

Google OAuth is pre-configured in the `agentvoicebox` realm:
- Client ID: `786567505985-553faripep2qguqvkejhr99j46cjbfdr.apps.googleusercontent.com`
- Redirect URI: `http://localhost:65006/realms/agentvoicebox/broker/google/endpoint`

## Connecting Applications

Applications should connect to shared services using the `shared_services_network` Docker network:

```yaml
networks:
  shared-network:
    name: shared_services_network
    external: true
```

Service hostnames within the network:
- `postgres` - PostgreSQL
- `redis` - Redis
- `keycloak` - Keycloak
- `vault` - Vault

## Environment Variables

```bash
# Database
SHARED_DB_PASSWORD=shared_secure_2024

# Keycloak
KEYCLOAK_ADMIN=admin
KEYCLOAK_ADMIN_PASSWORD=adminpassword123

# Vault
VAULT_DEV_TOKEN=devtoken
```
