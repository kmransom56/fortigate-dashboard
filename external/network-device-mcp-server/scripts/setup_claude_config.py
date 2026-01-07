#!/usr/bin/env python3
"""
Claude Desktop Configuration Setup Script
Adds the Network Device MCP Server to Claude Desktop configuration
"""

import json
import os
import sys
from pathlib import Path

def main():
    print("Claude Desktop Configuration Setup")
    print("=" * 40)
    print()
    
    # Get paths
    claude_config_dir = Path(os.environ['APPDATA']) / 'Claude'
    claude_config_file = claude_config_dir / 'claude_desktop_config.json'
    server_path = Path.cwd()
    
    print(f"Claude config directory: {claude_config_dir}")
    print(f"Config file: {claude_config_file}")
    print(f"Server path: {server_path}")
    print()
    
    # Create Claude config directory if it doesn't exist
    claude_config_dir.mkdir(exist_ok=True)
    
    # Load existing config or create new one
    config = {}
    if claude_config_file.exists():
        try:
            with open(claude_config_file, 'r') as f:
                config = json.load(f)
            print("✓ Loaded existing Claude configuration")
        except (json.JSONDecodeError, Exception) as e:
            print(f"⚠️  Warning: Could not read existing config ({e}), creating new one")
            config = {}
    else:
        print("✓ Creating new Claude configuration")
    
    # Ensure mcpServers section exists
    if 'mcpServers' not in config:
        config['mcpServers'] = {}
    
    # Add network device MCP server
    config['mcpServers']['network-devices'] = {
        "command": "python",
        "args": [str(server_path / "src" / "main.py")],
        "env": {
            "PYTHONPATH": str(server_path / "src"),
            "CONFIG_FILE": str(server_path / "config" / "devices.json")
        }
    }
    
    # Add other MCP servers if they don't exist
    if 'filesystem' not in config['mcpServers']:
        config['mcpServers']['filesystem'] = {
            "command": "npx",
            "args": [
                "@modelcontextprotocol/server-filesystem",
                str(Path.home())
            ]
        }
    
    if 'github' not in config['mcpServers']:
        config['mcpServers']['github'] = {
            "command": "npx",
            "args": ["@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": ""
            }
        }
    
    # Add global shortcut if not present
    if 'globalShortcut' not in config:
        config['globalShortcut'] = "Ctrl+Alt+Space"
    
    # Write configuration
    try:
        with open(claude_config_file, 'w') as f:
            json.dump(config, f, indent=2)
        print("✓ Claude Desktop configuration updated successfully!")
    except Exception as e:
        print(f"❌ Error writing configuration: {e}")
        return 1
    
    print()
    print("Configuration Summary:")
    print("-" * 20)
    print(f"Config file: {claude_config_file}")
    print("MCP Servers configured:")
    for server_name in config['mcpServers']:
        print(f"  - {server_name}")
    
    print()
    print("Next Steps:")
    print("1. Edit config/devices.json with your actual device credentials")
    print("2. Run 'install.bat' to install Python dependencies")
    print("3. Run 'test-server.bat' to test the MCP server")
    print("4. Restart Claude Desktop completely")
    print("5. Try: 'Show me network device management tools' in Claude")
    
    # Check Python installation
    print()
    print("Checking Python installation...")
    try:
        import subprocess
        result = subprocess.run(['python', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Python is available: {result.stdout.strip()}")
        else:
            print("⚠️  Python not found via 'python' command")
            check_py_command()
    except Exception:
        print("⚠️  Could not check Python installation")
        check_py_command()
    
    return 0

def check_py_command():
    """Check if 'py' command is available as alternative"""
    try:
        import subprocess
        result = subprocess.run(['py', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Python is available via 'py' command: {result.stdout.strip()}")
            print("Note: You may need to change 'python' to 'py' in the Claude config")
        else:
            print("❌ Neither 'python' nor 'py' commands are available")
    except Exception:
        print("❌ Could not find Python installation")

if __name__ == '__main__':
    sys.exit(main())
