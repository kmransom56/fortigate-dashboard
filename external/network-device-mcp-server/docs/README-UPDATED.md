# Voice-Enabled Network Management Platform

A professional NOC-style Voice-Enabled Network Management Platform for restaurant chain infrastructure with AI-powered analytics, LTM Intelligence System, and hands-free operation capabilities.

![Platform Overview](docs/images/noc-dashboard-overview.png)
*Professional NOC interface with sidebar navigation and real-time statistics*

## 🚀 Features

### 🎤 Voice-Controlled Operations
- **Hands-free navigation** - "Show Buffalo Wild Wings", "Investigate store 155"
- **Voice feedback** - Audio announcements for system status and results
- **Accessibility support** - Screen reader compatible with WCAG 2.1 AA compliance

![Voice Interface](docs/images/voice-controls.png)
*Voice control interface with microphone controls and status indicators*

### 🧠 LTM Intelligence System
- **Pattern Recognition Engine** - 8 threat pattern types with real-time detection
- **Predictive Analytics** - 6 prediction models for proactive maintenance
- **Network Graph Intelligence** - Attack path analysis and impact modeling
- **Voice Learning Engine** - Adaptive NLP for improved voice interaction

### 🏪 Multi-Brand Restaurant Support
- **Buffalo Wild Wings** - Complete network infrastructure management
- **Arby's** - Security monitoring and device health tracking  
- **Sonic Drive-In** - Performance analytics and compliance reporting
- **Unified Dashboard** - Single interface for all restaurant brands

![Brand Dashboard](docs/images/brand-overview.png)
*Brand-specific network overview with infrastructure status and security metrics*

### 🔧 Network Management Tools
- **FortiManager Integration** - Device provisioning and policy management
- **FortiAnalyzer Support** - Log analysis and threat intelligence
- **Web Filters Management** - Content filtering and SSL inspection
- **Store Investigation** - Deep-dive analysis for specific locations

![Store Investigation](docs/images/store-investigation.png)
*Comprehensive store investigation interface with security health analysis*

## 📱 Interface Screenshots

### NOC-Style Dashboard
![NOC Dashboard](docs/images/noc-full-interface.png)
*Complete NOC interface showing sidebar navigation, main dashboard, and status displays*

### Mobile Responsive Design
<div style="display: flex; gap: 20px;">

![Mobile View 1](docs/images/mobile-dashboard.png)
![Mobile View 2](docs/images/mobile-navigation.png)

</div>

*Responsive design optimized for mobile devices and tablets*

### Dark Theme Professional Interface
![Dark Theme](docs/images/dark-theme-details.png)
*Professional dark theme optimized for 24/7 NOC operations*

## 🛠️ Installation & Setup

### Prerequisites
- **Python 3.8+** with required packages
- **Node.js 16+** (optional, for enhanced features)
- **Network access** to restaurant infrastructure
- **Modern browser** with Web Speech API support

### Quick Start
```bash
# Clone the repository
git clone https://github.com/your-org/network-device-mcp-server.git
cd network-device-mcp-server

# Install Python dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your FortiManager credentials

# Start the platform
python rest_api_server.py
```

### Access the Platform
- **Main Interface**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **API Documentation**: http://localhost:5000/api

## 🎯 Usage Guide

### Voice Commands
Enable voice control and use natural language commands:

```
"Show Buffalo Wild Wings"
"Investigate BWW store 155" 
"Show security dashboard"
"Generate security report"
"Check system status"
```

![Voice Commands Demo](docs/images/voice-commands-demo.png)
*Voice command interface with real-time speech recognition*

### Store Investigation Workflow
1. **Select Brand** - Choose BWW, Arby's, or Sonic
2. **Enter Store ID** - Specify location number
3. **Choose Timeframe** - Select analysis period
4. **Run Investigation** - Get comprehensive security analysis

![Investigation Results](docs/images/investigation-results.png)
*Sample investigation results showing security events, URL blocking, and recommendations*

