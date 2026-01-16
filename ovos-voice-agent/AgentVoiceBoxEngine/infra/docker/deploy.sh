#!/bin/bash
# AgentVoiceBox Docker Deployment Script
# This script automates the complete deployment process
#
# Usage: ./deploy.sh [options]
# Options:
#   --shared-only    : Start only shared services
#   --app-only       : Start only application services (requires shared running)
#   --stop           : Stop all services
#   --stop-all       : Stop all services including shared
#   --logs           : Show logs after deployment
#   --status         : Show status of all services
#   --health         : Run health checks
#   --reset          : Stop and remove all volumes (WARNING: Data loss!)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")"
APP_DIR="$PROJECT_DIR"
SHARED_DIR="$PROJECT_DIR/infra/standalone"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker Desktop."
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not available. Please install Docker Compose v2."
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

check_ports() {
    log_info "Checking port availability (65000-65099)..."
    
    local ports=(65003 65004 65005 65006 65007 65011 65020 65027)
    local in_use=()
    
    for port in "${ports[@]}"; do
        if lsof -i :$port &> /dev/null; then
            in_use+=($port)
        fi
    done
    
    if [ ${#in_use[@]} -gt 0 ]; then
        log_warning "Ports in use: ${in_use[*]}"
        log_warning "These ports must be free for deployment"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        log_success "All required ports are available"
    fi
}

init_volumes() {
    log_info "Initializing volume directories..."
    
    if [ ! -f "$SCRIPT_DIR/init-volumes.sh" ]; then
        log_error "init-volumes.sh not found"
        exit 1
    fi
    
    chmod +x "$SCRIPT_DIR/init-volumes.sh"
    "$SCRIPT_DIR/init-volumes.sh"
    
    log_success "Volume directories initialized"
}

start_shared() {
    log_info "Starting shared services..."
    cd "$SHARED_DIR"
    docker compose -p shared-services up -d
    log_success "Shared services started"
}

start_app() {
    log_info "Starting AgentVoiceBox application stack..."
    cd "$APP_DIR"
    
    # Build images if needed
    log_info "Building application images..."
    docker compose -p agentvoicebox build
    
    docker compose -p agentvoicebox up -d
    
    if [ $? -eq 0 ]; then
        log_success "All services started"
    else
        log_error "Failed to start services"
        exit 1
    fi
}

stop_services() {
    local scope="${1:-app}"
    log_info "Stopping services..."

    cd "$APP_DIR"
    docker compose -p agentvoicebox down

    if [ "$scope" = "all" ]; then
        cd "$SHARED_DIR"
        docker compose -p shared-services down
    fi

    log_success "Services stopped"
}

reset_deployment() {
    log_warning "This will remove ALL data including databases and volumes!"
    log_warning "This action cannot be undone!"
    
    read -p "Are you sure you want to continue? (type 'YES' to confirm): " -r
    if [[ ! $REPLY == "YES" ]]; then
        log_info "Reset cancelled"
        exit 0
    fi
    
    log_info "Resetting deployment..."
    
    cd "$APP_DIR"
    
    # Stop everything
    docker compose -p agentvoicebox down -v
    cd "$SHARED_DIR"
    docker compose -p shared-services down -v
    
    # Remove volumes
    docker volume rm -f shared_postgres_data shared_redis_data shared_keycloak_data shared_vault_data shared_temporal_data avb_prometheus_data 2>/dev/null || true
    
    # Remove network
    docker network rm shared_services_network 2>/dev/null || true
    
    log_success "Deployment reset complete. All data has been removed."
}

show_status() {
    log_info "Service Status:"
    echo ""
    
    cd "$APP_DIR"
    
    echo "=== All Services ==="
    docker compose -p agentvoicebox ps 2>/dev/null || echo "Not running"
}

show_logs() {
    log_info "Showing logs (Ctrl+C to stop)..."
    
    cd "$APP_DIR"
    
    docker compose -p agentvoicebox logs -f
}

run_health_checks() {
    log_info "Running health checks..."
    
    local all_healthy=true
    
    # Check Django API
    echo -n "Django API (65020): "
    if curl -f http://localhost:65020/health/ &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi
    
    # Check Portal Frontend
    echo -n "Portal Frontend (65027): "
    if curl -f http://localhost:65027/ &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi
    
    # Check Keycloak
    echo -n "Keycloak (65006): "
    if curl -f http://localhost:65006/health/ready &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi
    
    # Check PostgreSQL
    echo -n "PostgreSQL (65004): "
    if docker exec shared_postgres pg_isready -U shared_admin -d shared &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi
    
    # Check Redis
    echo -n "Redis (65005): "
    if docker exec shared_redis redis-cli ping &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi

    # Check Prometheus
    echo -n "Prometheus (65011): "
    if curl -f http://localhost:65011/-/healthy &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi
    
    # Check API Docs
    echo -n "API Docs: "
    if curl -f http://localhost:65020/api/v2/docs &> /dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${RED}✗${NC}"
        all_healthy=false
    fi
    
    echo ""
    
    if [ "$all_healthy" = true ]; then
        log_success "All health checks passed!"
        echo ""
        echo "Access points:"
        echo "  - Portal: http://localhost:65027"
        echo "  - API: http://localhost:65020/api/v2"
        echo "  - API Docs: http://localhost:65020/api/v2/docs"
        echo "  - Keycloak: http://localhost:65006/admin (admin/adminpassword123)"
        echo "  - Prometheus: http://localhost:65011"
    else
        log_error "Some health checks failed. Check logs for details."
        exit 1
    fi
}

# Main deployment flow
deploy_full() {
    log_info "Starting full deployment..."
    
    check_prerequisites
    check_ports
    init_volumes
    start_shared
    start_app
    
    log_success "Full deployment complete!"
    echo ""
    echo "Waiting 30 seconds before health checks..."
    sleep 30
    
    run_health_checks
}

# Parse command line arguments
if [ $# -eq 0 ]; then
    deploy_full
    exit 0
fi

case "$1" in
    "--shared-only")
        check_prerequisites
        check_ports
        init_volumes
        start_shared
        ;;
    "--app-only")
        check_prerequisites
        start_app
        ;;
    "--stop")
        stop_services "app"
        ;;
    "--stop-all")
        stop_services "all"
        ;;
    "--logs")
        show_logs "$2"
        ;;
    "--status")
        show_status
        ;;
    "--health")
        run_health_checks
        ;;
    "--reset")
        reset_deployment
        ;;
    "--help")
        echo "Usage: $0 [option]"
        echo ""
        echo "Options:"
        echo "  (no args)        : Full deployment (all services)"
        echo "  --shared-only    : Start shared services"
        echo "  --app-only       : Start application stack"
        echo "  --stop           : Stop application stack"
        echo "  --stop-all       : Stop application + shared services"
        echo "  --logs           : Show logs"
        echo "  --status         : Show service status"
        echo "  --health         : Run health checks"
        echo "  --reset          : Reset deployment (WARNING: data loss!)"
        echo "  --help           : Show this help"
        ;;
    *)
        log_error "Unknown option: $1"
        echo "Use --help for usage information"
        exit 1
        ;;
esac
