#!/bin/bash

# FortiGate Dashboard - Port Registry Utility
# Wrapper around port-manager for checking port availability and registry lookups

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PORT_MANAGER="/home/keith/.local/bin/port-manager"
PORT_REGISTRY="$HOME/.config/port_registry.md"

usage() {
    echo -e "${BLUE}FortiGate Dashboard - Port Registry Utility${NC}"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  check <port>          Check if a port is in use (system + registry)"
    echo "  find [start] [end]    Find a free port in range (default: 11000-12000)"
    echo "  lookup <port>         Look up port info in registry file"
    echo "  list                  List all registered ports for fortigate-dashboard"
    echo "  register <port> <app> <desc>  Register a port in the registry"
    echo "  show-all              Show all active listening ports"
    echo ""
    echo "Examples:"
    echo "  $0 check 8000"
    echo "  $0 find"
    echo "  $0 lookup 11100"
    echo "  $0 list"
    echo ""
}

# Check if port-manager exists
if [[ ! -f "$PORT_MANAGER" ]]; then
    echo -e "${RED}Error: port-manager not found at $PORT_MANAGER${NC}"
    exit 1
fi

# Check if registry exists
if [[ ! -f "$PORT_REGISTRY" ]]; then
    echo -e "${YELLOW}Warning: Port registry not found at $PORT_REGISTRY${NC}"
fi

case "${1:-}" in
    check)
        if [[ -z "${2:-}" ]]; then
            echo -e "${RED}Error: Port number required${NC}"
            usage
            exit 1
        fi
        echo -e "${BLUE}Checking port $2...${NC}"
        $PORT_MANAGER check "$2"
        ;;
    
    find)
        START=${2:-11000}
        END=${3:-12000}
        echo -e "${BLUE}Finding free port in range $START-$END...${NC}"
        FREE_PORT=$($PORT_MANAGER find "$START" "$END")
        if [[ -n "$FREE_PORT" ]]; then
            echo -e "${GREEN}Found free port: $FREE_PORT${NC}"
            # Check registry for this port
            if grep -q "^| $FREE_PORT |" "$PORT_REGISTRY" 2>/dev/null; then
                echo -e "${YELLOW}Warning: Port $FREE_PORT is registered in registry but appears free${NC}"
                grep "^| $FREE_PORT |" "$PORT_REGISTRY"
            fi
            echo "$FREE_PORT"
        else
            echo -e "${RED}No free port found in range $START-$END${NC}"
            exit 1
        fi
        ;;
    
    lookup)
        if [[ -z "${2:-}" ]]; then
            echo -e "${RED}Error: Port number required${NC}"
            usage
            exit 1
        fi
        echo -e "${BLUE}Looking up port $2 in registry...${NC}"
        if grep -q "^| $2 |" "$PORT_REGISTRY" 2>/dev/null; then
            echo -e "${GREEN}Port $2 found in registry:${NC}"
            grep "^| $2 |" "$PORT_REGISTRY"
        else
            echo -e "${YELLOW}Port $2 not found in registry${NC}"
            # Still check if it's in use
            $PORT_MANAGER check "$2"
        fi
        ;;
    
    list)
        echo -e "${BLUE}FortiGate Dashboard registered ports:${NC}"
        if grep -q "fortigate" "$PORT_REGISTRY" 2>/dev/null; then
            grep -i "fortigate" "$PORT_REGISTRY" | while read -r line; do
                echo "  $line"
            done
        else
            echo -e "${YELLOW}No fortigate-dashboard ports found in registry${NC}"
        fi
        ;;
    
    register)
        if [[ -z "${2:-}" || -z "${3:-}" || -z "${4:-}" ]]; then
            echo -e "${RED}Error: Port, application name, and description required${NC}"
            echo "Usage: $0 register <port> <app> <description>"
            exit 1
        fi
        echo -e "${BLUE}Registering port $2 for $3...${NC}"
        $PORT_MANAGER register "$2" "$3" "$4"
        echo -e "${GREEN}Port registered successfully${NC}"
        ;;
    
    show-all)
        echo -e "${BLUE}All active listening ports:${NC}"
        $PORT_MANAGER list
        ;;
    
    *)
        usage
        exit 1
        ;;
esac
