# Network Device MCP Server

A Model Context Protocol (MCP) server for managing network infrastructure including FortiManager, FortiGate, and Cisco Meraki platforms. This server integrates with Claude Desktop to provide network device management capabilities through natural language interactions.

## Features

- **Multi-platform Support**: FortiManager, FortiGate, and Cisco Meraki
- **GitHub Secrets Integration**: Secure credential management
- **Enterprise Ready**: Corporate SSL/proxy support
- **Comprehensive Tools**: Device management, policy deployment, backup operations
- **Claude Integration**: Natural language network management

## Quick Start

### 1. Repository Setup

```bash
git clone https://github.com/YOUR_USERNAME/network-device-mcp-server.git
cd network-device-mcp-server
```

### 2. Environment Setup

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

#### Option A: Local Development (.env file)
```bash
cp .env.example .env
# Edit .env with your credentials
```

#### Option B: GitHub Secrets (Recommended for production)
1. Go to your repository Settings > Secrets and variables > Actions
2. Add the following secrets:
   - `FORTIMANAGER_ARBYS_HOST`
   - `FORTIMANAGER_ARBYS_USERNAME`
   - `FORTIMANAGER_ARBYS_PASSWORD`
   - `FORTIMANAGER_BWW_HOST`
   - `FORTIMANAGER_BWW_USERNAME`
   - `FORTIMANAGER_BWW_PASSWORD`
   - `FORTIMANAGER_SONIC_HOST`
   - `FORTIMANAGER_SONIC_USERNAME`
   - `FORTIMANAGER_SONIC_PASSWORD`
   - `MERAKI_API_KEY`
   - `MERAKI_ORG_ID`

### 4. Claude Desktop Integration

Add to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "network-devices": {
      "command": "python",
      "args": ["C:\\path\\to\\network-device-mcp-server\\src\\main.py"],
      "env": {
        "PYTHONPATH": "C:\\path\\to\\network-device-mcp-server\\src"
      }
    }
  }
}
```

## Available Tools

### FortiManager Operations
- `list_fortimanager_instances` - List all available FortiManager instances
- `get_fortimanager_devices` - Get managed devices from FortiManager
- `get_policy_packages` - List policy packages
- `install_policy_package` - Deploy policies to devices

### FortiGate Operations
- `list_fortigate_devices` - List configured FortiGate devices
- `get_fortigate_system_status` - Get device system status

### Meraki Operations
- `get_meraki_organizations` - List Meraki organizations
- `get_meraki_networks` - Get networks in organization
- `get_meraki_devices` - Get devices in network

### Infrastructure Summary
- `get_network_infrastructure_summary` - Comprehensive infrastructure overview
- `show_configuration_status` - Current server configuration

## Usage Examples

### Query Network Infrastructure
```
"Show me a summary of all our network infrastructure"
```

### Deploy Policies
```
"Install the 'Production-Policy' package to devices in the BWW FortiManager"
```

### Check Device Status
```
"What's the current status of our main firewall?"
```

### Backup Operations
```
"List all devices managed by the Arbys FortiManager and create a backup report"
```

## Configuration Details

### FortiManager Configuration
Each FortiManager instance requires:
- `HOST`: IP address or hostname
- `USERNAME`: Administrator username
- `PASSWORD`: Administrator password

### FortiGate Configuration
Each FortiGate device requires:
- `NAME`: Friendly name for the device
- `HOST`: IP address or hostname  
- `TOKEN`: API access token

### Meraki Configuration
Meraki integration requires:
- `API_KEY`: Meraki Dashboard API key
- `ORG_ID`: Target organization ID

### Corporate Network Support
For corporate environments with SSL interception:
```bash
# Environment variables
SSL_VERIFY=false
PYTHONHTTPSVERIFY=0
UV_INSECURE=1
```

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Configuration Validation
```bash
python scripts/validate-config.py
```

## Deployment

### GitHub Actions
The repository includes automated deployment workflows:
- **Continuous Deployment**: Triggered on pushes to main
- **Scheduled Backups**: Weekly backup operations
- **Health Checks**: Automated server monitoring

### Manual Deployment
```bash
# Using GitHub secrets
python scripts/setup-secrets.py YOUR_USERNAME YOUR_REPO_NAME

# Validate configuration
python scripts/validate-config.py

# Start server
python src/main.py
```

## Security Considerations

- **Credentials**: Use GitHub secrets for production
- **Network Access**: Ensure proper firewall rules
- **API Tokens**: Rotate tokens regularly
- **Audit Logging**: Monitor access to network devices

## Troubleshooting

### SSL Certificate Issues
```bash
# For corporate environments
set UV_INSECURE=1
set PYTHONHTTPSVERIFY=0
```

### Connection Timeouts
- Check network connectivity to devices
- Verify credentials are correct
- Ensure firewall rules allow access

### MCP Server Not Starting
- Verify Python dependencies are installed
- Check configuration file syntax
- Review server logs for errors

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing GitHub issues
3. Create a new issue with detailed information

## Changelog

### v1.0.0
- Initial release
- FortiManager, FortiGate, and Meraki support
- GitHub secrets integration
- Claude Desktop MCP integration