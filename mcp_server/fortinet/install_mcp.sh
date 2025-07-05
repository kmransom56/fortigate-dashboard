#!/bin/bash
"""
Fortinet MCP Server Installation Script
Provides multiple installation options for different use cases
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MCP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$MCP_DIR")")"

print_header() {
    echo -e "${BLUE}"
    echo "==============================================="
    echo "    Fortinet MCP Server Installation"
    echo "==============================================="
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    print_success "Python 3 found: $(python3 --version)"
    
    # Check pip
    if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
        print_error "pip is required but not installed"
        exit 1
    fi
    print_success "pip found"
    
    # Check if in virtual environment (recommended)
    if [[ "$VIRTUAL_ENV" != "" ]]; then
        print_success "Virtual environment detected: $VIRTUAL_ENV"
    else
        print_warning "No virtual environment detected. Consider using one."
    fi
}

install_requirements() {
    print_info "Installing Python requirements..."
    
    if [ -f "$MCP_DIR/requirements.txt" ]; then
        pip install -r "$MCP_DIR/requirements.txt"
        print_success "Requirements installed"
    else
        print_warning "requirements.txt not found, installing basic requirements..."
        pip install requests fastmcp
        print_success "Basic requirements installed"
    fi
}

test_installation() {
    print_info "Testing MCP server installation..."
    
    cd "$MCP_DIR"
    if python3 test_server.py; then
        print_success "MCP server test completed"
    else
        print_warning "MCP server test had some issues (check output above)"
    fi
}

install_global() {
    print_info "Installing MCP server globally..."
    
    # Add to Python path
    BASHRC_LINE="export PYTHONPATH=\"$MCP_DIR:\$PYTHONPATH\""
    ALIAS_LINE="alias fortinet-mcp=\"cd $MCP_DIR && python3 fortinet_server_enhanced.py\""
    TEST_ALIAS="alias fortinet-test=\"cd $MCP_DIR && python3 test_server.py\""
    
    # Determine shell config file
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_CONFIG="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_CONFIG="$HOME/.zshrc"
    else
        SHELL_CONFIG="$HOME/.profile"
    fi
    
    # Add lines if they don't exist
    if ! grep -q "fortinet-mcp" "$SHELL_CONFIG" 2>/dev/null; then
        echo "" >> "$SHELL_CONFIG"
        echo "# Fortinet MCP Server" >> "$SHELL_CONFIG"
        echo "$BASHRC_LINE" >> "$SHELL_CONFIG"
        echo "$ALIAS_LINE" >> "$SHELL_CONFIG"
        echo "$TEST_ALIAS" >> "$SHELL_CONFIG"
        print_success "Added MCP server to $SHELL_CONFIG"
        print_info "Run 'source $SHELL_CONFIG' or restart your terminal"
    else
        print_success "MCP server already configured in $SHELL_CONFIG"
    fi
}

install_claude_desktop() {
    print_info "Setting up Claude Desktop integration..."
    
    # Determine Claude config path based on OS
    case "$(uname -s)" in
        Darwin)  # macOS
            CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
            ;;
        Linux)
            CLAUDE_CONFIG="$HOME/.config/claude/claude_desktop_config.json"
            ;;
        MINGW*|CYGWIN*|MSYS*)  # Windows
            CLAUDE_CONFIG="$APPDATA/Claude/claude_desktop_config.json"
            ;;
        *)
            print_error "Unsupported operating system"
            return 1
            ;;
    esac
    
    # Create config directory if it doesn't exist
    mkdir -p "$(dirname "$CLAUDE_CONFIG")"
    
    # Read environment variables for configuration
    read -p "Enter FortiGate Host (default: https://192.168.0.254): " FORTIGATE_HOST
    FORTIGATE_HOST=${FORTIGATE_HOST:-https://192.168.0.254}
    
    read -p "Enter FortiGate API Token: " FORTIGATE_API_TOKEN
    if [ -z "$FORTIGATE_API_TOKEN" ]; then
        print_error "API Token is required"
        return 1
    fi
    
    read -p "Enter FortiGate VDOM (default: root): " FORTIGATE_VDOM
    FORTIGATE_VDOM=${FORTIGATE_VDOM:-root}
    
    # Create Claude Desktop config
    cat > "$CLAUDE_CONFIG" << EOF
{
  "mcpServers": {
    "fortinet": {
      "command": "python3",
      "args": ["$MCP_DIR/fortinet_server_enhanced.py"],
      "env": {
        "FORTIGATE_HOST": "$FORTIGATE_HOST",
        "FORTIGATE_API_TOKEN": "$FORTIGATE_API_TOKEN",
        "FORTIGATE_VDOM": "$FORTIGATE_VDOM"
      }
    }
  }
}
EOF
    
    print_success "Claude Desktop configuration created at $CLAUDE_CONFIG"
    print_info "Restart Claude Desktop to activate the MCP server"
}

create_env_file() {
    print_info "Creating environment configuration file..."
    
    ENV_FILE="$MCP_DIR/.env"
    
    if [ -f "$ENV_FILE" ]; then
        print_warning ".env file already exists. Backing up..."
        cp "$ENV_FILE" "$ENV_FILE.backup"
    fi
    
    read -p "Enter FortiGate Host (default: https://192.168.0.254): " FORTIGATE_HOST
    FORTIGATE_HOST=${FORTIGATE_HOST:-https://192.168.0.254}
    
    read -p "Enter FortiGate API Token: " FORTIGATE_API_TOKEN
    read -p "Enter FortiGate Username (default: admin): " FORTIGATE_USERNAME
    FORTIGATE_USERNAME=${FORTIGATE_USERNAME:-admin}
    
    read -s -p "Enter FortiGate Password: " FORTIGATE_PASSWORD
    echo
    
    read -p "Enter FortiGate VDOM (default: root): " FORTIGATE_VDOM
    FORTIGATE_VDOM=${FORTIGATE_VDOM:-root}
    
    cat > "$ENV_FILE" << EOF
# Fortinet MCP Server Configuration
FORTIGATE_HOST=$FORTIGATE_HOST
FORTIGATE_API_TOKEN=$FORTIGATE_API_TOKEN
FORTIGATE_USERNAME=$FORTIGATE_USERNAME
FORTIGATE_PASSWORD=$FORTIGATE_PASSWORD
FORTIGATE_VDOM=$FORTIGATE_VDOM

# FortiManager Configuration (optional)
FORTIMANAGER_HOST=
FORTIMANAGER_API_TOKEN=
FORTIMANAGER_USERNAME=admin
FORTIMANAGER_PASSWORD=
EOF
    
    chmod 600 "$ENV_FILE"  # Secure permissions
    print_success "Environment file created at $ENV_FILE"
}

create_systemd_service() {
    print_info "Creating systemd service..."
    
    if [ "$EUID" -eq 0 ]; then
        print_error "Don't run this as root. Run as your regular user."
        return 1
    fi
    
    # Create user systemd directory
    mkdir -p "$HOME/.config/systemd/user"
    
    SERVICE_FILE="$HOME/.config/systemd/user/fortinet-mcp.service"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Fortinet MCP Server
After=network.target

[Service]
Type=simple
WorkingDirectory=$MCP_DIR
ExecStart=$(which python3) $MCP_DIR/fortinet_server_enhanced.py
Restart=always
RestartSec=10
EnvironmentFile=$MCP_DIR/.env

[Install]
WantedBy=default.target
EOF
    
    print_success "Systemd service created at $SERVICE_FILE"
    print_info "To enable: systemctl --user enable fortinet-mcp"
    print_info "To start: systemctl --user start fortinet-mcp"
    print_info "To view logs: journalctl --user -u fortinet-mcp -f"
}

show_usage_examples() {
    echo
    print_info "Usage Examples:"
    echo
    echo "1. Standalone usage:"
    echo "   cd $MCP_DIR"
    echo "   python3 fortinet_server_enhanced.py"
    echo
    echo "2. Test the server:"
    echo "   cd $MCP_DIR"
    echo "   python3 test_server.py"
    echo
    echo "3. Use as Python module:"
    echo "   python3 -c \"from fortinet_server_enhanced import fg_api; print(fg_api.test_connection())\""
    echo
    echo "4. With global aliases (after shell restart):"
    echo "   fortinet-mcp      # Start the server"
    echo "   fortinet-test     # Run tests"
    echo
}

main_menu() {
    while true; do
        echo
        print_header
        echo "Select installation option:"
        echo "1) Basic installation (requirements only)"
        echo "2) Global installation (add to PATH and aliases)"
        echo "3) Claude Desktop integration"
        echo "4) Create environment file"
        echo "5) Create systemd service"
        echo "6) Full installation (all of the above)"
        echo "7) Test installation"
        echo "8) Show usage examples"
        echo "9) Exit"
        echo
        read -p "Enter your choice (1-9): " choice
        
        case $choice in
            1)
                check_dependencies
                install_requirements
                print_success "Basic installation completed!"
                ;;
            2)
                install_global
                print_success "Global installation completed!"
                ;;
            3)
                install_claude_desktop
                print_success "Claude Desktop integration configured!"
                ;;
            4)
                create_env_file
                print_success "Environment file created!"
                ;;
            5)
                create_systemd_service
                print_success "Systemd service created!"
                ;;
            6)
                check_dependencies
                install_requirements
                create_env_file
                install_global
                install_claude_desktop
                create_systemd_service
                test_installation
                print_success "Full installation completed!"
                ;;
            7)
                test_installation
                ;;
            8)
                show_usage_examples
                ;;
            9)
                print_info "Installation script finished"
                exit 0
                ;;
            *)
                print_error "Invalid option"
                ;;
        esac
        
        echo
        read -p "Press Enter to continue..."
    done
}

# Script entry point
if [ $# -eq 0 ]; then
    main_menu
else
    case $1 in
        --basic)
            check_dependencies
            install_requirements
            ;;
        --global)
            install_global
            ;;
        --claude)
            install_claude_desktop
            ;;
        --env)
            create_env_file
            ;;
        --service)
            create_systemd_service
            ;;
        --full)
            check_dependencies
            install_requirements
            create_env_file
            install_global
            install_claude_desktop
            create_systemd_service
            test_installation
            ;;
        --test)
            test_installation
            ;;
        --help)
            echo "Usage: $0 [option]"
            echo "Options:"
            echo "  --basic    Basic installation"
            echo "  --global   Global installation"
            echo "  --claude   Claude Desktop integration"
            echo "  --env      Create environment file"
            echo "  --service  Create systemd service"
            echo "  --full     Full installation"
            echo "  --test     Test installation"
            echo "  --help     Show this help"
            echo
            echo "Run without arguments for interactive menu"
            ;;
        *)
            print_error "Unknown option: $1"
            print_info "Use --help for available options"
            exit 1
            ;;
    esac
fi