#!/bin/bash

# AI Research Platform - Add Application Script
# Creates a standardized process for adding new applications to the platform
# Example:
#./add-application.sh --name "Prompt Forge" --port auto --description "Prompt IDE" --docker-image ghcr.io/insaanimanav/prompt-forge:main
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NGINX_CONFIG="/etc/nginx/sites-available/ai-hub.conf"
# Primary compose file (full container stack)
DOCKER_COMPOSE="/home/keith/chat-copilot/configs/docker-compose/docker-compose-full-stack.yml"
APPLICATIONS_HTML="/home/keith/chat-copilot/webapp/public/applications.html"
WEBAPI_HTML="/home/keith/chat-copilot/webapi/wwwroot/applications.html"
# Control-Panel HTML (authoritative copy)
CONTROL_PANEL_HTML="/home/keith/chat-copilot/webapi/wwwroot/control-panel.html"

# Print usage
usage() {
    echo -e "${BLUE}AI Research Platform - Add Application Script${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --name            Application name (required)"
    echo "  --port            Application port (optional – 'auto' or omitted = find free port)"
    echo "  --path            URL path prefix (optional – auto-generated from app name if omitted)"
    echo "  --description     Application description (required)"
    echo "  --docker-image    Docker image (optional)"
    echo "  --docker-env      Docker environment variables (optional)"
    echo "  --category        Application category: ai, dev, network, api (default: ai)"
    echo "  --status          Application status: active, ready, configured (default: ready)"
    echo "  --nginx-only      Only add nginx configuration (skip Docker and HTML updates)"
    echo "  --ca-cert         Request certificate from internal CA server"
    echo "  --direct-port     Create direct port access with SSL (requires --ca-cert)"
    echo "  --test-mode       Test mode - show what would be done without making changes"
    echo "  --help            Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --name \"Windmill\" --port 11005 --path \"/windmill\" --description \"Workflow Automation Engine\""
    echo "  $0 --name \"Grafana\" --port 11006 --path \"/grafana\" --description \"Monitoring Dashboard\" --category \"dev\""
    echo "  $0 --name \"MyApp\" --port 11007 --path \"/myapp\" --description \"My Application\" --ca-cert --direct-port"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --name)
            APP_NAME="$2"
            shift 2
            ;;
        --port)
            APP_PORT="$2"
            shift 2
            ;;
        --path)
            APP_PATH="$2"
            shift 2
            ;;
        --description)
            APP_DESCRIPTION="$2"
            shift 2
            ;;
        --docker-image)
            DOCKER_IMAGE="$2"
            shift 2
            ;;
        --docker-env)
            DOCKER_ENV="$2"
            shift 2
            ;;
        --category)
            APP_CATEGORY="$2"
            shift 2
            ;;
        --status)
            APP_STATUS="$2"
            shift 2
            ;;
        --nginx-only)
            NGINX_ONLY=true
            shift
            ;;
        --ca-cert)
            USE_CA_CERT=true
            shift
            ;;
        --direct-port)
            DIRECT_PORT=true
            shift
            ;;
        --test-mode)
            TEST_MODE=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
done

