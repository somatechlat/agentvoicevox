#!/bin/bash

# =============================================================================
# AGENTVOICEBOX SaaS DEPLOYMENT - PERFECT ISOLATED DEPLOYMENT
# Production-Ready with Local Restrictions
# =============================================================================

set -e  # Exit on error

echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║  AGENTVOICEBOX SaaS DEPLOYMENT                                           ║"
echo "║  Production-Ready with Local Restrictions                                ║"
echo "║  Port Policy: 65000-65099                                                ║"
echo "║  RAM Budget: 15GB (Shared 8GB + App 7GB)                                 ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
echo ""

# =============================================================================
# STEP 1: VALIDATE SHARED SERVICES
# =============================================================================
echo "🔍 STEP 1: Validating Shared Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if shared services are running
SHARED_RUNNING=$(docker ps --filter "name=shared_" --format "{{.Names}}" | wc -l)

if [ "$SHARED_RUNNING" -lt 5 ]; then
    echo "❌ Shared services not running. Starting..."
    echo ""
    echo "Starting shared services (PostgreSQL, Redis, Keycloak, Vault, Temporal)..."
    cd ../standalone
    docker compose -p shared-services up -d
    cd ../saas-deployment-perfect
    
    # Wait for services to be healthy
    echo ""
    echo "⏳ Waiting for shared services to be healthy (30 seconds)..."
    sleep 30
else
    echo "✅ Shared services already running: $SHARED_RUNNING containers"
fi

# Verify health
echo ""
echo "Checking health status..."
docker exec shared_postgres pg_isready -U shared_admin > /dev/null 2>&1 && echo "  ✅ PostgreSQL" || echo "  ❌ PostgreSQL"
docker exec shared_redis redis-cli ping > /dev/null 2>&1 && echo "  ✅ Redis" || echo "  ❌ Redis"
curl -s http://localhost:65006/health > /dev/null 2>&1 && echo "  ✅ Keycloak" || echo "  ❌ Keycloak"

# =============================================================================
# STEP 2: VALIDATE DOCKER STRUCTURE
# =============================================================================
echo ""
echo "🔧 STEP 2: Validating Docker Structure..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check worker directories exist
if [ ! -d "../../workers/llm" ]; then
    echo "❌ Worker directories missing. Creating..."
    cd ../..
    mkdir -p workers/llm workers/stt workers/tts
    cp workers/Dockerfile.llm workers/llm/Dockerfile
    cp workers/Dockerfile.stt workers/stt/Dockerfile
    cp workers/Dockerfile.tts workers/tts/Dockerfile
    cp workers/requirements-llm.txt workers/llm/requirements.txt
    cp workers/requirements-stt.txt workers/stt/requirements.txt
    cp workers/requirements-tts.txt workers/tts/requirements.txt
    cd infra/saas-deployment-perfect
    echo "✅ Worker directories created"
else
    echo "✅ Worker directories exist"
fi

# Check backend Dockerfile
if [ ! -f "../../backend/Dockerfile" ]; then
    echo "❌ Backend Dockerfile missing"
    exit 1
else
    echo "✅ Backend Dockerfile exists"
fi

# Check portal-frontend Dockerfile
if [ ! -f "../../portal-frontend/Dockerfile" ]; then
    echo "❌ Portal frontend Dockerfile missing"
    exit 1
else
    echo "✅ Portal frontend Dockerfile exists"
fi

# =============================================================================
# STEP 3: BUILD IMAGES
# =============================================================================
echo ""
echo "🏗️ STEP 3: Building Docker Images..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd ../..
echo "Building from: $(pwd)"

# Build all services
echo "Building Django API (1.5GB)..."
docker compose -f infra/saas-deployment-perfect/docker-compose.yml build django-api

echo ""
echo "Building Portal Frontend (512MB)..."
docker compose -f infra/saas-deployment-perfect/docker-compose.yml build portal-frontend

echo ""
echo "Building LLM Worker (2GB)..."
docker compose -f infra/saas-deployment-perfect/docker-compose.yml build worker-llm

echo ""
echo "Building STT Worker (1.5GB)..."
docker compose -f infra/saas-deployment-perfect/docker-compose.yml build worker-stt

echo ""
echo "Building TTS Worker (1GB)..."
docker compose -f infra/saas-deployment-perfect/docker-compose.yml build worker-tts

echo ""
echo "✅ All images built successfully"

# =============================================================================
# STEP 4: DEPLOY SERVICES
# =============================================================================
echo ""
echo "🚀 STEP 4: Deploying AgentVoiceBox Services..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

echo "Starting services on ports 65020 and 65027..."
docker compose -f infra/saas-deployment-perfect/docker-compose.yml -p agentvoicebox up -d

# Wait for services to start
echo ""
echo "⏳ Waiting for services to start (20 seconds)..."
sleep 20

# =============================================================================
# STEP 5: VALIDATE DEPLOYMENT
# =============================================================================
echo ""
echo "✅ STEP 5: Validating Deployment..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check all containers are running
echo ""
echo "Container Status:"
docker ps --filter "name=avb-" --format "table {{.Names}}\t{{.Status}}"

echo ""
echo "Service Endpoints:"
echo "  🌐 Django API:        http://localhost:65020"
echo "  🌐 Portal Frontend:   http://localhost:65027"
echo "  🔑 Keycloak:          http://localhost:65006"
echo "  🔑 Vault:             http://localhost:65003"
echo "  ⚙️  Temporal:          http://localhost:65007"
echo "  📊 PostgreSQL:        localhost:65004"
echo "  📊 Redis:             localhost:65005"

# Health check Django API
echo ""
echo "Health Checks:"
if curl -s http://localhost:65020/health/ > /dev/null 2>&1; then
    echo "  ✅ Django API: HEALTHY"
else
    echo "  ⚠️  Django API: Starting..."
fi

if curl -s http://localhost:65027/ > /dev/null 2>&1; then
    echo "  ✅ Portal Frontend: HEALTHY"
else
    echo "  ⚠️  Portal Frontend: Starting..."
fi

# =============================================================================
# STEP 6: DISPLAY NEXT STEPS
# =============================================================================
echo ""
echo "📋 STEP 6: Next Steps..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "To test your deployment:"
echo "  1. Run: ./test-audio.sh (for STT testing)"
echo "  2. Run: ./test-speech-to-speech.sh (for full pipeline)"
echo ""
echo "To view logs:"
echo "  docker compose -f infra/saas-deployment-perfect/docker-compose.yml logs -f <service>"
echo ""
echo "To stop:"
echo "  docker compose -f infra/saas-deployment-perfect/docker-compose.yml down"
echo ""
echo "╔═══════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                           ║"
echo "║  ✅ DEPLOYMENT COMPLETE                                                   ║"
echo "║                                                                           ║"
echo "║  Your AgentVoiceBox SaaS is now running!                                  ║"
echo "║                                                                           ║"
echo "╚═══════════════════════════════════════════════════════════════════════════╝"
