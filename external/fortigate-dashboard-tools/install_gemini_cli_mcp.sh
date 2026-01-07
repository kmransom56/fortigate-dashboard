#!/bin/bash

# Gemini CLI and MCP Servers Installation Script
# This script automates the installation of Google Gemini CLI and multiple MCP servers on WSL

set -e  # Exit on error

echo "========================================"
echo "Gemini CLI & MCP Servers Installation"
echo "========================================"
echo ""

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check for Node.js and npm
echo "${BLUE}Checking prerequisites...${NC}"
if ! command -v node &> /dev/null; then
    echo "${RED}Node.js is not installed. Installing Node.js LTS...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
    sudo apt-get install -y nodejs
else
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo "${RED}Node.js version 18+ required. Current: $(node -v)${NC}"
        echo "Upgrading Node.js..."
        curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
        sudo apt-get install -y nodejs
    else
        echo "${GREEN}Node.js $(node -v) detected ✓${NC}"
    fi
fi

if ! command -v npm &> /dev/null; then
    echo "${RED}npm not found. Installing...${NC}"
    sudo apt-get install -y npm
else
    echo "${GREEN}npm $(npm -v) detected ✓${NC}"
fi

# Install Gemini CLI
echo ""
echo "${BLUE}Installing Google Gemini CLI...${NC}"
npm install -g @google/gemini-cli
echo "${GREEN}Gemini CLI installed ✓${NC}"

# Create Gemini config directory
echo ""
echo "${BLUE}Setting up MCP configuration...${NC}"
GEMINI_CONFIG_DIR="$HOME/.gemini"
GEMINI_SETTINGS_FILE="$GEMINI_CONFIG_DIR/settings.json"

mkdir -p "$GEMINI_CONFIG_DIR"

# Create MCP configuration with all specified servers
cat > "$GEMINI_SETTINGS_FILE" << 'EOF'
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "playwright": {
      "command": "npx",
      "args": ["-y", "@executeautomation/playwright-mcp-server"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/$USER"]
    }
  }
}
EOF

echo "${GREEN}MCP configuration created at $GEMINI_SETTINGS_FILE ✓${NC}"

# Install Playwright dependencies
echo ""
echo "${BLUE}Installing Playwright browsers (this may take a few minutes)...${NC}"
npx playwright install

# Authentication instructions
echo ""
echo "${BLUE}========================================"
echo "Installation Complete! ✓"
echo "========================================${NC}"
echo ""
echo "${YELLOW}Next Steps - Authentication:${NC}"
echo ""
echo "When you first run 'gemini', you will be prompted to authenticate."
echo "Choose one of the following authentication methods:"
echo ""
echo "1. ${GREEN}Login with Google${NC} (Recommended)"
echo "   - Free tier: 60 requests/min, 1,000 requests/day"
echo "   - Access to Gemini 2.5 Pro with 1M token context"
echo "   - No API key management needed"
echo ""
echo "2. ${GREEN}Use Gemini API Key${NC}"
echo "   - Get your key from: https://aistudio.google.com/apikey"
echo "   - Set environment variable:"
echo "     export GEMINI_API_KEY="YOUR_API_KEY""
echo ""
echo "3. ${GREEN}Vertex AI${NC} (Enterprise)"
echo "   - Get your key from Google Cloud Console"
echo "   - Set environment variables:"
echo "     export GOOGLE_API_KEY="YOUR_API_KEY""
echo "     export GOOGLE_GENAI_USE_VERTEXAI=true"
echo ""
echo "${BLUE}To start Gemini CLI:${NC}"
echo "  gemini"
echo ""
echo "${BLUE}MCP servers configured in:${NC} $GEMINI_SETTINGS_FILE"
echo ""
echo "Available MCP servers:"
echo "  - GitHub"
echo "  - Sequential Thinking"
echo "  - Playwright"
echo "  - Filesystem"
echo ""
echo "To verify MCP servers in Gemini CLI, run:"
echo "  gemini"
echo "  Then type: /mcp"
echo ""
