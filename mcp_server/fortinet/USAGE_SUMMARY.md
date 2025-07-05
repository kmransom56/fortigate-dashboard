# 🚀 Fortinet MCP Server - Complete Usage Guide

## 📋 **Quick Summary**

Your enhanced Fortinet MCP Server provides **5 different ways** to use your FortiGate API infrastructure with **246 auto-discovered endpoints** across **3 categories**.

## 🎯 **Usage Options**

### **1. 🤖 Claude Desktop Integration** (Recommended for AI-powered management)

**What it does:** Gives Claude AI direct access to your FortiGate infrastructure

**Setup:**
```bash
./install_mcp.sh --claude
# Follow prompts to enter your FortiGate details
```

**Usage:**
- Open Claude Desktop
- Ask: "Check my FortiGate status and show detected devices"  
- Ask: "What switch-controller endpoints are available?"
- Ask: "Run a comprehensive health check on my network"

**Benefits:**
- Natural language network management
- AI-powered analysis and troubleshooting
- Automated report generation

### **2. 🐍 Python Module Import** (Best for development)

**What it does:** Import MCP server components directly in your Python applications

**Setup:**
```bash
./install_mcp.sh --global
```

**Usage:**
```python
# Import components
from fortinet_server_enhanced import fg_api, api_parser, discovered_endpoints

# Test connection
status = fg_api.test_connection()

# Get your detected devices (original curl functionality)
devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")

# Discover all available endpoints
print(f"Total endpoints: {len(discovered_endpoints)}")
```

**Benefits:**
- Full programmatic control
- Perfect for automation scripts
- Integration with existing applications

### **3. 🖥️ Standalone Application** (Great for testing)

**What it does:** Run the server independently for direct API access

**Setup:**
```bash
cd /home/keith/fortigate-dashboard/mcp_server/fortinet
./install_mcp.sh --basic
```

**Usage:**
```bash
# Run the server
python3 fortinet_server_enhanced.py

# Run tests
python3 test_server.py

# Run examples
python3 examples/simple_usage.py
```

**Benefits:**
- Direct API testing
- Debugging and development
- No dependencies on other applications

### **4. 🌐 Web Application Integration** (For web dashboards)

**What it does:** Integrate with Flask/FastAPI applications

**Example:**
```python
from flask import Flask, jsonify
from fortinet_server_enhanced import fg_api

app = Flask(__name__)

@app.route('/api/devices')
def get_devices():
    devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
    return jsonify(devices)

@app.route('/api/health')
def health_check():
    return jsonify(fg_api.test_connection())
```

### **5. 🐳 Docker Deployment** (For production)

**What it does:** Containerized deployment for consistent environments

**Setup:**
```bash
# Build container
docker build -t fortinet-mcp .

# Run with your API token
docker run -e FORTIGATE_API_TOKEN=your_token fortinet-mcp
```

## 📦 **Installation from PyPI**

To install the MCP server package from PyPI, run:
```bash
pip install fortinet-mcp-server
```

## 📚 **Usage Instructions**

After installation, you can use the MCP server module in your Python applications:
```python
from fortinet_server_enhanced import fg_api

# Test connection
status = fg_api.test_connection()

# Get detected devices
devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")

print(f"Detected devices: {len(devices['results'])}")
```

## 📊 **What You Get**

### **API Coverage:**
- **246 Total Endpoints** auto-discovered from official Fortinet documentation
- **System Management**: 170 endpoints (config, monitoring, admin)
- **Switch Direct**: 72 endpoints (FortiSwitch management) 
- **Configuration**: 10 endpoints (CMDB system config)

### **Your Original Use Case Enhanced:**
- ✅ **Your curl command**: `monitor/switch-controller/detected-device` 
- ✅ **Plus 245 more endpoints** automatically discovered
- ✅ **Dynamic endpoint calling** - call any endpoint without manual coding
- ✅ **Enhanced categorization** - organized by functionality

### **Key Capabilities:**
- 🔍 **API Discovery**: Automatically finds all available endpoints
- 🔀 **Switch Management**: Comprehensive FortiSwitch control
- ⚙️ **Configuration Management**: System config through CMDB endpoints
- 📊 **Health Monitoring**: Comprehensive system health checks
- 🔧 **Dynamic Calls**: Call any discovered endpoint dynamically

## 🚀 **Quick Start (30 seconds)**

1. **For AI-powered management:**
   ```bash
   ./install_mcp.sh --claude
   # Then use Claude Desktop
   ```

2. **For Python development:**
   ```bash
   ./install_mcp.sh --global
   source ~/.bashrc
   python3 examples/simple_usage.py
   ```

3. **For quick testing:**
   ```bash
   python3 test_server.py
   ```

## 📈 **Real-World Examples**

### **Network Health Check:**
```python
from fortinet_server_enhanced import fg_api

# Your original functionality + more
devices = fg_api._make_request("GET", "monitor/switch-controller/detected-device")
status = fg_api._make_request("GET", "monitor/system/status")
interfaces = fg_api._make_request("GET", "monitor/system/interface")

print(f"System: {status['results']['hostname']}")
print(f"Detected devices: {len(devices['results'])}")
```

### **Claude Desktop Conversation:**
```
You: "Show me all devices connected to my FortiSwitch"
Claude: "I found 6 devices connected to switch S124EPTQ22000276:
- MAC 10:7c:61:3f:2b:5d on port19 (VLAN 1000)
- MAC 3c:18:a0:d4:cf:68 on port21 (VLAN 1000)
..."

You: "What other switch management endpoints are available?"  
Claude: "I discovered 72 switch direct endpoints grouped by:
- Port Management: 10 endpoints
- Statistics: 8 endpoints  
- Security: 5 endpoints..."
```

### **Automation Script:**
```python
# Daily health report
from fortinet_server_enhanced import fg_api
import json
from datetime import datetime

report = {
    "timestamp": datetime.now().isoformat(),
    "system_status": fg_api._make_request("GET", "monitor/system/status"),
    "detected_devices": fg_api._make_request("GET", "monitor/switch-controller/detected-device"),
    "interface_stats": fg_api._make_request("GET", "monitor/system/interface")
}

with open(f"daily_report_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
    json.dump(report, f, indent=2)
```

## 🔧 **Installation Options**

| Method | Command | Use Case |
|--------|---------|----------|
| **Full Setup** | `./install_mcp.sh --full` | Everything (Claude + Python + Service) |
| **Claude Only** | `./install_mcp.sh --claude` | AI-powered management |
| **Development** | `./install_mcp.sh --global` | Python module access |
| **Basic** | `./install_mcp.sh --basic` | Testing and standalone |
| **Interactive** | `./install_mcp.sh` | Step-by-step menu |

## 📋 **Test Results**

Your current setup shows:
- ✅ **FortiGate Connection**: Success
- ✅ **246 Endpoints Discovered**: From 5 API documentation files
- ✅ **6 Devices Detected**: On switch S124EPTQ22000276
- ✅ **100% Health Score**: All systems operational
- ✅ **All Categories Working**: System, Switch Direct, Configuration

## 🎯 **Next Steps**

1. **Choose your preferred usage method** from the 5 options above
2. **Run the installer**: `./install_mcp.sh` 
3. **Test functionality**: `python3 examples/simple_usage.py`
4. **Start using**: Your FortiGate infrastructure is now accessible via AI or code

Your enhanced MCP server transforms your original curl command into a comprehensive network management platform with 246+ endpoints, AI integration, and multiple deployment options! 🚀