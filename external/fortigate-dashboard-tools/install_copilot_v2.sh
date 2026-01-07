#!/bin/bash

# Copilot CLI and MCP Servers Installation Script (Ubuntu 24.04 Compatible)
# Includes: GitHub, Sequential Thinking, Playwright, Filesystem, Memory Bank, Desktop Commander
# This script automates the installation of GitHub Copilot CLI and multiple MCP servers on WSL

set -e  # Exit on error

echo "========================================"
echo "Copilot CLI & MCP Servers Installation"
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
    if [ "$NODE_VERSION" -lt 22 ]; then
        echo "${RED}Node.js version 22+ required. Current: $(node -v)${NC}"
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

# Install GitHub CLI if not already installed
echo ""
echo "${BLUE}Installing GitHub CLI (gh)...${NC}"
if ! command -v gh &> /dev/null; then
    type -p curl >/dev/null || sudo apt install curl -y
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
    sudo chmod go+r /usr/share/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
    sudo apt update
    sudo apt install gh -y
    echo "${GREEN}GitHub CLI installed ✓${NC}"
else
    echo "${GREEN}GitHub CLI already installed ✓${NC}"
fi

# Install Copilot CLI
echo ""
echo "${BLUE}Installing GitHub Copilot CLI...${NC}"
npm install -g @github/copilot
echo "${GREEN}Copilot CLI installed ✓${NC}"

# Create MCP config directory
echo ""
echo "${BLUE}Setting up MCP configuration...${NC}"
MCP_CONFIG_DIR="$HOME/.copilot"
MCP_CONFIG_FILE="$MCP_CONFIG_DIR/mcp-config.json"

mkdir -p "$MCP_CONFIG_DIR"

# Create MCP configuration with all specified servers
cat > "$MCP_CONFIG_FILE" << EOF
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

echo "${GREEN}MCP configuration created at $MCP_CONFIG_FILE ✓${NC}"

# Set up custom instructions (AGENTS.md or copilot-instructions.md)
echo ""
echo "${BLUE}Setting up custom instructions...${NC}"

# Check if prompt.md exists in current directory
if [ -f "prompt.md" ]; then
    # Create .github directory if it doesn't exist
    mkdir -p .github

    # Copy to .github/copilot-instructions.md
    cp prompt.md .github/copilot-instructions.md
    echo "${GREEN}Custom instructions copied to .github/copilot-instructions.md ✓${NC}"

    # Also create AGENTS.md in root (for agent mode)
    cp prompt.md AGENTS.md
    echo "${GREEN}Custom instructions copied to AGENTS.md ✓${NC}"

    # Create global instructions directory
    GLOBAL_COPILOT_DIR="$HOME/.config/github-copilot"
    mkdir -p "$GLOBAL_COPILOT_DIR"
    cp prompt.md "$GLOBAL_COPILOT_DIR/global-copilot-instructions.md"
    echo "${GREEN}Global custom instructions created at $GLOBAL_COPILOT_DIR/global-copilot-instructions.md ✓${NC}"
else
    echo "${RED}Warning: prompt.md not found in current directory.${NC}"
    echo "To add custom instructions later:"
    echo "  - Repository level: Create .github/copilot-instructions.md"
    echo "  - Agent mode: Create AGENTS.md in repository root"
    echo "  - Global: Create ~/.config/github-copilot/global-copilot-instructions.md"
fi

# Install Playwright and its dependencies
echo ""
echo "${BLUE}Installing Playwright and system dependencies...${NC}"
echo "This may take a few minutes..."

# Install Playwright package first
npm install -g @playwright/test

# Install system dependencies for Playwright (Ubuntu 24.04 Noble compatible)
echo ""
echo "${BLUE}Installing Playwright system dependencies...${NC}"
sudo apt-get update

# Use npx playwright install-deps which handles package name differences automatically
echo "${BLUE}Using Playwright's automated dependency installer...${NC}"
sudo npx playwright install-deps

echo "${GREEN}System dependencies installed ✓${NC}"

# Now install Playwright browsers
echo ""
echo "${BLUE}Installing Playwright browsers...${NC}"
npx playwright install

echo "${GREEN}Playwright installation complete ✓${NC}"

# Authenticate with GitHub
echo ""
echo "${BLUE}GitHub Authentication...${NC}"
echo "You need to authenticate with GitHub to use Copilot CLI."
echo "Choose one of the following methods:"
echo ""
echo "1. Device Code Flow (Recommended for headless/SSH)"
echo "2. Skip authentication (do it later manually)"
echo ""
read -p "Enter your choice (1 or 2): " auth_choice

if [ "$auth_choice" = "1" ]; then
    echo ""
    echo "${BLUE}Starting GitHub authentication...${NC}"
    echo "This will open https://github.com/login/device in your browser."
    echo "If you're on SSH, copy the code and visit the URL manually."
    echo ""
    gh auth login --web -h github.com
    echo ""
    echo "${GREEN}Authentication complete ✓${NC}"
elif [ "$auth_choice" = "2" ]; then
    echo ""
    echo "${BLUE}Skipping authentication. You can authenticate later by running:${NC}"
    echo "  gh auth login --web -h github.com"
else
    echo "${RED}Invalid choice. Skipping authentication.${NC}"
fi

echo ""
echo "${GREEN}========================================"
echo "Installation Complete! ✓"
echo "========================================${NC}"
echo ""
echo "Next steps:"
echo "1. If you skipped authentication, run: gh auth login --web -h github.com"
echo "2. Start Copilot CLI by running: copilot"
echo "3. MCP servers are configured in: $MCP_CONFIG_FILE"
echo ""
echo "Custom Instructions:"
if [ -f ".github/copilot-instructions.md" ]; then
    echo "  - Repository: .github/copilot-instructions.md ✓"
    echo "  - Agent mode: AGENTS.md ✓"
    echo "  - Global: ~/.config/github-copilot/global-copilot-instructions.md ✓"
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
echo "To verify your setup:"
echo "  gh auth status"
echo "  copilot"
echo ""
