# ==========================================================================
# HashiCorp Vault Policy: Keycloak
# ==========================================================================
# Policy for Keycloak identity provider.
# Grants access to:
# - KV secrets for Keycloak configuration
# - Database credentials for Keycloak's PostgreSQL database
# - PKI for TLS certificates
# ==========================================================================

# --------------------------------------------------------------------------
# KV Secrets Engine v2 - Keycloak Configuration
# --------------------------------------------------------------------------
# Read Keycloak configuration secrets
path "secret/data/agentvoicebox/keycloak/*" {
  capabilities = ["read", "list"]
}

# Read SMTP credentials for email sending
path "secret/data/agentvoicebox/shared/smtp" {
  capabilities = ["read"]
}

# Read OAuth provider secrets (Google, GitHub, etc.)
path "secret/data/agentvoicebox/shared/oauth/*" {
  capabilities = ["read"]
}

# --------------------------------------------------------------------------
# Database Secrets Engine - Dynamic PostgreSQL Credentials
# --------------------------------------------------------------------------
# Generate dynamic database credentials for Keycloak
path "database/creds/keycloak" {
  capabilities = ["read"]
}

# Renew database credential leases
path "sys/leases/renew" {
  capabilities = ["update"]
}

# --------------------------------------------------------------------------
# PKI Engine - TLS Certificates
# --------------------------------------------------------------------------
# Issue certificates for Keycloak HTTPS
path "pki/issue/keycloak" {
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
path "sys/health" {
  capabilities = ["read"]
}