# Find a free port if none supplied or set to 'auto'
# Uses multiple methods to be diligent in finding truly available ports
find_free_port() {
    local start=${1:-11000}
    local end=${2:-12000}
    
    echo -e "${BLUE}Searching for free port in range ${start}-${end}...${NC}" >&2
    
    for ((p=start; p<=end; p++)); do
        local port_available=true
        
        # Method 1: Check with ss (socket statistics)
        if ss -ltn "sport = :$p" 2>/dev/null | grep -q LISTEN; then
            port_available=false
            continue
        fi
        
        # Method 2: Check with lsof (list open files)
        if lsof -iTCP:"$p" -sTCP:LISTEN -Pn 2>/dev/null | grep -q "$p"; then
            port_available=false
            continue
        fi
        
        # Method 3: Check with netstat (if available)
        if command -v netstat >/dev/null 2>&1; then
            if netstat -tuln 2>/dev/null | grep -q ":$p "; then
                port_available=false
                continue
            fi
        fi
        
        # Method 4: Check Docker containers
        if command -v docker >/dev/null 2>&1; then
            if docker ps --format '{{.Ports}}' 2>/dev/null | grep -q ":$p->" || \
               docker ps --format '{{.Ports}}' 2>/dev/null | grep -q "0.0.0.0:$p"; then
                port_available=false
                continue
            fi
        fi
        
        # Method 5: Check nginx configuration for port references
        if [[ -f "$NGINX_CONFIG" ]]; then
            if sudo grep -q ":$p" "$NGINX_CONFIG" 2>/dev/null; then
                port_available=false
                continue
            fi
        fi
        
        # Method 6: Try to bind to the port (most reliable test)
        if command -v timeout >/dev/null 2>&1; then
            if timeout 0.1 bash -c "echo >/dev/tcp/127.0.0.1/$p" 2>/dev/null; then
                port_available=false
                continue
            fi
        fi
        
        # Method 7: Check docker-compose files for port mappings
        if [[ -f "$DOCKER_COMPOSE" ]]; then
            if grep -q "\"$p:" "$DOCKER_COMPOSE" 2>/dev/null || \
               grep -q "'$p:" "$DOCKER_COMPOSE" 2>/dev/null; then
                port_available=false
                continue
            fi
        fi
        
        # If all checks passed, port is available
        if [[ "$port_available" == "true" ]]; then
            echo -e "${GREEN}Found available port: $p${NC}" >&2
            echo "$p"
            return 0
        fi
    done
    
    echo -e "${RED}No free ports found in range ${start}-${end}${NC}" >&2
    return 1
}

# Auto-assign port if needed
if [[ -z "$APP_PORT" || "$APP_PORT" == "auto" ]]; then
    echo -e "${YELLOW}Port not specified – searching for free port in 11000-12000…${NC}"
    APP_PORT=$(find_free_port 11000 12000) || {
        echo -e "${RED}Error: No free port available in 11000-12000${NC}"; exit 1; }
    echo -e "${GREEN}Assigned free port $APP_PORT${NC}"
fi

# ----------------------------
# Auto-generate path if needed
# ----------------------------
sanitize_name() { echo "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g'; }

generate_unique_path() {
    local base="/$(sanitize_name "$APP_NAME")"
    local candidate="$base"
    local n=2
    while sudo grep -q "location ${candidate}/" "$NGINX_CONFIG" 2>/dev/null; do
        candidate="${base}-${n}"
        ((n++))
    done
    echo "$candidate"
}

# Auto path when not provided or set to 'auto'
if [[ -z "$APP_PATH" || "$APP_PATH" == "auto" ]]; then
    APP_PATH=$(generate_unique_path)
    echo -e "${GREEN}Assigned URL path: $APP_PATH${NC}"
fi

# Validate required parameters after auto-generation
if [[ -z "$APP_NAME" || -z "$APP_DESCRIPTION" ]]; then
    echo -e "${RED}Error: Missing required parameters${NC}"
    usage
    exit 1
fi

# Set defaults
APP_CATEGORY=${APP_CATEGORY:-"ai"}
APP_STATUS=${APP_STATUS:-"ready"}
NGINX_ONLY=${NGINX_ONLY:-false}
USE_CA_CERT=${USE_CA_CERT:-false}
DIRECT_PORT=${DIRECT_PORT:-false}
TEST_MODE=${TEST_MODE:-false}

# Validate category
case $APP_CATEGORY in
    ai|dev|network|api)
        ;;
    *)
        echo -e "${RED}Error: Invalid category. Must be one of: ai, dev, network, api${NC}"
        exit 1
        ;;
esac

# Validate status
case $APP_STATUS in
    active|ready|configured)
        ;;
    *)
        echo -e "${RED}Error: Invalid status. Must be one of: active, ready, configured${NC}"
        exit 1
        ;;
esac

