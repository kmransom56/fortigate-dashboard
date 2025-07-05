# Fortinet MCP Server Deployment Guide

This guide explains how to use your enhanced Fortinet MCP server in different ways - as a standalone application, with Claude Desktop, with other applications, and globally across your development environment.

## 🎯 **What is an MCP Server?**

MCP (Model Context Protocol) servers provide AI models with real-time access to external systems, tools, and data. Your Fortinet MCP server acts as a bridge between AI assistants and your FortiGate/FortiSwitch infrastructure.

## 🚀 **Deployment Options**

### **1. Standalone Application Mode**

Run the server independently for testing, debugging, or direct API access:

```bash
# Navigate to the server directory
cd /home/keith/fortigate-dashboard/mcp_server/fortinet

# Run standalone
python fortinet_server_enhanced.py

# Or with specific configuration
FORTIGATE_HOST=192.168.0.254 FORTIGATE_API_TOKEN=your_token python fortinet_server_enhanced.py
```

**Use Cases:**
- API testing and development
- Direct Fortinet infrastructure monitoring
- Debugging and troubleshooting
- Batch operations and automation scripts

### **2. Claude Desktop Integration**

Integrate with Claude Desktop for AI-powered network management:

#### **Step 1: Configure Claude Desktop**

Edit your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Linux:** `~/.config/claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "fortinet": {
      "command": "python",
      "args": ["/home/keith/fortigate-dashboard/mcp_server/fortinet/fortinet_server_enhanced.py"],
      "env": {
        "FORTIGATE_HOST": "https://192.168.0.254",
        "FORTIGATE_API_TOKEN": "HbsysGgkc7wd1pp3xzQ095bb7jhzk8",
        "FORTIGATE_VDOM": "root"
      }
    }
  }
}
```

#### **Step 2: Restart Claude Desktop**

The server will now be available in Claude Desktop with access to all 246+ endpoints.

**Claude Desktop Benefits:**
- Natural language interface to your Fortinet infrastructure
- AI-powered network analysis and troubleshooting
- Automated report generation
- Interactive network management

### **3. Global Development Environment**

Make the server available globally across all your development projects:

#### **Option A: Install as Python Package**

```bash
# Create a setup.py for your MCP server
cd /home/keith/fortigate-dashboard/mcp_server/fortinet

# Install globally
pip install -e .

# Now available from anywhere
python -c "from fortinet_server_enhanced import fg_api; print(fg_api.test_connection())"
```

#### **Option B: Add to Python Path**

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
export PYTHONPATH="/home/keith/fortigate-dashboard/mcp_server/fortinet:$PYTHONPATH"
export FORTINET_MCP_PATH="/home/keith/fortigate-dashboard/mcp_server/fortinet"
```

#### **Option C: Create Global Alias**

```bash
# Add to ~/.bashrc or ~/.zshrc
alias fortinet-mcp="cd /home/keith/fortigate-dashboard/mcp_server/fortinet && python fortinet_server_enhanced.py"
alias fortinet-test="cd /home/keith/fortigate-dashboard/mcp_server/fortinet && python test_server.py"
```

### **4. Integration with Other Applications**

#### **Web Applications (FastAPI/Flask)**

```python
# Import the MCP server components
import sys
sys.path.append('/home/keith/fortigate-dashboard/mcp_server/fortinet')

from fortinet_server_enhanced import fg_api, api_parser, discovered_endpoints

from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/fortigate/status')
def get_status():
    result = fg_api._make_request("GET", "monitor/system/status")
    return jsonify(result)

@app.route('/api/switches/detected')
def get_detected_devices():
    result = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
    return jsonify(result)

@app.route('/api/discovery/endpoints')
def get_all_endpoints():
    return jsonify({
        "total_endpoints": len(discovered_endpoints),
        "categories": {cat: len(eps) for cat, eps in api_parser.categories.items()}
    })
```

#### **Jupyter Notebooks**

```python
# Cell 1: Import the MCP server
import sys
sys.path.append('/home/keith/fortigate-dashboard/mcp_server/fortinet')

