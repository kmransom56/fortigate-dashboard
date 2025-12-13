# Port Registry Usage Guide

## Global Port Registry Utility

The `port-registry` command is now available globally from any directory. Use it whenever you need to add a new application or service.

## Quick Reference

### Find and Register (Recommended for New Applications)

```bash
# One command to find a free port and register it
PORT=$(port-registry find-and-register "app-name" "Description")
echo "Using port: $PORT"
```

### Manual Process

```bash
# 1. Find a free port
PORT=$(port-registry find)

# 2. Check it's available
port-registry check $PORT

# 3. Register it
port-registry register $PORT "app-name" "Description"
```

### Lookup and Verification

```bash
# Look up a specific port
port-registry lookup 11100

# List all ports (optionally filter)
port-registry list
port-registry list fortigate

# Show all active ports
port-registry show-all
```

## Usage Examples

### Adding a New Service to Any Project

```bash
# From any directory, find and register a port
cd /path/to/any/project
PORT=$(port-registry find-and-register "my-service" "My new service")

# Use the port in docker-compose.yml
# ports:
#   - "${PORT}:8000"
```

### Checking Before Using a Port

```bash
# Before assigning port 11120, check if it's free
port-registry check 11120
port-registry lookup 11120
```

### Viewing All FortiGate Dashboard Ports

```bash
# List all fortigate-related ports
port-registry list fortigate
```

## Integration with add-application.sh

When using `add-application.sh` in the chat-copilot directory, the script already uses port-manager internally. The `port-registry` utility provides the same functionality but is available globally for any project.

## Documentation

- **Global Guide**: `~/.local/bin/ADD_APPLICATION_GUIDE.md`
- **Registry File**: `~/.config/port_registry.md`
- **Project Script**: `./scripts/check_port.sh` (fortigate-dashboard specific)
