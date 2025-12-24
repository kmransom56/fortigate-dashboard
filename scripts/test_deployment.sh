#!/bin/bash
# Test script for FortiGate Dashboard Docker deployment
# Validates all enterprise features are working correctly

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BASE_URL="http://localhost:10000"
TIMEOUT=30

# Functions
log_info() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Test functions
test_container_health() {
    log_info "Testing container health..."
    
    local unhealthy=$(docker compose ps --filter "status=unhealthy" --format json 2>/dev/null | wc -l)
    if [[ "$unhealthy" -eq 0 ]]; then
        log_success "All containers are healthy"
        return 0
    else
        log_error "Found $unhealthy unhealthy containers"
        docker compose ps
        return 1
    fi
}

test_api_endpoint() {
    local endpoint="$1"
    local expected_key="$2"
    local description="$3"
    
    log_info "Testing $description..."
    
    local response=$(curl -sf --max-time $TIMEOUT "$BASE_URL$endpoint" 2>/dev/null || echo "")
    
    if [[ -n "$response" ]]; then
        if [[ -n "$expected_key" ]]; then
            if echo "$response" | jq -e ".$expected_key" >/dev/null 2>&1; then
                log_success "$description - Key '$expected_key' found"
                return 0
            else
                log_error "$description - Key '$expected_key' missing"
                echo "Response: $response" | head -c 200
                return 1
            fi
        else
            log_success "$description - Endpoint responding"
            return 0
        fi
    else
        log_error "$description - Endpoint not responding"
        return 1
    fi
}

test_enterprise_features() {
    log_info "Testing enterprise features..."
    
    # Test enterprise summary
    test_api_endpoint "/api/enterprise/summary" "total_organizations" "Enterprise Summary" || return 1
    
    # Test FortiGate inventory
    test_api_endpoint "/api/fortigate/inventory/summary" "total_locations" "FortiGate Inventory" || return 1
    
    # Test organizations API
    test_api_endpoint "/api/organizations" "organizations" "Organizations API" || return 1
    
    # Test FortiGate search
    test_api_endpoint "/api/fortigate/search?q=Sonic&limit=5" "results" "FortiGate Search" || return 1
    
    return 0
}

test_fortigate_inventory_scale() {
    log_info "Testing FortiGate inventory scale..."
    
    local response=$(curl -sf --max-time $TIMEOUT "$BASE_URL/api/fortigate/inventory/summary" 2>/dev/null || echo "")
    
    if [[ -n "$response" ]]; then
        local total_locations=$(echo "$response" | jq -r '.total_locations // 0' 2>/dev/null || echo "0")
        local sonic_count=$(echo "$response" | jq -r '.brands.Sonic.count // 0' 2>/dev/null || echo "0")
        local bww_count=$(echo "$response" | jq -r '.brands.BWW.count // 0' 2>/dev/null || echo "0")
        local arbys_count=$(echo "$response" | jq -r '.brands.Arbys.count // 0' 2>/dev/null || echo "0")
        
        if [[ "$total_locations" -gt 5000 ]]; then
            log_success "FortiGate inventory loaded: $total_locations locations"
            log_info "  - Sonic: $sonic_count locations"
            log_info "  - BWW: $bww_count locations"
            log_info "  - Arby's: $arbys_count locations"
            return 0
        else
            log_error "FortiGate inventory incomplete: only $total_locations locations"
            return 1
        fi
    else
        log_error "Could not retrieve inventory summary"
        return 1
    fi
}

test_redis_connectivity() {
    log_info "Testing Redis connectivity..."
    
    if docker compose exec -T redis redis-cli ping >/dev/null 2>&1; then
        log_success "Redis is responding to ping"
        
        # Test Redis memory usage
        local memory_usage=$(docker compose exec -T redis redis-cli info memory | grep used_memory_human | cut -d: -f2 | tr -d '\r')
        log_info "Redis memory usage: $memory_usage"
        return 0
    else
        log_error "Redis is not responding"
        return 1
    fi
}

