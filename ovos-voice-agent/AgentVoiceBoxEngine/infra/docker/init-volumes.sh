#!/bin/bash
# Initialize persistent volume directories for Docker Compose
# Run this before first `docker compose up`
#
# Creates data directories with proper permissions for:
# - Redis (AOF/RDB persistence)
# - PostgreSQL (data + WAL)
# - Whisper model cache
# - Kokoro TTS models
# - TTS synthesis cache
# - Keycloak data
# - Vault data
# - Temporal data
# - Prometheus data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
DATA_DIR="${PROJECT_DIR}/data"

echo "Initializing volume directories in ${DATA_DIR}..."

# Create directories for shared services
mkdir -p "${DATA_DIR}/shared/postgres"
mkdir -p "${DATA_DIR}/shared/redis"
mkdir -p "${DATA_DIR}/shared/keycloak"
mkdir -p "${DATA_DIR}/shared/vault"
mkdir -p "${DATA_DIR}/shared/temporal"
mkdir -p "${DATA_DIR}/shared/prometheus"

# Create directories for agentvoicebox services
mkdir -p "${DATA_DIR}/avb/postgres"
mkdir -p "${DATA_DIR}/avb/redis"
mkdir -p "${DATA_DIR}/avb/whisper"
mkdir -p "${DATA_DIR}/avb/kokoro"
mkdir -p "${DATA_DIR}/avb/tts-cache"

# Set permissions (Redis and PostgreSQL need specific UIDs)
# Redis runs as redis user (UID 999 in alpine)
# PostgreSQL runs as postgres user (UID 70 in alpine)
chmod 755 "${DATA_DIR}/shared/postgres"
chmod 755 "${DATA_DIR}/shared/redis"
chmod 755 "${DATA_DIR}/shared/keycloak"
chmod 755 "${DATA_DIR}/shared/vault"
chmod 755 "${DATA_DIR}/shared/temporal"
chmod 755 "${DATA_DIR}/shared/prometheus"

chmod 755 "${DATA_DIR}/avb/postgres"
chmod 755 "${DATA_DIR}/avb/redis"
chmod 755 "${DATA_DIR}/avb/whisper"
chmod 755 "${DATA_DIR}/avb/kokoro"
chmod 755 "${DATA_DIR}/avb/tts-cache"

echo "Volume directories initialized:"
ls -la "${DATA_DIR}"

echo ""
echo "✅ Volume directories created successfully!"
echo ""
echo "Next steps:"
echo "1. Start shared services: cd infra/standalone && docker compose -p shared-services up -d"
echo "2. Wait for services to be healthy (30-60 seconds)"
echo "3. Start application: docker compose -p agentvoicebox up -d"
echo ""
echo "To view logs: docker compose -p agentvoicebox logs -f"
echo "To stop: docker compose -p agentvoicebox down"
echo "To stop shared services: cd infra/standalone && docker compose -p shared-services down"
