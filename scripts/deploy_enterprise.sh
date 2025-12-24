#!/bin/bash
# Enterprise Deployment Script for FortiGate Dashboard
# Manages 5,300+ FortiGate locations across three restaurant brands

set -euo pipefail

# Configuration
COMPOSE_PROJECT_NAME="fortigate-enterprise"
ENVIRONMENT="${1:-production}"
SCALE_REPLICAS="${2:-3}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed or too old"
        exit 1
    fi
    
    # Check required files
    if [[ ! -f "downloaded_files/vlan10_interfaces.csv" ]]; then
        log_error "FortiGate inventory CSV file not found"
        exit 1
    fi
    
    if [[ ! -f "secrets/fortigate_password.txt" ]]; then
        log_error "FortiGate password file not found"
        exit 1
    fi
    
    # Check CSV file size
    local csv_lines=$(wc -l < downloaded_files/vlan10_interfaces.csv)
    if [[ $csv_lines -lt 5000 ]]; then
        log_warning "CSV file has only $csv_lines lines, expected 5000+"
    else
        log_success "FortiGate inventory loaded: $csv_lines locations"
    fi
}

prepare_environment() {
    log_info "Preparing $ENVIRONMENT environment..."
    
    # Create necessary directories
    mkdir -p logs
    mkdir -p nginx/ssl
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana/{provisioning,dashboards}
    mkdir -p sql/init
    
    # Set proper permissions
    chmod 755 scripts/*.sh 2>/dev/null || true
    
    # Generate SSL certificates if not present
    if [[ ! -f "nginx/ssl/dashboard.crt" ]]; then
        log_info "Generating self-signed SSL certificate..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/dashboard.key \
            -out nginx/ssl/dashboard.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=dashboard.enterprise.local" \
            2>/dev/null || log_warning "Failed to generate SSL certificate"
    fi
    
    # Create secrets if missing
    if [[ ! -f "secrets/postgres_password.txt" ]]; then
        log_info "Generating PostgreSQL password..."
        openssl rand -base64 32 > secrets/postgres_password.txt
    fi
    
    if [[ ! -f "secrets/grafana_password.txt" ]]; then
        log_info "Generating Grafana password..."
        openssl rand -base64 16 > secrets/grafana_password.txt
    fi
}

build_images() {
    log_info "Building Docker images..."
    
    # Build with appropriate target
    if [[ "$ENVIRONMENT" == "enterprise" ]]; then
        docker compose -f compose.yml -f docker-compose.enterprise.yml build --no-cache
    elif [[ "$ENVIRONMENT" == "production" ]]; then
        docker compose -f compose.yml -f docker-compose.prod.yml build --no-cache
    else
        docker compose -f compose.yml build
    fi
    
    log_success "Images built successfully"
}

deploy_stack() {
    log_info "Deploying $ENVIRONMENT stack..."
    
    case "$ENVIRONMENT" in
        "enterprise")
            log_info "Deploying enterprise-scale stack with $SCALE_REPLICAS replicas"
            docker compose -f compose.yml -f docker-compose.enterprise.yml up -d --scale dashboard=$SCALE_REPLICAS
            ;;
        "production")
            log_info "Deploying production stack"
            docker compose -f compose.yml -f docker-compose.prod.yml up -d
            ;;
        "development"|*)
            log_info "Deploying development stack"
            docker compose -f compose.yml up -d
            ;;
    esac
}

wait_for_services() {
    log_info "Waiting for services to be healthy..."
    
    local max_wait=300  # 5 minutes
    local wait_time=0
    
    while [[ $wait_time -lt $max_wait ]]; do
        if docker compose ps --filter "status=running" | grep -q "dashboard"; then
            if curl -sf http://localhost:10000/api/enterprise/summary > /dev/null 2>&1; then
                log_success "Services are healthy and responding"
                return 0
            fi
        fi
        
        sleep 10
        wait_time=$((wait_time + 10))
        log_info "Waiting... ($wait_time/${max_wait}s)"
    done
    
    log_error "Services failed to become healthy within $max_wait seconds"
    return 1
}

run_health_checks() {
    log_info "Running comprehensive health checks..."
    
    # Check container health
    local unhealthy_containers=$(docker compose ps --filter "status=unhealthy" --format json | jq -r '.Name // empty' 2>/dev/null || echo "")
    if [[ -n "$unhealthy_containers" ]]; then
        log_error "Unhealthy containers detected: $unhealthy_containers"
        return 1
    fi
    
    # Check API endpoints
    local endpoints=(
        "http://localhost:10000/api/enterprise/summary"
        "http://localhost:10000/api/fortigate/inventory/summary" 
        "http://localhost:10000/api/organizations"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -sf "$endpoint" > /dev/null; then
            log_success "✓ $endpoint"
        else
            log_error "✗ $endpoint"
            return 1
        fi
    done
    
    # Check FortiGate inventory loading
    local inventory_count=$(curl -s http://localhost:10000/api/fortigate/inventory/summary | jq -r '.total_locations // 0' 2>/dev/null || echo "0")
    if [[ "$inventory_count" -gt 5000 ]]; then
        log_success "✓ FortiGate inventory loaded: $inventory_count locations"
    else
        log_error "✗ FortiGate inventory issue: only $inventory_count locations loaded"
        return 1
    fi
}

show_deployment_info() {
    log_info "Deployment Information:"
    echo ""
    echo "🏢 Environment: $ENVIRONMENT"
    echo "🔧 Project: $COMPOSE_PROJECT_NAME"
    echo "📊 Dashboard: http://localhost:10000"
    echo "🏗️ Enterprise: http://localhost:10000/enterprise"
    echo ""
    
    if [[ "$ENVIRONMENT" == "enterprise" ]]; then
        echo "🔄 Load Balancer: http://localhost (nginx)"
        echo "📈 Monitoring: http://localhost:3000 (Grafana)"
        echo "🔍 Metrics: http://localhost:9090 (Prometheus)"
    fi
    
    echo ""
    echo "🚀 Quick Test Commands:"
    echo "  curl http://localhost:10000/api/enterprise/summary"
    echo "  curl http://localhost:10000/api/fortigate/inventory/summary"
    echo "  curl 'http://localhost:10000/api/fortigate/search?q=Sonic&limit=5'"
    echo ""
    
    # Show container status
    log_info "Container Status:"
    docker compose ps
}

cleanup() {
    log_info "Cleaning up previous deployment..."
    docker compose -f compose.yml -f docker-compose.prod.yml -f docker-compose.enterprise.yml down --remove-orphans 2>/dev/null || true
    docker system prune -f --filter "label=com.docker.compose.project=$COMPOSE_PROJECT_NAME" 2>/dev/null || true
}

main() {
    echo "🏗️ FortiGate Enterprise Dashboard Deployment"
    echo "=============================================="
    echo ""
    
    # Parse arguments
    case "${1:-help}" in
        "development"|"dev")
            ENVIRONMENT="development"
            ;;
        "production"|"prod")
            ENVIRONMENT="production"
            ;;
        "enterprise"|"ent")
            ENVIRONMENT="enterprise"
            ;;
        "clean")
            cleanup
            log_success "Cleanup completed"
            exit 0
            ;;
        "status")
            docker compose ps
            exit 0
            ;;
        "help"|*)
            echo "Usage: $0 {development|production|enterprise|clean|status} [replicas]"
            echo ""
            echo "Environments:"
            echo "  development - Local development with hot reload"
            echo "  production  - Production deployment with optimizations"
            echo "  enterprise  - Enterprise-scale with load balancing and monitoring"
            echo "  clean       - Clean up all containers and volumes"
            echo "  status      - Show container status"
            echo ""
            echo "Examples:"
            echo "  $0 development"
            echo "  $0 production"
            echo "  $0 enterprise 5    # Deploy with 5 dashboard replicas"
            exit 0
            ;;
    esac
    
    # Set project name
    export COMPOSE_PROJECT_NAME
    
    # Execute deployment steps
    check_prerequisites
    prepare_environment
    build_images
    deploy_stack
    
    if wait_for_services; then
        if run_health_checks; then
            log_success "🎉 Deployment completed successfully!"
            show_deployment_info
        else
            log_error "❌ Health checks failed"
            exit 1
        fi
    else
        log_error "❌ Deployment failed - services not healthy"
        exit 1
    fi
}

# Execute main function
main "$@"