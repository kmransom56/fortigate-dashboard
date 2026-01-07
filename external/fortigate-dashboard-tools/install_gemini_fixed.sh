#!/bin/bash

# Gemini CLI and MCP Servers Installation Script (Fixed)
# Includes: GitHub, Sequential Thinking, Playwright, Filesystem, Memory Bank, Desktop Commander
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

# Fix npm prefix issue if it exists
echo ""
echo "${BLUE}Checking npm configuration...${NC}"
if [ -f "$HOME/.npmrc" ]; then
    if grep -q "^prefix=" "$HOME/.npmrc"; then
        echo "${YELLOW}Found npm prefix configuration in ~/.npmrc${NC}"
        echo "Backing up and removing problematic prefix setting..."
        cp "$HOME/.npmrc" "$HOME/.npmrc.backup"
        sed -i '/^prefix=/d' "$HOME/.npmrc"
        echo "${GREEN}npm configuration fixed ✓${NC}"
    fi
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
cat > "$GEMINI_SETTINGS_FILE" << EOF
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
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "$HOME"]
    },
    "memory-bank": {
      "command": "npx",
      "args": ["-y", "@movibe/memory-bank-mcp", "--mode", "code"]
    },
    "desktop-commander": {
      "command": "npx",
      "args": ["-y", "@wonderwhy-er/desktop-commander"]
    }
  }
}
EOF

echo "${GREEN}MCP configuration created at $GEMINI_SETTINGS_FILE ✓${NC}"

# Set up custom instructions (GEMINI.md)
echo ""
echo "${BLUE}Setting up custom instructions...${NC}"

# Check if prompt.md exists in current directory
if [ -f "prompt.md" ]; then
    # Copy to GEMINI.md in repository root
    cp prompt.md GEMINI.md
    echo "${GREEN}Custom instructions copied to GEMINI.md ✓${NC}"

    # Also copy to project .gemini directory
    mkdir -p .gemini
    cp prompt.md .gemini/GEMINI.md
    echo "${GREEN}Custom instructions copied to .gemini/GEMINI.md ✓${NC}"

    # Create global instructions
    cp prompt.md "$GEMINI_CONFIG_DIR/GEMINI.md"
    echo "${GREEN}Global custom instructions created at $GEMINI_CONFIG_DIR/GEMINI.md ✓${NC}"
else
    echo "${RED}Warning: prompt.md not found in current directory.${NC}"
    echo "To add custom instructions later:"
    echo "  - Repository level: Create GEMINI.md in repository root"
    echo "  - Project level: Create .gemini/GEMINI.md"
    echo "  - Global: Create ~/.gemini/GEMINI.md"
fi

# Install Playwright and its dependencies
echo ""
echo "${BLUE}Installing Playwright and system dependencies...${NC}"
echo "This may take a few minutes..."

# Install Playwright package first
npm install -g @playwright/test

# Install system dependencies for Playwright
echo ""
echo "${BLUE}Installing Playwright system dependencies...${NC}"
sudo apt-get update
sudo apt-get install -y \
    libgstreamer-plugins-bad1.0-0 \
    libavif16 \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite0 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0

# Now install Playwright browsers
echo ""
echo "${BLUE}Installing Playwright browsers...${NC}"
npx playwright install

echo "${GREEN}Playwright installation complete ✓${NC}"

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
echo "Custom Instructions:"
if [ -f "GEMINI.md" ]; then
    echo "  - Repository: GEMINI.md ✓"
    echo "  - Project: .gemini/GEMINI.md ✓"
    echo "  - Global: ~/.gemini/GEMINI.md ✓"
fi
echo ""
echo "Available MCP servers:"
echo "  - GitHub (API access)"
echo "  - Sequential Thinking (problem-solving)"
echo "  - Playwright (browser automation)"
echo "  - Filesystem (file operations)"
echo "  - Memory Bank (persistent context across sessions)"
echo "  - Desktop Commander (terminal, process control, code editing)"
echo ""
echo "${YELLOW}Memory Bank Features:${NC}"
echo "  - Stores project context in memory-bank/ directory"
echo "  - Tracks progress, decisions, and system patterns"
echo "  - Maintains context across AI sessions"
echo ""
echo "${YELLOW}Desktop Commander Features:${NC}"
echo "  - Execute terminal commands with live output"
echo "  - Manage files and directories"
echo "  - Search and edit code"
echo "  - Control running processes"
echo ""
echo "To verify MCP servers in Gemini CLI, run:"
echo "  gemini"
echo "  Then type: /mcp"
echo ""
echo "To view loaded context/instructions:"
echo "  /memory show"
echo ""