# Validate path format (after auto-gen)
if [[ ! "$APP_PATH" =~ ^/[a-z0-9-]+$ ]]; then
    echo -e "${RED}Error: Generated/Provided path '$APP_PATH' is invalid${NC}"
    exit 1
fi

# Validate port range
if [[ $APP_PORT -lt 11000 || $APP_PORT -gt 12000 ]]; then
    echo -e "${YELLOW}Warning: Port $APP_PORT is outside the standard range 11000-12000${NC}"
fi

# Validate direct-port requires ca-cert
if [[ "$DIRECT_PORT" == "true" && "$USE_CA_CERT" != "true" ]]; then
    echo -e "${RED}Error: --direct-port requires --ca-cert${NC}"
    exit 1
fi

# Status icon mapping
case $APP_STATUS in
    active)
        STATUS_ICON="✅ Active"
        STATUS_CLASS="active"
        ;;
    ready)
        STATUS_ICON="🟡 Ready"
        STATUS_CLASS="ready"
        ;;
    configured)
        STATUS_ICON="🟡 Configured"
        STATUS_CLASS="configured"
        ;;
esac

# Category class mapping
case $APP_CATEGORY in
    ai)
        CATEGORY_CLASS="ai-category"
        ;;
    dev)
        CATEGORY_CLASS="dev-category"
        ;;
    network)
        CATEGORY_CLASS="network-category"
        ;;
    api)
        CATEGORY_CLASS="api-category"
        ;;
esac

echo -e "${BLUE}AI Research Platform - Adding Application${NC}"
echo -e "Name: ${GREEN}$APP_NAME${NC}"
echo -e "Port: ${GREEN}$APP_PORT${NC} (auto-assigned if not specified)"
echo -e "Path: ${GREEN}$APP_PATH${NC}"
echo -e "Description: ${GREEN}$APP_DESCRIPTION${NC}"
echo -e "Category: ${GREEN}$APP_CATEGORY${NC}"
echo -e "Status: ${GREEN}$APP_STATUS${NC}"
echo -e "CA Certificate: ${GREEN}$USE_CA_CERT${NC}"
echo -e "Direct Port: ${GREEN}$DIRECT_PORT${NC}"
echo ""

if [[ "$TEST_MODE" == "true" ]]; then
    echo -e "${YELLOW}TEST MODE - No changes will be made${NC}"
    echo ""
fi

# Function to add nginx configuration
add_nginx_config() {
    echo -e "${BLUE}Adding nginx configuration...${NC}"
    
    # Create the nginx location line
    NGINX_LINE="    location ${APP_PATH}/        { proxy_pass http://127.0.0.1:${APP_PORT}/;  include /etc/nginx/sites-available/04-proxy-settings.conf; }"
    
    if [[ "$TEST_MODE" == "true" ]]; then
        echo "Would add to nginx config: $NGINX_LINE"
        return
    fi
    
    # Check if the location already exists
    if sudo grep -q "location ${APP_PATH}/" "$NGINX_CONFIG"; then
        echo -e "${YELLOW}Warning: nginx location ${APP_PATH}/ already exists${NC}"
        return
    fi
    
    # Add the configuration after the searxng line
    sudo sed -i "/location \/searxng\//a\\    location ${APP_PATH}/        { proxy_pass http://127.0.0.1:${APP_PORT}/;  include /etc/nginx/sites-available/04-proxy-settings.conf; }" "$NGINX_CONFIG"
    
    # Test nginx configuration
    if sudo nginx -t; then
        echo -e "${GREEN}nginx configuration added successfully${NC}"
        sudo systemctl reload nginx
        echo -e "${GREEN}nginx reloaded${NC}"
    else
        echo -e "${RED}Error: nginx configuration test failed${NC}"
        exit 1
    fi
}

