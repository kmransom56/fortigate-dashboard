# NOC-Style Voice-Enabled Network Management Platform

A modern Network Operations Center (NOC) interface for managing restaurant chain network infrastructure with voice control and AI-powered analytics.

## 🎯 Features

### NOC-Style Interface
- **Dark theme** optimized for 24/7 operations
- **Sidebar navigation** with organized tool sections  
- **Real-time status displays** with color-coded indicators
- **Professional layout** inspired by enterprise NOC environments

### Voice Control Integration
- **Hands-free operation** for busy network engineers
- **Voice commands** for navigation and investigation
- **Audio feedback** for status updates and alerts
- **Accessibility features** for improved usability

### AI-Powered Analytics
- **LTM Intelligence System** with 5 core engines
- **Pattern recognition** for security threats
- **Predictive analytics** for proactive maintenance
- **Network graph analysis** for topology insights

### Multi-Brand Restaurant Support
- **Buffalo Wild Wings** network management
- **Arby's** infrastructure monitoring  
- **Sonic Drive-In** security analysis
- **Unified dashboard** for all brands

## 🚀 Quick Start

### Prerequisites
- **Node.js** 16+ and **npm** 8+
- **Python** 3.8+ with required packages
- **Network access** to restaurant infrastructure

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/network-device-mcp-server.git
   cd network-device-mcp-server
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your FortiManager credentials
   ```

### Running the Platform

#### Option 1: Automatic Startup (Recommended)
```bash
# Windows
start-noc-platform.bat

# Linux/Mac
./start-noc-platform.sh
```

#### Option 2: Manual Startup
```bash
# Terminal 1 - Python Backend
python rest_api_server.py

# Terminal 2 - Node.js Frontend  
node server_noc_style.js
```

#### Option 3: Development Mode
```bash
# Run both servers with auto-restart
npm run both
```

### Access the Platform
- **NOC Dashboard:** http://localhost:5001
- **Original Dashboard:** http://localhost:5000
- **Health Check:** http://localhost:5001/health

## 🎮 Using the Interface

### Navigation
- **Sidebar menu** for section navigation
- **Brand-specific views** for BWW, Arby's, Sonic
- **Investigation tools** for store analysis
- **Management consoles** for FortiManager/FortiAnalyzer

### Voice Commands
1. **Enable voice control** using the microphone button
2. **Say commands** like:
   - "Show Buffalo Wild Wings"
   - "Investigate BWW store 155"
   - "Show security dashboard"
   - "Generate report"

### Dashboard Features
- **Real-time statistics** (stores, events, security)
- **Network topology** visualization (coming soon)
- **Status indicators** with color coding
- **Export capabilities** for reports

## 📊 API Endpoints

### Core Endpoints
- `GET /health` - System health check
- `GET /api/noc/dashboard` - NOC dashboard status
- `GET /api/brands` - Supported restaurant brands
- `GET /api/ltm/status` - LTM Intelligence status

### Brand Management
- `GET /api/brands/:brand/overview` - Brand infrastructure
- `GET /api/stores/:brand/:id/security` - Store security health
- `GET /api/devices/:device/security-events` - Device events

### File Operations
- `POST /api/upload` - Upload topology/config files
- `POST /api/generate-report` - Generate network reports

## 🛠️ Configuration

### Environment Variables
```bash
# Server Configuration
PORT=5001
PYTHON_SERVER_URL=http://localhost:5000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5001

# FortiManager Settings (configure in .env)
FM_BWW_HOST=10.128.145.4
FM_BWW_USERNAME=your_username
FM_BWW_PASSWORD=your_password
```

### Security Features
- **Helmet.js** for security headers
- **Rate limiting** on API endpoints
- **File upload validation**
- **CORS protection**
- **Input sanitization**

## 🎨 Customization

### Styling
The interface uses a professional NOC color scheme:
- **Background:** Dark gray (#1a1a1a)
- **Panels:** Medium gray (#2d2d2d)  
- **Accent:** Green (#4caf50)
- **Text:** Light gray/white

### Adding New Brands
1. **Add navigation item** in `index_noc_style.html`
2. **Create brand section** with unique ID
3. **Update JavaScript** navigation function
4. **Add API endpoints** in server files

### Voice Commands
Extend voice commands in `voice-commands.js`:
```javascript
// Add new command patterns
this.addCommandPattern(/your pattern/, this.yourHandler);
```

## 📱 Mobile Support

The interface includes responsive design for mobile devices:
- **Collapsible sidebar** on small screens
- **Touch-friendly controls**
- **Optimized layouts** for tablets

## 🔧 Troubleshooting

### Common Issues

**Port conflicts:**
- Change `PORT` in `.env` file
- Update startup scripts accordingly

**Python server not responding:**
- Check Flask server is running on port 5000
- Verify API proxy configuration

**Voice features not working:**
- Enable microphone permissions
- Use Chrome/Edge browser for best compatibility
- Check Web Speech API support

### Logs and Debugging
- **Node.js logs:** Console output from server
- **Python logs:** Flask development server output
- **Browser logs:** Developer Console (F12)

## 🚀 Deployment

### Production Deployment
1. **Use process managers:**
   ```bash
   # PM2 for Node.js
   pm2 start server_noc_style.js --name noc-frontend
   
   # Gunicorn for Python
   gunicorn -w 4 -b 0.0.0.0:5000 rest_api_server:app
   ```

2. **Configure reverse proxy** (Nginx/Apache)
3. **Set up SSL certificates**
4. **Configure monitoring** and alerting

### Docker Deployment
```dockerfile
# Multi-stage build for production
FROM node:18-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm install --production

FROM python:3.9-alpine AS backend  
WORKDIR /app
COPY requirements.txt ./
RUN pip install -r requirements.txt
```

## 📄 License

This project is licensed under the ISC License. See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

For support and questions:
- **Issues:** GitHub Issues page
- **Documentation:** README files
- **Email:** network-team@yourcompany.com

---

**🌐 Experience the future of network operations with voice-controlled, AI-powered restaurant network management!**