### Brand Management
Each brand has dedicated views with:
- **Infrastructure Status** - Device health and connectivity
- **Security Overview** - Recent events and policy status
- **Quick Actions** - Investigation tools and FortiManager access

![Brand Management](docs/images/brand-management-tools.png)
*Brand-specific management tools and quick action buttons*

## 🔧 Configuration

### Environment Variables
```bash
# FortiManager Configuration
FM_BWW_HOST=10.128.145.4
FM_BWW_USERNAME=your_username
FM_BWW_PASSWORD=your_password

FM_ARBYS_HOST=10.128.144.132
FM_ARBYS_USERNAME=your_username
FM_ARBYS_PASSWORD=your_password

FM_SONIC_HOST=10.128.156.36
FM_SONIC_USERNAME=your_username
FM_SONIC_PASSWORD=your_password
```

### Voice Settings
- **Speech Rate**: Adjustable 0.5x to 2.0x speed
- **Volume**: Configurable audio levels
- **Voice Selection**: Choose from available system voices
- **Accessibility**: Screen reader and continuous listening modes

## 📊 API Reference

### Core Endpoints
```bash
GET /api/brands                           # List supported brands
GET /api/brands/{brand}/overview           # Brand infrastructure overview
GET /api/stores/{brand}/{id}/security      # Store security analysis
GET /api/ltm/status                        # LTM Intelligence status
POST /api/ltm/voice/command                # Process voice commands
```

### Response Format
```json
{
  "success": true,
  "data": {
    "brand_summary": {
      "brand": "Buffalo Wild Wings",
      "device_prefix": "IBR-BWW",
      "total_stores": 347
    },
    "infrastructure_status": {
      "fortimanager_host": "10.128.145.4",
      "total_managed_devices": 342,
      "online_devices": 338,
      "offline_devices": 4
    }
  }
}
```

## 🧪 Testing & Development

### Run Tests
```bash
# Test core functionality
python -m pytest tests/

# Test API endpoints  
python -c "
import requests
response = requests.get('http://localhost:5000/health')
print(f'Health Check: {response.status_code}')
"

# Test voice integration
# Navigate to http://localhost:5000 and enable voice controls
```

### Development Mode
```bash
# Start with auto-reload
python rest_api_server.py --debug

# Monitor logs
tail -f application.log
```

## 📈 Performance & Monitoring

### System Requirements
- **RAM**: 2GB minimum, 4GB recommended
- **CPU**: 2 cores minimum for voice processing
- **Storage**: 1GB for logs and temporary files
- **Network**: Stable connection to FortiManager instances

### Monitoring Features
- **Real-time status displays** with connection health
- **Performance metrics** for voice processing
- **Error logging** with detailed troubleshooting info
- **Usage analytics** for voice command patterns

![System Monitoring](docs/images/system-monitoring.png)
*Real-time system monitoring and performance metrics*

## 🔐 Security & Compliance

### Security Features
- **Encrypted communications** with FortiManager
- **Credential management** via environment variables
- **Session management** with timeout controls
- **Audit logging** for all administrative actions

### Compliance
- **WCAG 2.1 AA** accessibility standards
- **Enterprise security** best practices
- **Data protection** with local processing
- **No external dependencies** for sensitive operations

## 🚀 Deployment

### Production Deployment
```bash
# Use process manager
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 rest_api_server:app

# Or use systemd service
sudo cp deploy/network-management.service /etc/systemd/system/
sudo systemctl enable network-management
sudo systemctl start network-management
```

### Docker Deployment
```dockerfile
FROM python:3.9-alpine
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "rest_api_server.py"]
```

## 📄 License

This project is licensed under the ISC License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **Issues**: GitHub Issues page
- **Documentation**: README and code comments
- **Email**: network-team@yourcompany.com

---

**🌐 The world's first voice-enabled AI-powered restaurant network management platform!**

![Footer Banner](docs/images/platform-banner.png)
*Professional network operations center for the modern restaurant industry*