#!/bin/bash

# FortiGate Dashboard Deployment Script
# Supports development, production, and enterprise deployments

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="fortigate-dashboard"
DEFAULT_ENV="development"

# Functions
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

print_banner() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "    FortiGate Enterprise Dashboard Deployment"
    echo "    Version 2.0 - AI-Enhanced Network Management"
    echo "=================================================="
    echo -e "${NC}"
}

show_usage() {
    echo "Usage: $0 [ENVIRONMENT] [OPTIONS]"
    echo ""
    echo "ENVIRONMENTS:"
    echo "  dev, development  - Development environment with hot-reload"
    echo "  prod, production  - Production environment with clustering"
    echo "  enterprise        - Enterprise-scale deployment (5900+ locations)"
    echo ""
    echo "OPTIONS:"
    echo "  --build           Force rebuild of images"
    echo "  --pull            Pull latest base images"
    echo "  --setup           Run initial setup and create secrets"
    echo "  --stop            Stop all services"
    echo "  --clean           Remove all containers and volumes"
    echo "  --logs            Follow logs after deployment"
    echo "  --health          Check health of all services"
    echo "  --help            Show this help message"
    echo ""
    echo "EXAMPLES:"
    echo "  $0 dev --build           # Build and start development environment"
    echo "  $0 prod --setup          # Setup and deploy production environment"
    echo "  $0 enterprise --logs     # Deploy enterprise and follow logs"
    echo "  $0 --stop                # Stop all environments"
}

check_requirements() {
    log_info "Checking requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed or outdated"
        exit 1
    fi
    
    # Check available disk space (need at least 10GB)
    available_space=$(df . | awk 'NR==2 {print $4}')
    if [ "$available_space" -lt 10485760 ]; then  # 10GB in KB
        log_warning "Low disk space. At least 10GB recommended."
    fi
    
    # Check available memory (need at least 4GB)
    available_memory=$(free -m | awk 'NR==2 {print $7}')
    if [ "$available_memory" -lt 4096 ]; then
        log_warning "Low available memory. At least 4GB recommended."
    fi
    
    log_success "Requirements check passed"
}

