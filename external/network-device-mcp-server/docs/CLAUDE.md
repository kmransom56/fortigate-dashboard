# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is a Model Context Protocol (MCP) server for managing FortiGate, FortiManager, and Cisco Meraki network devices. It provides unified API access to these platforms for automation and integration with Claude Desktop and Power Automate workflows.

## Development Commands

### Environment Setup
```bash
# Install dependencies
install.bat                    # Full setup including virtual environment
venv\Scripts\activate.bat      # Activate virtual environment manually
pip install -r requirements.txt

# Configuration
notepad config\devices.json.user    # Edit device configuration
```

### Server Operations
```bash
# Testing and validation
test-server.bat               # Test MCP server startup and connectivity
validate-config.bat          # Validate configuration files
python src\main.py           # Run server directly (for debugging)

# Claude Desktop integration
setup-claude-config.bat      # Configure Claude Desktop integration
setup-claude.bat             # Alternative setup method
```

### Development and Testing
```bash
# Run specific tests
python -m pytest            # If tests exist (check for test files)
python validate-config.py   # Validate configuration programmatically

# Debug configuration
python debug_config.py      # Debug configuration loading
python test_env_loading.py  # Test environment variable loading
```

## Architecture

### Core Components

- **`src/main.py`** - Main MCP server implementation with tool registration and request routing
- **`src/config.py`** - Configuration management with absolute path resolution for deployment flexibility
- **`src/platforms/`** - Platform-specific API managers:
  - `fortigate.py` - FortiGate REST API management
  - `fortimanager.py` - FortiManager JSON-RPC API management  
  - `meraki.py` - Cisco Meraki Dashboard API management
  - `fortianalyzer.py` - FortiAnalyzer integration

### Configuration System

The configuration system uses environment variables with fallback to `.env` file:

- **FortiManager instances**: `FORTIMANAGER_{ARBYS|BWW|SONIC}_{HOST|USERNAME|PASSWORD}`
- **FortiGate devices**: `FORTIGATE_DEVICE_{N}_{NAME|HOST|TOKEN}` (numbered 1, 2, 3...)
- **Meraki**: `MERAKI_API_KEY`, `MERAKI_ORG_ID`
- **Paths**: `BACKUP_PATH`, `REPORT_PATH`

Configuration is loaded with absolute path resolution to support both local development and GitHub Actions deployment.

### MCP Tool Architecture

Tools are registered dynamically based on available device configurations:

1. **FortiManager Tools** - Always available if instances are configured
2. **FortiGate Tools** - Added if `fortigate_devices` exist  
3. **Meraki Tools** - Added if `has_meraki_config()` returns true
4. **Universal Tools** - Configuration status and network infrastructure summary

### Platform Managers

Each platform manager in `src/platforms/` implements:
- Async API communication using `httpx`
- Authentication handling (tokens, session management)
- Error handling and logging
- Device-specific data formatting

### Path Resolution Strategy

The system uses absolute path resolution throughout to support:
- Local development (`C:\Users\keith.ransom\network-device-mcp-server`)  
- GitHub Actions deployment (dynamic paths)
- Virtual environment activation from any working directory

Key paths are resolved in `config.py` using `Path(__file__).parent.resolve()` pattern.

## Testing Strategy

- **`test-server.bat`** - Comprehensive server testing with timeout and diagnostics
- **Configuration validation** - JSON syntax and network connectivity checks
- **Dependency verification** - Python environment and package availability
- **MCP protocol testing** - Server startup and tool registration verification

## Deployment Patterns

### Local Development
1. Run `install.bat` for full setup
2. Edit `config\devices.json.user` with actual credentials  
3. Use `setup-claude-config.bat` for Claude Desktop integration

### Production/CI
- Environment variables take precedence over `.env` file
- GitHub Actions deployment supported via environment detection
- Absolute path resolution handles varying execution contexts

## Integration Architecture

- **Claude Desktop** - Direct MCP integration via stdio transport
- **Power Automate** - File-based integration patterns with report generation
- **Multi-platform reporting** - Unified status across FortiGate/FortiManager/Meraki

## Common Development Tasks

### Adding New Platform Support
1. Create new manager class in `src/platforms/new_platform.py`
2. Import and initialize in `src/main.py` 
3. Add tool definitions to `setup_tools()` method
4. Add configuration loading to `src/config.py`

### Adding New Tools
1. Add tool definition to `list_tools()` in `src/main.py`
2. Create handler method `_handle_new_tool()` 
3. Add routing logic to `handle_call_tool()` dispatcher
4. Update configuration checks if device-specific

### Debugging Connection Issues
1. Use `validate-config.bat` to check configuration syntax
2. Run `python debug_config.py` to verify credential loading
3. Check `logs/network-mcp-server.log` for detailed error information
4. Test individual platform connectivity before full server startup