# Function to request CA certificate
request_ca_certificate() {
    echo -e "${BLUE}Requesting CA certificate...${NC}"
    
    if [[ "$USE_CA_CERT" != "true" ]]; then
        echo -e "${YELLOW}CA certificate not requested, skipping${NC}"
        return
    fi
    
    if [[ "$TEST_MODE" == "true" ]]; then
        echo "Would request CA certificate for $APP_NAME.local"
        return
    fi
    
    # Generate domain name for the application
    local app_domain
    app_domain=$(echo "${APP_NAME,,}" | sed 's/[^a-z0-9]/-/g').local
    
    # Path to CA certificate script
    local ca_script="/home/keith/chat-copilot/scripts/infrastructure/request-ca-certificate.sh"
    
    if [[ ! -f "$ca_script" ]]; then
        echo -e "${RED}Error: CA certificate script not found at $ca_script${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Requesting certificate for domain: $app_domain${NC}"
    
    # Request certificate with appropriate parameters
    if [[ "$DIRECT_PORT" == "true" ]]; then
        # Direct port access - use the application port
        "$ca_script" --domain "$app_domain" --port "$APP_PORT" --service "${APP_NAME,,}"
    else
        # Subpath access - don't specify port
        "$ca_script" --domain "$app_domain" --service "${APP_NAME,,}"
    fi
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}CA certificate requested successfully${NC}"
        
        # Update nginx configuration to use CA certificates if direct port
        if [[ "$DIRECT_PORT" == "true" ]]; then
            echo -e "${BLUE}CA certificate will be configured for direct port access${NC}"
        fi
    else
        echo -e "${RED}Failed to request CA certificate${NC}"
        return 1
    fi
}

# Function to add Docker Compose service
add_docker_service() {
    echo -e "${BLUE}Adding Docker Compose service...${NC}"
    
    if [[ -z "$DOCKER_IMAGE" ]]; then
        echo -e "${YELLOW}No Docker image specified, skipping Docker Compose configuration${NC}"
        return
    fi
    
    # Generate service name (lowercase, replace spaces with hyphens)
    SERVICE_NAME=$(echo "$APP_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g')
    
    # Create Docker service configuration
    DOCKER_SERVICE="
  ${SERVICE_NAME}:
    image: ${DOCKER_IMAGE}
    container_name: ${SERVICE_NAME}
    restart: unless-stopped
    ports:
      - \"${APP_PORT}:8000\"
    networks:
      - ai-platform"
    
    if [[ -n "$DOCKER_ENV" ]]; then
        DOCKER_SERVICE="${DOCKER_SERVICE}
    environment:
      ${DOCKER_ENV}"
    fi
    
    if [[ "$TEST_MODE" == "true" ]]; then
        echo "Would add Docker service:"
        echo "$DOCKER_SERVICE"
        return
    fi
    
    # Check if service already exists
    if grep -q "^  ${SERVICE_NAME}:" "$DOCKER_COMPOSE"; then
        echo -e "${YELLOW}Warning: Docker service ${SERVICE_NAME} already exists${NC}"
        return
    fi
    
    # Safely insert the block before the first "volumes:" line using awk (avoids sed escape issues)
    tmp_file=$(mktemp)
    awk -v s="$DOCKER_SERVICE" 'BEGIN{printed=0} {
        if (!printed && /^volumes:/) {print s; printed=1}
        print $0
    }' "$DOCKER_COMPOSE" > "$tmp_file" && mv "$tmp_file" "$DOCKER_COMPOSE"

    echo -e "${GREEN}Docker Compose service added${NC}"
}

