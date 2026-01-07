#!/usr/bin/env python3
"""
Gemini CLI and MCP Servers Installation Script with Custom Instructions
Automates the installation of Google Gemini CLI and multiple MCP servers on WSL
"""

import os
import sys
import subprocess
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = Colors.NC):
    """Print colored message to terminal"""
    print(f"{color}{message}{Colors.NC}")


def run_command(cmd: List[str], check: bool = True, capture_output: bool = False) -> Optional[subprocess.CompletedProcess]:
    """Execute a shell command"""
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture_output,
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        print_colored(f"Error executing command: {' '.join(cmd)}", Colors.RED)
        print_colored(f"Error: {e}", Colors.RED)
        if not check:
            return None
        sys.exit(1)


def check_command_exists(command: str) -> bool:
    """Check if a command exists in PATH"""
    result = run_command(["which", command], check=False, capture_output=True)
    return result.returncode == 0 if result else False


def get_version(command: str, flag: str = "--version") -> Optional[str]:
    """Get version of a command"""
    result = run_command([command, flag], check=False, capture_output=True)
    if result and result.returncode == 0:
        return result.stdout.strip()
    return None


def install_nodejs():
    """Install or upgrade Node.js to version 18+"""
    print_colored("Checking Node.js installation...", Colors.BLUE)

    if not check_command_exists("node"):
        print_colored("Node.js not found. Installing...", Colors.YELLOW)
        run_command(["curl", "-fsSL", "https://deb.nodesource.com/setup_lts.x", "-o", "/tmp/nodesource_setup.sh"])
        run_command(["sudo", "bash", "/tmp/nodesource_setup.sh"])
        run_command(["sudo", "apt-get", "install", "-y", "nodejs"])
    else:
        version_output = get_version("node", "-v")
        if version_output:
            version_num = int(version_output.split('.')[0].replace('v', ''))
            if version_num < 18:
                print_colored(f"Node.js {version_output} detected. Upgrading to v18+...", Colors.YELLOW)
                run_command(["curl", "-fsSL", "https://deb.nodesource.com/setup_lts.x", "-o", "/tmp/nodesource_setup.sh"])
                run_command(["sudo", "bash", "/tmp/nodesource_setup.sh"])
                run_command(["sudo", "apt-get", "install", "-y", "nodejs"])
            else:
                print_colored(f"Node.js {version_output} detected ✓", Colors.GREEN)

    if not check_command_exists("npm"):
        print_colored("npm not found. Installing...", Colors.YELLOW)
        run_command(["sudo", "apt-get", "install", "-y", "npm"])
    else:
        npm_version = get_version("npm")
        print_colored(f"npm {npm_version} detected ✓", Colors.GREEN)


def install_gemini_cli():
    """Install Google Gemini CLI"""
    print_colored("\nInstalling Google Gemini CLI...", Colors.BLUE)
    run_command(["npm", "install", "-g", "@google/gemini-cli"])
    print_colored("Gemini CLI installed ✓", Colors.GREEN)


def create_gemini_mcp_config():
    """Create Gemini MCP configuration file"""
    print_colored("\nSetting up MCP configuration...", Colors.BLUE)

    home = Path.home()
    gemini_config_dir = home / ".gemini"
    gemini_settings_file = gemini_config_dir / "settings.json"

    gemini_config_dir.mkdir(exist_ok=True)

    # Check if settings.json already exists and has content
    existing_config = {}
    if gemini_settings_file.exists():
        try:
            with open(gemini_settings_file, "r") as f:
                existing_config = json.load(f)
        except json.JSONDecodeError:
            print_colored("Existing settings.json is invalid. Creating new configuration.", Colors.YELLOW)

    # MCP configuration
    mcp_servers = {
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
            "args": ["-y", "@modelcontextprotocol/server-filesystem", str(home)]
        }
    }

    # Merge with existing configuration
    if "mcpServers" in existing_config:
        existing_config["mcpServers"].update(mcp_servers)
    else:
        existing_config["mcpServers"] = mcp_servers

    with open(gemini_settings_file, "w") as f:
        json.dump(existing_config, f, indent=2)

    print_colored(f"MCP configuration created at {gemini_settings_file} ✓", Colors.GREEN)
    return gemini_settings_file