setup_secrets() {
    log_info "Setting up secrets directory..."
    
    mkdir -p "$SCRIPT_DIR/secrets"
    
    # Create default secret files if they don't exist
    secrets=(
        "fortigate_api_token.txt"
        "fortiswitch_password.txt"
        "eraser_api_token.txt"
        "postgres_password.txt"
        "postgres_replication_password.txt"
        "grafana_admin_password.txt"
        "grafana_db_password.txt"
        "neo4j_password.txt"
        "meraki_api_key.txt"
    )
    
    for secret in "${secrets[@]}"; do
        if [ ! -f "$SCRIPT_DIR/secrets/$secret" ]; then
            # Generate random password or prompt for API keys
            if [[ "$secret" == *"api"* ]] || [[ "$secret" == *"key"* ]]; then
                echo "your_${secret%.*}_here" > "$SCRIPT_DIR/secrets/$secret"
                log_warning "Please update $secret with actual value"
            else
                openssl rand -base64 32 > "$SCRIPT_DIR/secrets/$secret"
                log_success "Generated random password for $secret"
            fi
        fi
    done
    
    # Set appropriate permissions
    chmod 600 "$SCRIPT_DIR/secrets"/*
    log_success "Secrets setup completed"
}

create_env_file() {
    local env_type="$1"
    local env_file="$SCRIPT_DIR/.env"
    
    if [ ! -f "$env_file" ]; then
        log_info "Creating .env file for $env_type environment..."
        
        cat > "$env_file" << EOF
# FortiGate Dashboard Environment Configuration
ENVIRONMENT=$env_type

# FortiGate Connection Settings
FORTIGATE_HOST=192.168.0.254
FORTIGATE_USERNAME=admin
FORTIGATE_PASSWORD=your_password_here
FORTIGATE_API_PORT=8443

# Network Settings
SNMP_COMMUNITY=netintegrate

# AI Integration
ERASER_ENABLED=true
ERASER_API_URL=https://app.eraser.io

# Meraki Integration
MERAKI_API_KEY=your_meraki_api_key_here

# Compose Project Name
COMPOSE_PROJECT_NAME=$PROJECT_NAME
EOF
        
        log_success "Created .env file - please update with your values"
        log_warning "Update FortiGate credentials and API keys in .env file"
    fi
}

deploy_environment() {
    local env_type="$1"
    local compose_file="docker-compose.yml"
    local additional_args=""
    
    case "$env_type" in
        "development"|"dev")
            compose_file="docker-compose.dev.yml"
            log_info "Deploying development environment..."
            ;;
        "production"|"prod")
            compose_file="docker-compose.prod.yml"
            log_info "Deploying production environment..."
            additional_args="--scale fortigate-dashboard=3"
            ;;
        "enterprise")
            compose_file="docker-compose.enterprise.yml"
            log_info "Deploying enterprise environment..."
            additional_args="--scale fortigate-dashboard-enterprise=6"
            ;;
        *)
            log_info "Deploying default environment..."
            ;;
    esac
    
    # Build and deploy
    if [ "$BUILD" = true ]; then
        log_info "Building images..."
        docker compose -f "$compose_file" build
    fi
    
    if [ "$PULL" = true ]; then
        log_info "Pulling latest images..."
        docker compose -f "$compose_file" pull
    fi
    
    log_info "Starting services..."
    docker compose -f "$compose_file" up -d $additional_args
    
    log_success "Deployment completed for $env_type environment"
    
    # Show service status
    show_service_status "$compose_file"
}

show_service_status() {
    local compose_file="$1"
    
    log_info "Service status:"
    docker compose -f "$compose_file" ps
    
    echo ""
    log_info "Available endpoints:"
    echo "  • Main Dashboard: http://localhost:8000"
    echo "  • 3D Topology: http://localhost:8000/topology-3d"
    echo "  • FortiGate Topology: http://localhost:8000/topology-fortigate"
    echo "  • Enterprise Dashboard: http://localhost:8000/enterprise"
    echo "  • API Documentation: http://localhost:8000/docs"
    
    if docker compose -f "$compose_file" ps | grep -q grafana; then
        echo "  • Grafana: http://localhost:3000"
    fi
    
    if docker compose -f "$compose_file" ps | grep -q prometheus; then
        echo "  • Prometheus: http://localhost:9090"
    fi
    
    if docker compose -f "$compose_file" ps | grep -q neo4j; then
        echo "  • Neo4j Browser: http://localhost:7474"
    fi
}

check_health() {
    log_info "Checking service health..."
    
    # Find the appropriate compose file
    local compose_files=("docker-compose.yml" "docker-compose.dev.yml" "docker-compose.prod.yml" "docker-compose.enterprise.yml")
    
    for compose_file in "${compose_files[@]}"; do
        if docker compose -f "$compose_file" ps | grep -q "Up"; then
            log_info "Checking health for $compose_file"
            
            # Check main application
            if curl -f -s "http://localhost:8000/" > /dev/null; then
                log_success "Main dashboard is healthy"
            else
                log_error "Main dashboard is not responding"
            fi
            
            # Check API
            if curl -f -s "http://localhost:8000/api/debug/topology" > /dev/null; then
                log_success "API endpoints are healthy"
            else
                log_error "API endpoints are not responding"
            fi
            
            # Check databases
            docker compose -f "$compose_file" exec -T redis redis-cli ping > /dev/null && log_success "Redis is healthy" || log_error "Redis is not healthy"
            
            break
        fi
    done
}

stop_all() {
    log_info "Stopping all services..."
    
    local compose_files=("docker-compose.yml" "docker-compose.dev.yml" "docker-compose.prod.yml" "docker-compose.enterprise.yml")
    
    for compose_file in "${compose_files[@]}"; do
        if [ -f "$compose_file" ]; then
            docker compose -f "$compose_file" down 2>/dev/null || true
        fi
    done
    
    log_success "All services stopped"
}

clean_all() {
    log_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Operation cancelled"
        exit 0
    fi
    
    log_info "Cleaning up all resources..."
    
    stop_all
    
    # Remove volumes
    docker volume prune -f
    docker network prune -f
    docker system prune -f
    
    log_success "Cleanup completed"
}

follow_logs() {
    local env_type="$1"
    local compose_file="docker-compose.yml"
    
    case "$env_type" in
        "development"|"dev")
            compose_file="docker-compose.dev.yml"
            ;;
        "production"|"prod")
            compose_file="docker-compose.prod.yml"
            ;;
        "enterprise")
            compose_file="docker-compose.enterprise.yml"
            ;;
    esac
    
    log_info "Following logs for $env_type environment..."
    docker compose -f "$compose_file" logs -f
}

# Main script
main() {
    print_banner
    
    # Default values
    ENVIRONMENT="$DEFAULT_ENV"
    BUILD=false
    PULL=false
    SETUP=false
    STOP=false
    CLEAN=false
    LOGS=false
    HEALTH=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            dev|development)
                ENVIRONMENT="development"
                shift
                ;;
            prod|production)
                ENVIRONMENT="production"
                shift
                ;;
            enterprise)
                ENVIRONMENT="enterprise"
                shift
                ;;
            --build)
                BUILD=true
                shift
                ;;
            --pull)
                PULL=true
                shift
                ;;
            --setup)
                SETUP=true
                shift
                ;;
            --stop)
                STOP=true
                shift
                ;;
            --clean)
                CLEAN=true
                shift
                ;;
            --logs)
                LOGS=true
                shift
                ;;
            --health)
                HEALTH=true
                shift
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    
    # Handle special operations
    if [ "$CLEAN" = true ]; then
        clean_all
        exit 0
    fi
    
    if [ "$STOP" = true ]; then
        stop_all
        exit 0
    fi
    
    if [ "$HEALTH" = true ]; then
        check_health
        exit 0
    fi
    
    # Check requirements
    check_requirements
    
    # Setup
    if [ "$SETUP" = true ]; then
        setup_secrets
        create_env_file "$ENVIRONMENT"
    fi
    
    # Deploy
    deploy_environment "$ENVIRONMENT"
    
    # Follow logs if requested
    if [ "$LOGS" = true ]; then
        follow_logs "$ENVIRONMENT"
    fi
}

# Run main function
main "$@"