# Function to add to applications.html
add_to_applications() {
    echo -e "${BLUE}Adding to applications.html...${NC}"
    
    # Create the HTML card
    APP_CARD="
                <div class=\"app-card ${CATEGORY_CLASS}\">
                    <h3>${APP_NAME} <span class=\"status ${STATUS_CLASS}\">${STATUS_ICON}</span></h3>
                    <p>${APP_DESCRIPTION}</p>
                    <a href=\"${APP_PATH}\" class=\"app-link\" target=\"_blank\">Launch ${APP_NAME}</a>
                </div>"
    
    # Create the quick link
    QUICK_LINK="                <a href=\"${APP_PATH}\" class=\"quick-link\" target=\"_blank\">⚡ ${APP_NAME}</a>"
    
    # Add port mapping to JavaScript
    PORT_MAPPING="                '${APP_PORT}': '${APP_PATH}/'"

    # Helper to escape string for sed (slashes, ampersands, newlines)
    escape_sed() {
        printf '%s' "$1" | sed -e 's/[/&]/\\&/g' -e ':a' -e 'N' -e '$!ba' -e 's/\n/\\n/g'
    }

    ESC_CARD=$(escape_sed "$APP_CARD")
    ESC_QUICK=$(escape_sed "$QUICK_LINK")
    ESC_PORT=$(escape_sed "$PORT_MAPPING")
    
    if [[ "$TEST_MODE" == "true" ]]; then
        echo "Would add application card:"
        echo "$APP_CARD"
        echo ""
        echo "Would add quick link:"
        echo "$QUICK_LINK"
        echo ""
        echo "Would add port mapping:"
        echo "$PORT_MAPPING"
        return
    fi
    
    # Function to update an HTML file
    update_html_file() {
        local file=$1
        
        # Check if app already exists
        if grep -q "Launch ${APP_NAME}" "$file"; then
            echo -e "${YELLOW}Warning: ${APP_NAME} already exists in $(basename $file)${NC}"
            return
        fi
        
        # Add the app card before the closing div of the appropriate section
        case $APP_CATEGORY in
            ai)
                sed -i "/Launch GenAI Stack<\/a>/a\\${ESC_CARD}" "$file"
                ;;
            dev)
                sed -i "/Launch Backup<\/a>/a\\${ESC_CARD}" "$file"
                ;;
            network)
                sed -i "/Launch Backup<\/a>/a\\${ESC_CARD}" "$file"
                ;;
            api)
                sed -i "/API Docs<\/a>/a\\${ESC_CARD}" "$file"
                ;;
        esac
        
        # Add quick link (insert after first existing quick-link)
        sed -i "0,/class=\\\"quick-link\\\"/s//&\n${ESC_QUICK}/" "$file"
        
        # Add port mapping to JavaScript PORT_TO_PATH if present
        if grep -q "const PORT_TO_PATH" "$file"; then
            if ! grep -q "'${APP_PORT}'" "$file"; then
                sed -i "/const PORT_TO_PATH = {/{n; a\\${ESC_PORT}}" "$file"
            fi
        fi
    }
    
    # Update both HTML files
    update_html_file "$APPLICATIONS_HTML"
    update_html_file "$WEBAPI_HTML"
    
    echo -e "${GREEN}Applications HTML updated${NC}"
}

# Function to add to control-panel.html
add_to_control_panel() {
    echo -e "${BLUE}Adding to control-panel.html...${NC}"

    local file="$CONTROL_PANEL_HTML"

    if [[ ! -f "$file" ]]; then
        echo -e "${YELLOW}control-panel.html not found – skipping${NC}"
        return
    fi

    # Avoid duplicate entry
    if grep -q "Launch ${APP_NAME}" "$file" || grep -q ">${APP_NAME}<" "$file"; then
        echo -e "${YELLOW}${APP_NAME} already exists in control-panel.html${NC}"
        return
    fi

    # Build anchor element (copy style of existing buttons)
    local CP_BUTTON="                    <a href=\"http://localhost:${APP_PORT}\" target=\"_blank\" class=\"control-button\">\n                        <span class=\"material-icons\">apps</span>\n                        ${APP_NAME}\n                    </a>"

    if [[ "$TEST_MODE" == "true" ]]; then
        echo "Would insert into control-panel.html:"; echo "$CP_BUTTON"; return
    fi

    # Insert before the closing tag of the AI Services button grid (after Windmill link)
    # Fallback: append at the end of first button-grid in AI Services section
    if grep -n "Windmill" "$file" >/dev/null; then
        sed -i "/Windmill/a\\${CP_BUTTON}" "$file"
    else
        sed -i "0,/AI Services/{/button-grid/{n; a\\${CP_BUTTON}}}" "$file"
    fi

    # Add port mapping to PORT_TO_PATH table if present
    if grep -q "const PORT_TO_PATH" "$file"; then
        if ! grep -q "'${APP_PORT}'" "$file"; then
            sed -i "/const PORT_TO_PATH = {/{n; a\\                '${APP_PORT}': '${APP_PATH}/',}" "$file"
        fi
    fi

    echo -e "${GREEN}control-panel.html updated${NC}"
}

