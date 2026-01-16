#!/bin/bash
# Vault Initialization Script for AgentVoiceBox
# Run this ONCE after first Vault startup to initialize and seed secrets

set -e

VAULT_ADDR=${VAULT_ADDR:-http://localhost:25012}
export VAULT_ADDR

echo "=== AgentVoiceBox Vault Initialization ==="
echo "Vault Address: $VAULT_ADDR"

# Wait for Vault to be ready
echo "Waiting for Vault to be ready..."
until curl -s $VAULT_ADDR/v1/sys/health > /dev/null 2>&1; do
  sleep 2
done

# Check if already initialized
INIT_STATUS=$(curl -s $VAULT_ADDR/v1/sys/init | jq -r '.initialized')

if [ "$INIT_STATUS" = "true" ]; then
  echo "Vault is already initialized."
  echo "If you need to re-initialize, delete the vault-data volume first."
  exit 0
fi

echo "Initializing Vault..."
INIT_RESPONSE=$(curl -s -X PUT $VAULT_ADDR/v1/sys/init \
  -H "Content-Type: application/json" \
  -d '{"secret_shares": 1, "secret_threshold": 1}')

UNSEAL_KEY=$(echo $INIT_RESPONSE | jq -r '.keys[0]')
ROOT_TOKEN=$(echo $INIT_RESPONSE | jq -r '.root_token')

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║  CRITICAL: SAVE THESE VALUES SECURELY - SHOWN ONLY ONCE!        ║"
echo "╠══════════════════════════════════════════════════════════════════╣"
echo "║  Unseal Key: $UNSEAL_KEY"
echo "║  Root Token: $ROOT_TOKEN"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Save to file for development (DO NOT DO THIS IN PRODUCTION)
echo "VAULT_UNSEAL_KEY=$UNSEAL_KEY" > vault/vault-keys.env
echo "VAULT_ROOT_TOKEN=$ROOT_TOKEN" >> vault/vault-keys.env
echo "WARNING: vault-keys.env created for development. DELETE in production!"

# Unseal Vault
echo "Unsealing Vault..."
curl -s -X PUT $VAULT_ADDR/v1/sys/unseal \
  -H "Content-Type: application/json" \
  -d "{\"key\": \"$UNSEAL_KEY\"}" > /dev/null

export VAULT_TOKEN=$ROOT_TOKEN

# Enable KV secrets engine v2
echo "Enabling KV secrets engine..."
curl -s -X POST $VAULT_ADDR/v1/sys/mounts/secret \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "kv", "options": {"version": "2"}}' > /dev/null 2>&1 || true

# Seed secrets
echo "Seeding secrets..."

# Database credentials
curl -s -X POST $VAULT_ADDR/v1/secret/data/agentvoicebox/database/postgres \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "username": "agentvoicebox",
      "password": "'$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)'",
      "database": "agentvoicebox",
      "host": "postgres",
      "port": "5432"
    }
  }'

# Redis (no auth by default, but prepared)
curl -s -X POST $VAULT_ADDR/v1/secret/data/agentvoicebox/database/redis \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "host": "redis",
      "port": "6379",
      "password": ""
    }
  }'

# Keycloak admin credentials
curl -s -X POST $VAULT_ADDR/v1/secret/data/agentvoicebox/keycloak/admin \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "username": "admin",
      "password": "'$(openssl rand -base64 32 | tr -d '/+=' | head -c 24)'"
    }
  }'

# Application secrets (Django)
curl -s -X POST $VAULT_ADDR/v1/secret/data/agentvoicebox/app/django \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "secret_key": "'$(openssl rand -base64 48 | tr -d '/+=' | head -c 64)'"
    }
  }'

# Lago secrets
curl -s -X POST $VAULT_ADDR/v1/secret/data/agentvoicebox/lago/app \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "secret_key_base": "'$(openssl rand -hex 64)'",
      "encryption_primary_key": "'$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)'",
      "encryption_deterministic_key": "'$(openssl rand -base64 32 | tr -d '/+=' | head -c 32)'"
    }
  }'

# LLM API keys (empty by default - user must set)
curl -s -X POST $VAULT_ADDR/v1/secret/data/agentvoicebox/api-keys/llm \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "groq_api_key": "",
      "openai_api_key": "",
      "anthropic_api_key": ""
    }
  }'

# Create policy
echo "Creating Vault policy..."
curl -s -X PUT $VAULT_ADDR/v1/sys/policies/acl/agentvoicebox \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d @- << 'EOF'
{
  "policy": "path \"secret/data/agentvoicebox/*\" { capabilities = [\"read\"] }\npath \"auth/token/renew-self\" { capabilities = [\"update\"] }\npath \"auth/token/lookup-self\" { capabilities = [\"read\"] }"
}
EOF

# Create app token
echo "Creating application token..."
APP_TOKEN_RESPONSE=$(curl -s -X POST $VAULT_ADDR/v1/auth/token/create \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "policies": ["agentvoicebox"],
    "ttl": "720h",
    "renewable": true,
    "display_name": "agentvoicebox-app"
  }')

APP_TOKEN=$(echo $APP_TOKEN_RESPONSE | jq -r '.auth.client_token')
echo "VAULT_APP_TOKEN=$APP_TOKEN" >> vault/vault-keys.env

echo ""
echo "=== Vault Initialization Complete ==="
echo ""
echo "Application Token: $APP_TOKEN"
echo ""
echo "To use Vault secrets in your application:"
echo "  export VAULT_ADDR=$VAULT_ADDR"
echo "  export VAULT_TOKEN=$APP_TOKEN"
echo ""
echo "To read a secret:"
echo "  curl -s -H \"X-Vault-Token: \$VAULT_TOKEN\" \$VAULT_ADDR/v1/secret/data/agentvoicebox/database/postgres | jq '.data.data'"
echo ""
