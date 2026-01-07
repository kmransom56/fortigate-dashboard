#!/usr/bin/env python3
"""
Copilot CLI and MCP Servers Installation Script with Custom Instructions
Automates the installation of GitHub Copilot CLI and multiple MCP servers on WSL
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
    """Install or upgrade Node.js to version 22+"""
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
            if version_num < 22:
                print_colored(f"Node.js {version_output} detected. Upgrading to v22+...", Colors.YELLOW)
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


def install_github_cli():
    """Install GitHub CLI (gh)"""
    print_colored("\nInstalling GitHub CLI...", Colors.BLUE)

    if check_command_exists("gh"):
        print_colored("GitHub CLI already installed ✓", Colors.GREEN)
        return

    # Install GitHub CLI
    run_command(["sudo", "apt-get", "update"])
    run_command(["sudo", "apt-get", "install", "-y", "curl"])

    # Download and add GitHub CLI repository
    run_command([
        "bash", "-c",
        "curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | "
        "sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg"
    ])
    run_command(["sudo", "chmod", "go+r", "/usr/share/keyrings/githubcli-archive-keyring.gpg"])

    arch = subprocess.check_output(["dpkg", "--print-architecture"], text=True).strip()
    repo_line = f"deb [arch={arch} signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main"

    with open("/tmp/github-cli.list", "w") as f:
        f.write(repo_line)
    run_command(["sudo", "mv", "/tmp/github-cli.list", "/etc/apt/sources.list.d/github-cli.list"])

    run_command(["sudo", "apt-get", "update"])
    run_command(["sudo", "apt-get", "install", "-y", "gh"])

    print_colored("GitHub CLI installed ✓", Colors.GREEN)


def install_copilot_cli():
    """Install GitHub Copilot CLI"""
    print_colored("\nInstalling GitHub Copilot CLI...", Colors.BLUE)
    run_command(["npm", "install", "-g", "@github/copilot"])
    print_colored("Copilot CLI installed ✓", Colors.GREEN)


def create_mcp_config():
    """Create MCP configuration file"""
    print_colored("\nSetting up MCP configuration...", Colors.BLUE)

    home = Path.home()
    mcp_config_dir = home / ".copilot"
    mcp_config_file = mcp_config_dir / "mcp-config.json"

    mcp_config_dir.mkdir(exist_ok=True)

    # MCP configuration
    config = {
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
                "args": ["-y", "@modelcontextprotocol/server-filesystem", str(home)]
            }
        }
    }

    with open(mcp_config_file, "w") as f:
        json.dump(config, f, indent=2)

    print_colored(f"MCP configuration created at {mcp_config_file} ✓", Colors.GREEN)
    return mcp_config_file


def setup_custom_instructions():
    """Set up custom instructions for Copilot CLI"""
    print_colored("\nSetting up custom instructions...", Colors.BLUE)

    prompt_file = Path("prompt.md")
    instructions_created = []

    if not prompt_file.exists():
        print_colored("Warning: prompt.md not found in current directory.", Colors.RED)
        print("To add custom instructions later:")
        print("  - Repository level: Create .github/copilot-instructions.md")
        print("  - Agent mode: Create AGENTS.md in repository root")
        print("  - Global: Create ~/.config/github-copilot/global-copilot-instructions.md")
        return instructions_created

    # Repository-level instructions (.github/copilot-instructions.md)
    github_dir = Path(".github")
    github_dir.mkdir(exist_ok=True)
    copilot_instructions = github_dir / "copilot-instructions.md"
    shutil.copy(prompt_file, copilot_instructions)
    instructions_created.append(f"Repository: {copilot_instructions}")
    print_colored(f"Custom instructions copied to {copilot_instructions} ✓", Colors.GREEN)

    # Agent mode instructions (AGENTS.md)
    agents_file = Path("AGENTS.md")
    shutil.copy(prompt_file, agents_file)
    instructions_created.append(f"Agent mode: {agents_file}")
    print_colored(f"Custom instructions copied to {agents_file} ✓", Colors.GREEN)

    # Global instructions
    home = Path.home()
    global_copilot_dir = home / ".config" / "github-copilot"
    global_copilot_dir.mkdir(parents=True, exist_ok=True)
    global_instructions = global_copilot_dir / "global-copilot-instructions.md"
    shutil.copy(prompt_file, global_instructions)
    instructions_created.append(f"Global: {global_instructions}")
    print_colored(f"Global custom instructions created at {global_instructions} ✓", Colors.GREEN)

    return instructions_created


def install_playwright_browsers():
    """Install Playwright browser binaries"""
    print_colored("\nInstalling Playwright browsers (this may take a few minutes)...", Colors.BLUE)
    run_command(["npx", "playwright", "install"])
    print_colored("Playwright browsers installed ✓", Colors.GREEN)


def authenticate_github():
    """Authenticate with GitHub"""
    print_colored("\nGitHub Authentication", Colors.BLUE)
    print("You need to authenticate with GitHub to use Copilot CLI.")
    print("\nChoose one of the following methods:")
    print("1. Device Code Flow (Recommended for headless/SSH)")
    print("2. Skip authentication (do it later manually)")

    try:
        choice = input("\nEnter your choice (1 or 2): ").strip()

        if choice == "1":
            print_colored("\nStarting GitHub authentication...", Colors.BLUE)
            print("This will provide a code for https://github.com/login/device")
            print("If you're on SSH, copy the code and visit the URL manually.\n")
            run_command(["gh", "auth", "login", "--web", "-h", "github.com"])
            print_colored("\nAuthentication complete ✓", Colors.GREEN)
        elif choice == "2":
            print_colored("\nSkipping authentication. You can authenticate later by running:", Colors.BLUE)
            print("  gh auth login --web -h github.com")
        else:
            print_colored("Invalid choice. Skipping authentication.", Colors.YELLOW)
    except KeyboardInterrupt:
        print_colored("\n\nAuthentication cancelled.", Colors.YELLOW)


def main():
    """Main installation function"""
    print_colored("=" * 60, Colors.GREEN)
    print_colored("Copilot CLI & MCP Servers Installation", Colors.GREEN)
    print_colored("=" * 60, Colors.GREEN)
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
        install_github_cli()
        install_copilot_cli()
        config_file = create_mcp_config()
        instructions_created = setup_custom_instructions()
        install_playwright_browsers()
        authenticate_github()

        # Print completion message
        print()
        print_colored("=" * 60, Colors.GREEN)
        print_colored("Installation Complete! ✓", Colors.GREEN)
        print_colored("=" * 60, Colors.GREEN)
        print()
        print("Next steps:")
        print("1. If you skipped authentication, run: gh auth login --web -h github.com")
        print("2. Start Copilot CLI by running: copilot")
        print(f"3. MCP servers are configured in: {config_file}")
        print()

        if instructions_created:
            print("Custom Instructions:")
            for instruction in instructions_created:
                print(f"  - {instruction} ✓")
            print()

        print("Available MCP servers:")
        print("  - GitHub")
        print("  - Sequential Thinking")
        print("  - Playwright")
        print("  - Filesystem")
        print()
        print("To verify your setup:")
        print("  gh auth status")
        print("  copilot")
        print()

    except KeyboardInterrupt:
        print_colored("\n\nInstallation cancelled by user.", Colors.RED)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n\nAn error occurred: {e}", Colors.RED)
        sys.exit(1)


if __name__ == "__main__":
    main()