# Function to update port documentation
update_port_docs() {
    echo -e "${BLUE}Updating port documentation...${NC}"
    
    PORT_DOC="/home/keith/chat-copilot/docs/troubleshooting/PORT_CONFIGURATION_SUMMARY.md"
    
    if [[ "$TEST_MODE" == "true" ]]; then
        echo "Would add port $APP_PORT for $APP_NAME to documentation"
        return
    fi
    
    # Add to the appropriate section based on port range
    if [[ $APP_PORT -ge 11000 && $APP_PORT -le 11099 ]]; then
        SECTION="### **Core AI Services (11000-11099)**"
    elif [[ $APP_PORT -ge 11100 && $APP_PORT -le 11199 ]]; then
        SECTION="### **Network Tools (11100-11199)**"
    elif [[ $APP_PORT -ge 11400 && $APP_PORT -le 11499 ]]; then
        SECTION="### **Infrastructure (11400-11499)**"
    else
        SECTION="### **Additional Services**"
    fi
    
    if grep -q "**$APP_NAME:**" "$PORT_DOC"; then
        echo -e "${YELLOW}Warning: $APP_NAME already documented${NC}"
        return
    fi
    
    # Add the port documentation
    sed -i "/$SECTION/a- **$APP_NAME:** \`$APP_PORT\` - $APP_DESCRIPTION" "$PORT_DOC"
    
    echo -e "${GREEN}Port documentation updated${NC}"
}

# Main execution
echo -e "${BLUE}Starting application addition process...${NC}"
echo ""

# Request CA certificate first if needed
if [[ "$USE_CA_CERT" == "true" ]]; then
    request_ca_certificate
fi

# Always add nginx configuration
add_nginx_config

# Skip Docker and HTML if nginx-only mode
if [[ "$NGINX_ONLY" != "true" ]]; then
    add_docker_service
    add_to_applications
    add_to_control_panel
    update_port_docs
fi

echo ""
echo -e "${GREEN}✅ Application addition completed successfully!${NC}"
echo ""

if [[ "$TEST_MODE" != "true" ]]; then
    echo -e "${BLUE}Next steps:${NC}"
    
    if [[ "$DIRECT_PORT" == "true" && "$USE_CA_CERT" == "true" ]]; then
        local app_domain
        app_domain=$(echo "${APP_NAME,,}" | sed 's/[^a-z0-9]/-/g').local
        echo -e "1. Test the application (Direct SSL): ${GREEN}https://$app_domain:$APP_PORT${NC}"
        echo -e "2. Test the application (Subpath): ${GREEN}https://ubuntuaicodeserver-1.tail5137b4.ts.net:10443${APP_PATH}${NC}"
    else
        echo -e "1. Test the application: ${GREEN}https://ubuntuaicodeserver-1.tail5137b4.ts.net:10443${APP_PATH}${NC}"
    fi
    
    if [[ "$NGINX_ONLY" != "true" && -n "$DOCKER_IMAGE" ]]; then
        echo -e "2. Start the Docker service: ${GREEN}docker-compose up -d${NC}"
        echo -e "3. Check service status: ${GREEN}docker ps --filter name=${SERVICE_NAME}${NC}"
    fi
    
    echo -e "4. Update status in applications.html if needed"
    echo -e "5. Add any additional configuration as required"
    
    if [[ "$USE_CA_CERT" == "true" ]]; then
        echo -e "6. CA certificate installed and configured"
    fi
fi

echo ""
echo -e "${BLUE}Application ${APP_NAME} has been added to the AI Research Platform!${NC}"