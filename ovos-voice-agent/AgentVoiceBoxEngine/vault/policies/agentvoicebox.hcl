# AgentVoiceBox Vault Policy
# Grants access to all AgentVoiceBox secrets

# Database credentials
path "secret/data/agentvoicebox/database/*" {
  capabilities = ["read"]
}

# API keys (LLM providers)
path "secret/data/agentvoicebox/api-keys/*" {
  capabilities = ["read"]
}

# Keycloak credentials
path "secret/data/agentvoicebox/keycloak/*" {
  capabilities = ["read"]
}

# Lago billing credentials
path "secret/data/agentvoicebox/lago/*" {
  capabilities = ["read"]
}

# Application secrets
path "secret/data/agentvoicebox/app/*" {
  capabilities = ["read"]
}

# Grafana credentials
path "secret/data/agentvoicebox/grafana/*" {
  capabilities = ["read"]
}

# Allow token renewal
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Allow looking up own token
path "auth/token/lookup-self" {
  capabilities = ["read"]
}