from fortinet_server_enhanced import fg_api, api_parser, discovered_endpoints
import json

# Cell 2: Test connection
status = fg_api.test_connection()
print(f"Connection Status: {status}")

# Cell 3: Discover endpoints
print(f"Total Endpoints: {len(discovered_endpoints)}")
for category, endpoints in api_parser.categories.items():
    print(f"{category}: {len(endpoints)} endpoints")

# Cell 4: Get detected devices
devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
print(json.dumps(devices, indent=2))
```

#### **Automation Scripts**

```python
#!/usr/bin/env python3
"""
Daily network health check automation
"""
import sys
sys.path.append('/home/keith/fortigate-dashboard/mcp_server/fortinet')

from fortinet_server_enhanced import fg_api
import json
from datetime import datetime

def daily_health_check():
    report = {
        "timestamp": datetime.now().isoformat(),
        "system_status": fg_api._make_request("GET", "monitor/system/status"),
        "detected_devices": fg_api._make_request("GET", "monitor/switch-controller/detected-device"),
        "interface_stats": fg_api._make_request("GET", "monitor/system/interface")
    }
    
    # Save report
    with open(f"health_report_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(report, f, indent=2)
    
    return report

if __name__ == "__main__":
    report = daily_health_check()
    print(f"Health check completed: {len(report)} sections")
```

### **5. Docker Deployment**

Create a containerized version for consistent deployment:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the MCP server
COPY fortinet_server_enhanced.py .
COPY test_server.py .

# Set environment variables
ENV FORTIGATE_HOST=https://192.168.0.254
ENV FORTIGATE_API_TOKEN=""

# Expose port for standalone mode
EXPOSE 8080

# Run the server
CMD ["python", "fortinet_server_enhanced.py"]
```

```bash
# Build and run
docker build -t fortinet-mcp-server .
docker run -e FORTIGATE_API_TOKEN=your_token -p 8080:8080 fortinet-mcp-server
```

### **6. VS Code Integration**

#### **Option A: As Extension**

Create a VS Code extension that uses your MCP server:

```typescript
// extension.ts
import * as vscode from 'vscode';
import { exec } from 'child_process';

export function activate(context: vscode.ExtensionContext) {
    let disposable = vscode.commands.registerCommand('fortinet.getDevices', () => {
        exec('python /home/keith/fortigate-dashboard/mcp_server/fortinet/test_server.py', 
             (error, stdout, stderr) => {
            if (error) {
                vscode.window.showErrorMessage(`Error: ${error.message}`);
                return;
            }
            vscode.window.showInformationMessage(`Fortinet Status: ${stdout}`);
        });
    });

    context.subscriptions.push(disposable);
}
```

#### **Option B: Integrated Terminal**

Add tasks to `.vscode/tasks.json`:

```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Fortinet Health Check",
            "type": "shell",
            "command": "python",
            "args": ["/home/keith/fortigate-dashboard/mcp_server/fortinet/test_server.py"],
            "group": "build",
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            }
        },
        {
            "label": "Fortinet API Discovery",
            "type": "shell",
            "command": "python",
            "args": [
                "/home/keith/fortigate-dashboard/mcp_server/fortinet/fortinet_server_enhanced.py",
                "--discover"
            ],
            "group": "build"
        }
    ]
}
```

## 🔧 **Configuration Management**

### **Environment Variables**

Create a `.env` file for easy configuration:

```bash
# .env file
FORTIGATE_HOST=https://192.168.0.254
FORTIGATE_API_TOKEN=HbsysGgkc7wd1pp3xzQ095bb7jhzk8
FORTIGATE_USERNAME=admin
FORTIGATE_PASSWORD=your_password
FORTIGATE_VDOM=root

# FortiManager (optional)
FORTIMANAGER_HOST=https://192.168.0.100
FORTIMANAGER_API_TOKEN=your_fm_token
```

### **Configuration File**

Create a `config.yaml` for advanced settings:

```yaml
# config.yaml
fortigate:
  host: "https://192.168.0.254"
  api_token: "HbsysGgkc7wd1pp3xzQ095bb7jhzk8"
  vdom: "root"
  timeout: 30
  verify_ssl: false

discovery:
  api_docs_path: "../../fortiosapi"
  auto_refresh: true
  cache_duration: 3600

logging:
  level: "INFO"
  file: "fortinet_mcp.log"
  max_size: "10MB"
```

## 🧪 **Testing and Validation**

### **Quick Test**

```bash
# Test basic functionality
python -c "
import sys; sys.path.append('/home/keith/fortigate-dashboard/mcp_server/fortinet')
from fortinet_server_enhanced import fg_api
print('Connection:', fg_api.test_connection())
print('Endpoints discovered:', len(fg_api._make_request('GET', 'monitor/switch-controller/detected-device')))
"
```

### **Comprehensive Test**

```bash
# Run full test suite
cd /home/keith/fortigate-dashboard/mcp_server/fortinet
python test_server.py
```

## 📊 **Monitoring and Logging**

### **Enable Detailed Logging**

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fortinet_mcp.log'),
        logging.StreamHandler()
    ]
)
```

### **Health Monitoring**

Create a monitoring script:

```python
# monitor.py
import time
import json
from fortinet_server_enhanced import fg_api