test_database_connectivity() {
    log_info "Testing database connectivity..."
    
    # Check if PostgreSQL is running (enterprise mode)
    if docker compose ps --services | grep -q postgres; then
        if docker compose exec -T postgres pg_isready -U dashboard >/dev/null 2>&1; then
            log_success "PostgreSQL is ready"
            return 0
        else
            log_error "PostgreSQL is not ready"
            return 1
        fi
    else
        log_info "PostgreSQL not configured (development/production mode)"
        return 0
    fi
}

test_performance() {
    log_info "Testing API performance..."
    
    local endpoints=(
        "/api/enterprise/summary"
        "/api/fortigate/inventory/summary"
        "/api/organizations"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local start_time=$(date +%s.%N)
        local response=$(curl -sf --max-time $TIMEOUT "$BASE_URL$endpoint" 2>/dev/null || echo "")
        local end_time=$(date +%s.%N)
        
        if [[ -n "$response" ]]; then
            local duration=$(echo "$end_time - $start_time" | bc -l 2>/dev/null || echo "unknown")
            if (( $(echo "$duration < 5.0" | bc -l 2>/dev/null || echo "0") )); then
                log_success "$endpoint - Response time: ${duration}s"
            else
                log_warning "$endpoint - Slow response time: ${duration}s"
            fi
        else
            log_error "$endpoint - No response"
        fi
    done
}

test_resource_usage() {
    log_info "Checking resource usage..."
    
    # Check container resource usage
    local stats=$(docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || echo "")
    
    if [[ -n "$stats" ]]; then
        echo "$stats" | head -10
        log_success "Container resource statistics retrieved"
    else
        log_warning "Could not retrieve container resource statistics"
    fi
}

run_comprehensive_test() {
    echo "🧪 FortiGate Dashboard Deployment Test"
    echo "======================================"
    echo ""
    
    local tests_passed=0
    local tests_failed=0
    
    # Run all tests
    if test_container_health; then ((tests_passed++)); else ((tests_failed++)); fi
    if test_redis_connectivity; then ((tests_passed++)); else ((tests_failed++)); fi  
    if test_database_connectivity; then ((tests_passed++)); else ((tests_failed++)); fi
    if test_enterprise_features; then ((tests_passed++)); else ((tests_failed++)); fi
    if test_fortigate_inventory_scale; then ((tests_passed++)); else ((tests_failed++)); fi
    
    # Performance and resource tests (non-critical)
    test_performance
    test_resource_usage
    
    echo ""
    echo "📊 Test Results:"
    echo "================"
    echo "✅ Tests Passed: $tests_passed"
    echo "❌ Tests Failed: $tests_failed"
    echo ""
    
    if [[ $tests_failed -eq 0 ]]; then
        log_success "🎉 All tests passed! Deployment is healthy and ready for enterprise use."
        echo ""
        echo "🚀 Quick Access Links:"
        echo "  Dashboard: http://localhost:10000"
        echo "  Enterprise View: http://localhost:10000/enterprise" 
        echo "  API Documentation: http://localhost:10000/docs"
        echo ""
        return 0
    else
        log_error "❌ Some tests failed. Please check the deployment."
        echo ""
        echo "🔧 Troubleshooting:"
        echo "  1. Check container logs: docker compose logs"
        echo "  2. Verify secrets are present: ls -la secrets/"
        echo "  3. Check CSV file: ls -la downloaded_files/vlan10_interfaces.csv"
        echo ""
        return 1
    fi
}

# Main execution
if [[ $# -eq 0 ]]; then
    run_comprehensive_test
else
    case "$1" in
        "health")
            test_container_health
            ;;
        "api")
            test_enterprise_features
            ;;
        "inventory") 
            test_fortigate_inventory_scale
            ;;
        "redis")
            test_redis_connectivity
            ;;
        "performance")
            test_performance
            ;;
        "resources")
            test_resource_usage
            ;;
        *)
            echo "Usage: $0 [health|api|inventory|redis|performance|resources]"
            echo ""
            echo "Test categories:"
            echo "  health      - Container health checks"
            echo "  api         - Enterprise API functionality"  
            echo "  inventory   - FortiGate inventory loading"
            echo "  redis       - Redis connectivity and performance"
            echo "  performance - API response times"
            echo "  resources   - Container resource usage"
            echo ""
            echo "Run without arguments for comprehensive test"
            exit 1
            ;;
    esac
fi