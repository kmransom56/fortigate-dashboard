# 🌐 Network Device MCP Web Server

A comprehensive **Model Context Protocol (MCP) Server** with a professional web dashboard for managing multi-brand restaurant network infrastructure. Built for **Buffalo Wild Wings**, **Arby's**, and **Sonic Drive-In** locations with advanced network troubleshooting capabilities.

## 🚀 **No More Claude Desktop Message Limits!**

This web-based solution provides unlimited network investigations through a professional team-accessible interface.

![Dashboard Preview](https://img.shields.io/badge/Web_Dashboard-Professional-blue) ![Cross Platform](https://img.shields.io/badge/Cross_Platform-Windows%20%7C%20WSL%20%7C%20Linux-green) ![Multi Brand](https://img.shields.io/badge/Multi_Brand-BWW%20%7C%20Arbys%20%7C%20Sonic-orange)

---

## ✨ **Key Features**

### 🌐 **Professional Web Dashboard**
- **Team-accessible interface** - No technical knowledge required
- **Real-time monitoring** with live connection status
- **Multi-brand support** with dedicated pages for each restaurant chain
- **Responsive design** works on desktop, tablet, and mobile
- **Interactive investigation tools** with tabbed results

### 🔧 **Advanced Network Tools** *(from network_tools.txt)*
- **Policy Package Rules Analysis** - FortiManager compliance checking
- **Web Filter Profile Analysis** - Review and optimize filtering policies
- **Device Routing Table Diagnostics** - Analyze network connectivity paths  
- **Real-time Device Log Analysis** - Review traffic logs for security events
- **Network Connectivity Testing** - Ping tests and connection troubleshooting

### 🏪 **Multi-Brand Restaurant Support**
- **Buffalo Wild Wings (BWW)** - Device prefix: `IBR-BWW-XXXXX`
- **Arby's (ARBYS)** - Device prefix: `IBR-ARBYS-XXXXX` 
- **Sonic Drive-In (SONIC)** - Device prefix: `IBR-SONIC-XXXXX`

### 🐧 **Cross-Platform Compatibility**
- **Windows** - Native batch scripts and GUI tools
- **WSL (Windows Subsystem for Linux)** - Hybrid environment support
- **Linux** - Full bash script compatibility
- **Auto-detection** of platform and appropriate tool selection

---

## 🚀 **Quick Start**

### **Option 1: Web Dashboard (Recommended)**
```bash
# Start the web dashboard server
start-web-dashboard.bat        # Windows
# OR
python rest_api_server.py      # Cross-platform

# Access the dashboard
http://localhost:5000
```

### **Option 2: Run Complete Demo**
```bash
# Windows
run-complete-demo.bat

# WSL/Linux  
bash run-demo-cross-platform.sh
```

### **Option 3: Direct Advanced Tools Test**
```bash
python demo-advanced-tools-cross-platform.py
```

---

## 🛠️ **Installation**

### **Prerequisites**
- Python 3.10+
- FortiGate/FortiManager network devices
- Network access to your infrastructure

### **Setup Steps**

1. **Clone the repository**
   ```bash
   git clone https://github.com/kmransom56/network-device-mcp-web-server.git
   cd network-device-mcp-web-server
   ```

2. **Install dependencies**
   ```bash
   # Windows
   scripts/install.bat
   
   # Linux/WSL
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Copy and edit configuration
   cp .env.example .env
   # Edit .env with your FortiManager IPs and credentials
   ```

4. **Set up team access** *(Optional)*
   ```bash
   # Windows (run as Administrator)
   setup-firewall.bat
   ```

---

## 🌐 **Web Dashboard Features**

### **📊 Overview Dashboard**
- Network infrastructure statistics
- Security event summaries  
- Device health monitoring
- Brand-specific metrics

### **🔍 Store Investigation Tool**
- Select brand and store ID
- Choose analysis period (1h, 24h, 7d, 30d)
- Comprehensive security health scoring
- URL blocking pattern analysis
- Security event correlation

### **🏢 Brand Management**
- Dedicated pages for each restaurant chain
- FortiManager status monitoring
- Infrastructure health overview
- Quick action buttons

### **🛡️ FortiManager Integration**
- Multiple FortiManager instance support
- Device management and status
- Policy package deployment
- Configuration backup automation

---

## 🔧 **Advanced Network Tools**

### **Policy Analysis**
```bash
# Analyze FortiManager policy packages
GET /api/tools/policy-rules?fortimanager=BWW&package=Standard_Policy

# Review web filtering profiles  
GET /api/tools/webfilter-profile?device=IBR-BWW-00155&profile=Standard_Filter
```

### **Network Diagnostics** 
```bash
# Get device routing table
GET /api/tools/routing-table?device=IBR-BWW-00155&platform=fortigate

# Analyze device logs
GET /api/tools/device-logs?device=IBR-BWW-00155&type=traffic&period=1h

# Test connectivity
GET /api/tools/connectivity-test?device=IBR-BWW-00155&destination=8.8.8.8
```

### **Store Investigation**
```bash
# Complete store security analysis
GET /api/stores/bww/155/security?recommendations=true

# URL blocking analysis with export
GET /api/stores/bww/155/url-blocking?period=24h&export=true

# Security events summary
GET /api/devices/IBR-BWW-00155/security-events?timeframe=24h&top_count=20
```

---

## 🎯 **API Endpoints**

### **Core APIs**
- `GET /` - Web dashboard interface
- `GET /health` - Server health check
- `GET /api` - API documentation

### **Brand Management**
- `GET /api/brands` - List supported restaurant brands
- `GET /api/brands/{brand}/overview` - Brand-specific overview

### **FortiManager**
- `GET /api/fortimanager` - List FortiManager instances  
- `GET /api/fortimanager/{name}/devices` - Get managed devices

### **Store Investigation**
- `GET /api/stores/{brand}/{store_id}/security` - Security health analysis
- `GET /api/stores/{brand}/{store_id}/url-blocking` - URL blocking patterns

---

## 🔒 **Security Features**

- **Multi-layer authentication** support
- **HTTPS/TLS encryption** ready
- **Rate limiting** for API endpoints  
- **Input validation** and sanitization
- **Audit logging** for all operations
- **Role-based access control** framework

---

## 📋 **Team Setup Guide**

### **For Network Administrators**
1. Follow installation steps above
2. Configure `.env` with your network credentials
3. Run `test-network-setup.bat` to validate configuration
4. Start web dashboard with `start-web-dashboard.bat`

### **For Team Members**
1. Get the web dashboard URL from your admin: `http://[ADMIN-IP]:5000`
2. No installation required - just use your web browser
3. Refer to `TEAM-SETUP.md` for investigation procedures

### **For IT Support**
- Full cross-platform compatibility
- Comprehensive testing suite included
- Professional documentation for deployment
- Enterprise-ready with firewall configuration

---

## 🧪 **Testing & Validation**

### **Network Access Test**
```bash
test-network-setup.bat          # Windows
bash run-demo-cross-platform.sh # Linux/WSL (option 1)
```

### **Advanced Tools Demo**
```bash
demo-advanced-tools-cross-platform.py  # All platforms
```

### **Web Dashboard Test**
```bash
python test-web-dashboard.py --url http://localhost:5000
```

---

## 📚 **Documentation**

- **[DEPLOYMENT-SUMMARY.md](DEPLOYMENT-SUMMARY.md)** - Complete capabilities overview
- **[TEAM-SETUP.md](TEAM-SETUP.md)** - Team member setup guide  
- **[NETWORK-ACCESS-SETUP.md](NETWORK-ACCESS-SETUP.md)** - Network configuration
- **[CLAUDE.md](CLAUDE.md)** - Claude Desktop integration guide

---

## 🛠️ **Development**

### **Project Structure**
```
network-device-mcp-web-server/
├── src/                          # Core MCP server code
│   ├── main.py                   # MCP server with advanced tools
│   ├── config.py                 # Multi-brand configuration
│   └── platforms/                # Device platform handlers
├── web/                          # Web dashboard
│   ├── templates/index.html      # Main dashboard interface
│   ├── static/css/dashboard.css  # Professional styling
│   └── static/js/dashboard.js    # Interactive functionality
├── rest_api_server.py            # Web server and API endpoints
├── demo-advanced-tools-cross-platform.py  # Cross-platform demo
├── run-complete-demo.bat         # Windows demo suite
├── run-demo-cross-platform.sh   # Linux/WSL demo suite
└── docs/                         # Comprehensive documentation
```

### **Contributing**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Submit a pull request

---

## 🆘 **Support & Troubleshooting**

### **Common Issues**
- **Port 5000 in use**: Change port in `rest_api_server.py` 
- **Permission denied**: Run scripts as Administrator (Windows)
- **Connection timeouts**: Check firewall and network connectivity
- **Virtual environment issues**: Use cross-platform scripts

### **Getting Help**
- Check the comprehensive documentation in the `docs/` folder
- Run the testing suite to validate your setup
- Review the troubleshooting guides in each documentation file

---

## 🏆 **Enterprise Ready**

This solution is production-ready with:
- ✅ **Scalable architecture** for multiple restaurant chains
- ✅ **Professional web interface** for non-technical team members  
- ✅ **Cross-platform deployment** on Windows, WSL, and Linux
- ✅ **Comprehensive testing** and validation framework
- ✅ **Enterprise documentation** for IT departments
- ✅ **Advanced security** features and audit capabilities

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 **Acknowledgments**

- Built with **Claude Code** for enhanced development workflow
- **FortiGate/FortiManager** API integration for network management
- **Cisco Meraki** support for comprehensive device coverage
- **Multi-brand restaurant** architecture for scalable deployment

---

*Transform your network troubleshooting from limited Claude Desktop sessions to unlimited team-accessible web-based investigations! 🚀*