def monitor_health():
    while True:
        try:
            status = fg_api.test_connection()
            devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
            
            health_data = {
                "timestamp": time.time(),
                "connection_status": status,
                "detected_devices": len(devices.get("results", [])),
                "status": "healthy" if status.get("status") == "success" else "unhealthy"
            }
            
            print(json.dumps(health_data))
            time.sleep(60)  # Check every minute
            
        except Exception as e:
            print(f"Monitor error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_health()
```

## 🔒 **Security Considerations**

1. **API Token Security**: Store tokens in environment variables or secure vaults
2. **Network Access**: Ensure proper firewall rules for FortiGate API access
3. **SSL Verification**: Enable SSL verification in production environments
4. **Access Control**: Implement proper authentication for your applications
5. **Logging**: Don't log sensitive data like API tokens

## 🚀 **Production Deployment**

### **Systemd Service (Linux)**

```ini
# /etc/systemd/system/fortinet-mcp.service
[Unit]
Description=Fortinet MCP Server
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/home/keith/fortigate-dashboard/mcp_server/fortinet
ExecStart=/usr/bin/python3 fortinet_server_enhanced.py
Restart=always
RestartSec=10
Environment=FORTIGATE_HOST=https://192.168.0.254
Environment=FORTIGATE_API_TOKEN=your_token

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable fortinet-mcp
sudo systemctl start fortinet-mcp
sudo systemctl status fortinet-mcp
```

## 📚 **Usage Examples**

### **Claude Desktop Conversation Examples**

```
You: "Check the status of my FortiGate and show me detected devices"
Claude: [Uses MCP server to get system status and detected devices]

You: "What switch-controller endpoints are available?"
Claude: [Uses discover_api_endpoints and get_endpoints_by_category tools]

You: "Run a health check on my network infrastructure"
Claude: [Uses run_health_check tool for comprehensive analysis]
```

### **Programmatic Usage**

```python
# Import and use directly
from fortinet_server_enhanced import fg_api, api_parser

# Get system status
status = fg_api._make_request("GET", "monitor/system/status")

# Discover all endpoints
endpoints = api_parser.discover_endpoints()

# Get switch-specific endpoints
switch_eps = api_parser.get_endpoints_by_category("switch_direct")

# Call any discovered endpoint dynamically
result = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
```

## 🎯 **Best Practices**

1. **Error Handling**: Always implement proper error handling
2. **Rate Limiting**: Respect API rate limits
3. **Caching**: Cache responses when appropriate
4. **Monitoring**: Monitor server health and performance
5. **Documentation**: Keep API usage documented
6. **Testing**: Regular testing of connectivity and functionality
7. **Updates**: Keep the server updated with latest API changes

Your enhanced Fortinet MCP server is now ready for deployment in any of these configurations, providing comprehensive network management capabilities across your entire development and production environment!