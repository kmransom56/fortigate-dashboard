# FortiGate Dashboard Scripts

## Port Registry Utility

The `check_port.sh` script provides a convenient wrapper around the system-wide `port-manager` command for checking port availability and looking up port information in the registry.

### Usage

```bash
# Check if a port is in use (checks both system and registry)
./scripts/check_port.sh check <port>

# Find a free port in a range (default: 11000-12000)
./scripts/check_port.sh find [start] [end]

# Look up port information in the registry
./scripts/check_port.sh lookup <port>

# List all fortigate-dashboard registered ports
./scripts/check_port.sh list

# Register a new port in the registry
./scripts/check_port.sh register <port> <app-name> <description>

# Show all active listening ports
./scripts/check_port.sh show-all
```

### Examples

```bash
# Check if port 8000 is available
./scripts/check_port.sh check 8000

# Find a free port for a new service
PORT=$(./scripts/check_port.sh find 11110 11120)
echo "Using port: $PORT"

# Look up information about port 11100
./scripts/check_port.sh lookup 11100

# See all registered fortigate-dashboard ports
./scripts/check_port.sh list

# Register a new port
./scripts/check_port.sh register 11110 "fortigate-new-service" "New service description"
```

### Current FortiGate Dashboard Ports

Based on the registry, the following ports are registered for fortigate-dashboard:

- **11100** - fortigate-dashboard (Docker Container)
- **11101** - fortigate-redis (Docker Container)
- **11102** - fortigate-postgres (Docker Container)
- **11103** - fortigate-neo4j (Docker Container)
- **11104** - fortigate-neo4j (Docker Container)
- **11105** - fortigate-prometheus (Docker Container)
- **11106** - fortigate-grafana (Docker Container)
- **11107** - fortigate-nginx (Docker Container)
- **11108** - fortigate-nginx (Docker Container)

### Port Registry Location

The global port registry is maintained at: `~/.config/port_registry.md`

This registry is shared across all projects on the system to prevent port conflicts.