def setup_gemini_custom_instructions():
    """Set up custom instructions for Gemini CLI"""
    print_colored("\nSetting up custom instructions...", Colors.BLUE)

    prompt_file = Path("prompt.md")
    instructions_created = []

    if not prompt_file.exists():
        print_colored("Warning: prompt.md not found in current directory.", Colors.RED)
        print("To add custom instructions later:")
        print("  - Repository level: Create GEMINI.md in repository root")
        print("  - Project level: Create .gemini/GEMINI.md")
        print("  - Global: Create ~/.gemini/GEMINI.md")
        return instructions_created

    # Repository-level instructions (GEMINI.md in root)
    gemini_root = Path("GEMINI.md")
    shutil.copy(prompt_file, gemini_root)
    instructions_created.append(f"Repository: {gemini_root}")
    print_colored(f"Custom instructions copied to {gemini_root} ✓", Colors.GREEN)

    # Project-level instructions (.gemini/GEMINI.md)
    project_gemini_dir = Path(".gemini")
    project_gemini_dir.mkdir(exist_ok=True)
    project_gemini_file = project_gemini_dir / "GEMINI.md"
    shutil.copy(prompt_file, project_gemini_file)
    instructions_created.append(f"Project: {project_gemini_file}")
    print_colored(f"Custom instructions copied to {project_gemini_file} ✓", Colors.GREEN)

    # Global instructions (~/.gemini/GEMINI.md)
    home = Path.home()
    global_gemini_dir = home / ".gemini"
    global_gemini_dir.mkdir(exist_ok=True)
    global_gemini_file = global_gemini_dir / "GEMINI.md"
    shutil.copy(prompt_file, global_gemini_file)
    instructions_created.append(f"Global: {global_gemini_file}")
    print_colored(f"Global custom instructions created at {global_gemini_file} ✓", Colors.GREEN)

    return instructions_created


def install_playwright_browsers():
    """Install Playwright browser binaries"""
    print_colored("\nInstalling Playwright browsers (this may take a few minutes)...", Colors.BLUE)
    run_command(["npx", "playwright", "install"])
    print_colored("Playwright browsers installed ✓", Colors.GREEN)


def print_authentication_instructions():
    """Print authentication instructions for Gemini CLI"""
    print()
    print_colored("=" * 70, Colors.GREEN)
    print_colored("Installation Complete! ✓", Colors.GREEN)
    print_colored("=" * 70, Colors.GREEN)
    print()
    print_colored("Next Steps - Authentication:", Colors.YELLOW)
    print()
    print("When you first run 'gemini', you will be prompted to authenticate.")
    print("Choose one of the following authentication methods:")
    print()
    print_colored("1. Login with Google (Recommended)", Colors.GREEN)
    print("   - Free tier: 60 requests/min, 1,000 requests/day")
    print("   - Access to Gemini 2.5 Pro with 1M token context")
    print("   - No API key management needed")
    print()
    print_colored("2. Use Gemini API Key", Colors.GREEN)
    print("   - Get your key from: https://aistudio.google.com/apikey")
    print("   - Set environment variable:")
    print("     export GEMINI_API_KEY=\"YOUR_API_KEY\"")
    print()
    print_colored("3. Vertex AI (Enterprise)", Colors.GREEN)
    print("   - Get your key from Google Cloud Console")
    print("   - Set environment variables:")
    print("     export GOOGLE_API_KEY=\"YOUR_API_KEY\"")
    print("     export GOOGLE_GENAI_USE_VERTEXAI=true")
    print()
    print_colored("To start Gemini CLI:", Colors.BLUE)
    print("  gemini")
    print()


def main():
    """Main installation function"""
    print_colored("=" * 70, Colors.GREEN)
    print_colored("Gemini CLI & MCP Servers Installation", Colors.GREEN)
    print_colored("=" * 70, Colors.GREEN)
    print()

    # Check if running on Linux (WSL)
    if sys.platform != "linux":
        print_colored("Warning: This script is designed for WSL/Linux systems.", Colors.YELLOW)
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != 'y':
            sys.exit(0)

    try:
        # Installation steps
        install_nodejs()
        install_gemini_cli()
        config_file = create_gemini_mcp_config()
        instructions_created = setup_gemini_custom_instructions()
        install_playwright_browsers()

        # Print MCP configuration location
        print_colored(f"\nMCP servers configured in: {config_file}", Colors.BLUE)

        # Print custom instructions locations
        if instructions_created:
            print()
            print("Custom Instructions:")
            for instruction in instructions_created:
                print(f"  - {instruction} ✓")

        # Print authentication instructions
        print_authentication_instructions()

        print("Available MCP servers:")
        print("  - GitHub")
        print("  - Sequential Thinking")
        print("  - Playwright")
        print("  - Filesystem")
        print()
        print("To verify MCP servers in Gemini CLI, run:")
        print("  gemini")
        print("  Then type: /mcp")
        print()
        print("To view loaded context/instructions:")
        print("  /memory show")
        print()

    except KeyboardInterrupt:
        print_colored("\n\nInstallation cancelled by user.", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n\nAn error occurred: {e}", Colors.RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
