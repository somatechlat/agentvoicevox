#!/bin/bash
# ==========================================================================
# HashiCorp Vault Setup Script for AgentVoiceBox
# ==========================================================================
# This script configures Vault with:
# - KV secrets engine v2
# - Transit engine for encryption
# - Database secrets engine for dynamic PostgreSQL credentials
# - PKI engine for internal TLS certificates
# - AppRole authentication
# - Service policies
# ==========================================================================

set -euo pipefail

# Configuration
VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v vault &> /dev/null; then
        log_error "vault CLI not found. Please install HashiCorp Vault."
        exit 1
    fi
    
    if [ -z "$VAULT_TOKEN" ]; then
        log_error "VAULT_TOKEN environment variable not set."
        exit 1
    fi
    
    export VAULT_ADDR
    export VAULT_TOKEN
    
    # Check Vault is accessible
    if ! vault status &> /dev/null; then
        log_error "Cannot connect to Vault at $VAULT_ADDR"
        exit 1
    fi
    
    log_info "Prerequisites check passed."
}

# Enable and configure KV secrets engine v2
setup_kv_engine() {
    log_info "Setting up KV secrets engine v2..."
    
    # Enable KV v2 at secret/ if not already enabled
    if ! vault secrets list | grep -q "^secret/"; then
        vault secrets enable -path=secret kv-v2
        log_info "KV v2 engine enabled at secret/"
    else
        log_warn "KV v2 engine already enabled at secret/"
    fi
    
    # Create initial secret structure
    log_info "Creating initial secret structure..."
    
    # Backend secrets
    vault kv put secret/agentvoicebox/backend/config \
        django_secret_key="$(openssl rand -base64 50)" \
        debug="false"
    
    # Shared secrets placeholder
    vault kv put secret/agentvoicebox/shared/external-apis \
        openai_api_key="" \
        groq_api_key="" \
        anthropic_api_key=""
    
    log_info "KV secrets engine configured."
}

# Enable and configure Transit engine
setup_transit_engine() {
    log_info "Setting up Transit secrets engine..."
    
    # Enable Transit engine if not already enabled
    if ! vault secrets list | grep -q "^transit/"; then
        vault secrets enable transit
        log_info "Transit engine enabled."
    else
        log_warn "Transit engine already enabled."
    fi
    
    # Create encryption keys
    log_info "Creating encryption keys..."
    
    # API keys encryption key
    vault write -f transit/keys/api-keys \
        type="aes256-gcm96" \
        auto_rotate_period="90d"
    
    # Webhook secrets encryption key
    vault write -f transit/keys/webhook-secrets \
        type="aes256-gcm96" \
        auto_rotate_period="90d"
    
    # Session data encryption key
    vault write -f transit/keys/session-data \
        type="aes256-gcm96" \
        auto_rotate_period="30d"
    
    log_info "Transit engine configured with encryption keys."
}

# Enable and configure Database secrets engine
setup_database_engine() {
    log_info "Setting up Database secrets engine..."
    
    # Enable Database engine if not already enabled
    if ! vault secrets list | grep -q "^database/"; then
        vault secrets enable database
        log_info "Database engine enabled."
    else
        log_warn "Database engine already enabled."
    fi
    
    # Configure PostgreSQL connection
    # Note: Update these values for your environment
    log_info "Configuring PostgreSQL connection..."
    
    vault write database/config/postgresql \
        plugin_name="postgresql-database-plugin" \
        allowed_roles="backend,temporal-worker,keycloak" \
        connection_url="postgresql://{{username}}:{{password}}@postgres:5432/agentvoicebox?sslmode=disable" \
        username="vault_admin" \
        password="${DB_VAULT_PASSWORD:-changeme}" \
        password_authentication="scram-sha-256"
    
    # Create backend role (read-write)
    vault write database/roles/backend \
        db_name="postgresql" \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
            GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; \
            GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO \"{{name}}\";" \
        revocation_statements="REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"; DROP ROLE IF EXISTS \"{{name}}\";" \
        default_ttl="1h" \
        max_ttl="24h"
    
    # Create temporal-worker role (read-heavy)
    vault write database/roles/temporal-worker \
        db_name="postgresql" \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; \
            GRANT INSERT, UPDATE ON sessions, session_events, audit_logs TO \"{{name}}\";" \
        revocation_statements="REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM \"{{name}}\"; DROP ROLE IF EXISTS \"{{name}}\";" \
        default_ttl="1h" \
        max_ttl="24h"
    
    # Create keycloak role
    vault write database/roles/keycloak \
        db_name="postgresql" \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
            GRANT ALL PRIVILEGES ON DATABASE keycloak TO \"{{name}}\";" \
        revocation_statements="REVOKE ALL PRIVILEGES ON DATABASE keycloak FROM \"{{name}}\"; DROP ROLE IF EXISTS \"{{name}}\";" \
        default_ttl="1h" \
        max_ttl="24h"
    
    log_info "Database engine configured with roles."
}

