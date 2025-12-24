# ==========================================================================
# HashiCorp Vault Policy: Temporal Worker
# ==========================================================================
# Policy for Temporal workflow workers.
# Grants access to:
# - KV secrets for worker configuration
# - Transit engine for encrypting workflow data
# - Database credentials for PostgreSQL (read-only role)
# - PKI for internal TLS certificates
# ==========================================================================

# --------------------------------------------------------------------------
# KV Secrets Engine v2 - Worker Configuration
# --------------------------------------------------------------------------
# Read worker configuration secrets
path "secret/data/agentvoicebox/workers/*" {
  capabilities = ["read", "list"]
}

# Read shared secrets (external API keys for STT/TTS/LLM providers)
path "secret/data/agentvoicebox/shared/*" {
  capabilities = ["read", "list"]
}

# Read tenant-specific secrets for workflow processing
path "secret/data/agentvoicebox/tenants/+/workflows" {
  capabilities = ["read"]
}

# --------------------------------------------------------------------------
# Transit Engine - Encryption/Decryption
# --------------------------------------------------------------------------
# Encrypt/decrypt workflow data using tenant keys
path "transit/encrypt/tenant-*" {
  capabilities = ["update"]
}

path "transit/decrypt/tenant-*" {
  capabilities = ["update"]
}

# Encrypt/decrypt session data
path "transit/encrypt/session-data" {
  capabilities = ["update"]
}

path "transit/decrypt/session-data" {
  capabilities = ["update"]
}

# Read encryption key metadata
path "transit/keys/tenant-*" {
  capabilities = ["read"]
}

path "transit/keys/session-data" {
  capabilities = ["read"]
}

# --------------------------------------------------------------------------
# Database Secrets Engine - Dynamic PostgreSQL Credentials
# --------------------------------------------------------------------------
# Generate dynamic database credentials for the worker role (read-heavy)
path "database/creds/temporal-worker" {
  capabilities = ["read"]
}

# Renew database credential leases
path "sys/leases/renew" {
  capabilities = ["update"]
}

# --------------------------------------------------------------------------
# PKI Engine - Internal TLS Certificates
# --------------------------------------------------------------------------
# Issue certificates for worker-to-service communication
path "pki/issue/internal-services" {
  capabilities = ["create", "update"]
}

# Read CA certificate
path "pki/ca/pem" {
  capabilities = ["read"]
}

# --------------------------------------------------------------------------
# Token Management
# --------------------------------------------------------------------------
# Renew own token
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Lookup own token
path "auth/token/lookup-self" {
  capabilities = ["read"]
}

# --------------------------------------------------------------------------
# Health Check
# --------------------------------------------------------------------------
path "sys/health" {
  capabilities = ["read"]
}
