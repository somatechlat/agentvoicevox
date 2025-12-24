# ==========================================================================
# HashiCorp Vault Policy: Backend Service
# ==========================================================================
# Policy for the Django backend service.
# Grants access to:
# - KV secrets for application configuration
# - Transit engine for encrypting sensitive tenant data
# - Database credentials for PostgreSQL
# - PKI for internal TLS certificates
# ==========================================================================

# --------------------------------------------------------------------------
# KV Secrets Engine v2 - Application Secrets
# --------------------------------------------------------------------------
# Read application configuration secrets
path "secret/data/agentvoicebox/backend/*" {
  capabilities = ["read", "list"]
}

# Read shared secrets (API keys, external service credentials)
path "secret/data/agentvoicebox/shared/*" {
  capabilities = ["read", "list"]
}

# Manage tenant-specific secrets (webhook secrets, integration tokens)
path "secret/data/agentvoicebox/tenants/*" {
  capabilities = ["create", "read", "update", "delete", "list"]
}

# --------------------------------------------------------------------------
# Transit Engine - Encryption/Decryption
# --------------------------------------------------------------------------
# Encrypt data using tenant encryption keys
path "transit/encrypt/tenant-*" {
  capabilities = ["update"]
}

# Decrypt data using tenant encryption keys
path "transit/decrypt/tenant-*" {
  capabilities = ["update"]
}

# Encrypt/decrypt using the master API key encryption key
path "transit/encrypt/api-keys" {
  capabilities = ["update"]
}

path "transit/decrypt/api-keys" {
  capabilities = ["update"]
}

# Encrypt/decrypt webhook secrets
path "transit/encrypt/webhook-secrets" {
  capabilities = ["update"]
}

path "transit/decrypt/webhook-secrets" {
  capabilities = ["update"]
}

# Read encryption key metadata (for key rotation status)
path "transit/keys/tenant-*" {
  capabilities = ["read"]
}

path "transit/keys/api-keys" {
  capabilities = ["read"]
}

path "transit/keys/webhook-secrets" {
  capabilities = ["read"]
}

# --------------------------------------------------------------------------
# Database Secrets Engine - Dynamic PostgreSQL Credentials
# --------------------------------------------------------------------------
# Generate dynamic database credentials for the backend role
path "database/creds/backend" {
  capabilities = ["read"]
}

# Renew database credential leases
path "sys/leases/renew" {
  capabilities = ["update"]
}

# --------------------------------------------------------------------------
# PKI Engine - Internal TLS Certificates
# --------------------------------------------------------------------------
# Issue certificates for internal service communication
path "pki/issue/internal-services" {
  capabilities = ["create", "update"]
}

# Read CA certificate
path "pki/ca/pem" {
  capabilities = ["read"]
}

# Read certificate chain
path "pki/ca_chain" {
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
# Read Vault health status
path "sys/health" {
  capabilities = ["read"]
}