# Enable and configure PKI engine
setup_pki_engine() {
    log_info "Setting up PKI secrets engine..."
    
    # Enable PKI engine if not already enabled
    if ! vault secrets list | grep -q "^pki/"; then
        vault secrets enable pki
        log_info "PKI engine enabled."
    else
        log_warn "PKI engine already enabled."
    fi
    
    # Configure PKI max lease TTL
    vault secrets tune -max-lease-ttl=87600h pki
    
    # Generate root CA
    log_info "Generating root CA..."
    vault write -format=json pki/root/generate/internal \
        common_name="AgentVoiceBox Internal CA" \
        issuer_name="root-ca" \
        ttl=87600h \
        key_type="rsa" \
        key_bits=4096 > /dev/null
    
    # Configure CA and CRL URLs
    vault write pki/config/urls \
        issuing_certificates="$VAULT_ADDR/v1/pki/ca" \
        crl_distribution_points="$VAULT_ADDR/v1/pki/crl"
    
    # Create role for internal services
    vault write pki/roles/internal-services \
        allowed_domains="agentvoicebox.local,localhost" \
        allow_subdomains=true \
        allow_localhost=true \
        max_ttl="720h" \
        key_type="rsa" \
        key_bits=2048 \
        require_cn=false \
        allow_ip_sans=true \
        server_flag=true \
        client_flag=true
    
    # Create role for Keycloak
    vault write pki/roles/keycloak \
        allowed_domains="keycloak.agentvoicebox.local,localhost" \
        allow_subdomains=true \
        allow_localhost=true \
        max_ttl="720h" \
        key_type="rsa" \
        key_bits=2048 \
        require_cn=false \
        allow_ip_sans=true \
        server_flag=true \
        client_flag=false
    
    log_info "PKI engine configured with CA and roles."
}

# Enable and configure AppRole authentication
setup_approle_auth() {
    log_info "Setting up AppRole authentication..."
    
    # Enable AppRole auth if not already enabled
    if ! vault auth list | grep -q "^approle/"; then
        vault auth enable approle
        log_info "AppRole auth enabled."
    else
        log_warn "AppRole auth already enabled."
    fi
    
    # Create AppRole for backend
    vault write auth/approle/role/backend \
        token_policies="backend" \
        token_ttl="1h" \
        token_max_ttl="4h" \
        secret_id_ttl="720h" \
        secret_id_num_uses=0
    
    # Create AppRole for temporal-worker
    vault write auth/approle/role/temporal-worker \
        token_policies="temporal-worker" \
        token_ttl="1h" \
        token_max_ttl="4h" \
        secret_id_ttl="720h" \
        secret_id_num_uses=0
    
    # Create AppRole for keycloak
    vault write auth/approle/role/keycloak \
        token_policies="keycloak" \
        token_ttl="1h" \
        token_max_ttl="4h" \
        secret_id_ttl="720h" \
        secret_id_num_uses=0
    
    log_info "AppRole authentication configured."
    
    # Output role IDs
    log_info "AppRole Role IDs:"
    echo "  Backend: $(vault read -field=role_id auth/approle/role/backend/role-id)"
    echo "  Temporal Worker: $(vault read -field=role_id auth/approle/role/temporal-worker/role-id)"
    echo "  Keycloak: $(vault read -field=role_id auth/approle/role/keycloak/role-id)"
}

# Apply policies
apply_policies() {
    log_info "Applying Vault policies..."
    
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Apply backend policy
    if [ -f "$SCRIPT_DIR/policies/backend.hcl" ]; then
        vault policy write backend "$SCRIPT_DIR/policies/backend.hcl"
        log_info "Backend policy applied."
    else
        log_error "Backend policy file not found."
    fi
    
    # Apply temporal-worker policy
    if [ -f "$SCRIPT_DIR/policies/temporal-worker.hcl" ]; then
        vault policy write temporal-worker "$SCRIPT_DIR/policies/temporal-worker.hcl"
        log_info "Temporal worker policy applied."
    else
        log_error "Temporal worker policy file not found."
    fi
    
    # Apply keycloak policy
    if [ -f "$SCRIPT_DIR/policies/keycloak.hcl" ]; then
        vault policy write keycloak "$SCRIPT_DIR/policies/keycloak.hcl"
        log_info "Keycloak policy applied."
    else
        log_error "Keycloak policy file not found."
    fi
    
    log_info "All policies applied."
}

# Generate secret IDs for services
generate_secret_ids() {
    log_info "Generating Secret IDs for services..."
    
    echo ""
    echo "=========================================="
    echo "SERVICE CREDENTIALS (SAVE THESE SECURELY)"
    echo "=========================================="
    echo ""
    
    echo "Backend Service:"
    echo "  VAULT_ROLE_ID=$(vault read -field=role_id auth/approle/role/backend/role-id)"
    echo "  VAULT_SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/backend/secret-id)"
    echo ""
    
    echo "Temporal Worker:"
    echo "  VAULT_ROLE_ID=$(vault read -field=role_id auth/approle/role/temporal-worker/role-id)"
    echo "  VAULT_SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/temporal-worker/secret-id)"
    echo ""
    
    echo "Keycloak:"
    echo "  VAULT_ROLE_ID=$(vault read -field=role_id auth/approle/role/keycloak/role-id)"
    echo "  VAULT_SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/keycloak/secret-id)"
    echo ""
}

# Main execution
main() {
    log_info "Starting Vault setup for AgentVoiceBox..."
    
    check_prerequisites
    setup_kv_engine
    setup_transit_engine
    setup_database_engine
    setup_pki_engine
    apply_policies
    setup_approle_auth
    
    echo ""
    log_info "Vault setup complete!"
    echo ""
    
    read -p "Generate Secret IDs for services? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        generate_secret_ids
    fi
}

main "$@"
