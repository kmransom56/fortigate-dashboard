# 🐳 Network Device MCP Server - Docker Deployment Guide

## 🚀 Quick Start for Your Team

### Prerequisites
- **Docker Desktop** installed (free from [docker.com](https://www.docker.com/products/docker-desktop/))
- **Network access** to your FortiManager systems

### One-Command Setup
```powershell
# Run this once to set up everything (use .\ in PowerShell):
.\setup-auto-start.bat
```

That's it! Your team can now use the Network Device MCP Server with Docker Desktop.

---

## 📋 Detailed Setup Instructions

### Step 1: Install Docker Desktop
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install and start Docker Desktop
3. Verify: Run `docker --version` in terminal

### Step 2: Configure Environment
The setup script will automatically:
- ✅ Create `.env` file from template
- ✅ Open `.env` for you to edit
- ✅ Build the Docker image
- ✅ Test the container
- ✅ Create desktop shortcut

**Edit the `.env` file with your credentials:**
```env
FMG_IP=10.128.145.4
FMG_USERNAME=your_username
FMG_PASSWORD=your_password
ADOM_NAME=root
```

### Step 3: Start the Application
```bash
# Option 1: Use the desktop shortcut (created automatically)
# Double-click: "Network Device MCP Server" on your desktop

# Option 2: Command line
.\start-server.bat

# Option 3: Docker commands
docker-compose up -d
```

### Step 4: Access the Application
- 🌐 **Web Interface:** http://localhost:12000
- 📊 **API Documentation:** http://localhost:12000/api
- 🏥 **Health Check:** http://localhost:12000/health

---

## 🔧 Docker Auto-Start Configuration

### Windows Auto-Start Setup
The setup script creates everything needed for auto-start:

1. **Desktop Shortcut** - Double-click to start/stop
2. **Start Script** - `start-server.bat` for command line
3. **Docker Compose** - Auto-restart with `restart: always`

### Manual Auto-Start (Optional)
If you want the container to start automatically when Docker Desktop starts:

```bash
# Start and keep running
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## 🛠️ Docker Commands Reference

### Basic Operations
```bash
# Start the server
docker-compose up -d

# Stop the server
docker-compose down

# View logs
docker-compose logs -f

# Check status
docker-compose ps

# Restart
docker-compose restart
```

### Development
```bash
# Rebuild after code changes
docker-compose build

# Build and start
docker-compose up -d --build

# Run tests in container
docker-compose run --rm network-mcp-server python -m pytest tests/ -v
```

### Troubleshooting
```bash
# Check container health
curl http://localhost:12000/health

# View detailed logs
docker-compose logs

# Check container resources
docker stats

# Debug container
docker-compose exec network-mcp-server bash
```

---

## 📁 File Structure

```
network-device-mcp-server/
├── 🐳 Dockerfile                 # Container configuration
├── 🐳 docker-compose.yml         # Docker services
├── 🐳 .dockerignore             # Build exclusions
├── ⚙️ .env.docker               # Environment template
├── ⚙️ .env                      # Your configuration (create from template)
├── 🚀 start-server.bat          # Start/stop script
├── 🔧 setup-auto-start.bat      # One-time setup script
├── 📁 src/                      # Application source code
├── 📁 web/                      # Web interface files
├── 📁 tests/                    # Test suite
└── 📁 logs/                     # Application logs (auto-created)
```

---

## 🔒 Security Considerations

### Environment Variables
- ✅ **Never commit** `.env` file to git
- ✅ **Use strong passwords** for FortiManager access
- ✅ **Limit network access** to trusted networks only
- ✅ **Regular credential rotation** recommended

### Docker Security
- ✅ **Non-root container** user
- ✅ **Minimal base image** (Python slim)
- ✅ **Resource limits** configured
- ✅ **Health checks** implemented

---

## 🚨 Troubleshooting

### Common Issues

**❌ Docker Desktop not running**
```bash
# Check if Docker is running
docker info

# Start Docker Desktop manually
# Or reboot your system
```

**❌ Container fails to start**
```bash
# Check logs for errors
docker-compose logs

# Verify .env file exists and has correct values
notepad .env

# Test health endpoint
curl http://localhost:12000/health
```

**❌ Cannot connect to FortiManager**
```bash
# Check FortiManager credentials in .env
# Verify network connectivity
ping your-fortimanager-ip

# Check FortiManager API access
curl https://your-fortimanager-ip/jsonrpc
```

**❌ Port 12000 already in use**
```bash
# Check what's using port 12000
netstat -ano | findstr :12000

# Change port in docker-compose.yml
# Update: ports: - "12001:12000"
```

### Getting Help
1. 📊 Check logs: `docker-compose logs`
2. 🔍 Check status: `docker-compose ps`
3. 🏥 Test health: `curl http://localhost:12000/health`
4. 📝 Review configuration: `notepad .env`

---

## 📞 Support for Your Team

### What Your Team Needs to Know:
1. **Install Docker Desktop** (IT can help with this)
2. **Run setup script once** (creates all necessary files)
3. **Edit .env file** with FortiManager credentials
4. **Double-click desktop shortcut** to start
5. **Access at http://localhost:12000**

### IT/Admin Support:
- **Network**: Ensure access to FortiManager IPs on required ports
- **Security**: Review firewall rules for Docker containers
- **Permissions**: Ensure users can run Docker containers
- **Resources**: Allocate sufficient memory to Docker Desktop

---

## 🔄 Updates and Maintenance

### Updating the Application:
```bash
# Pull latest changes
git pull origin main

# Rebuild container
docker-compose build

# Restart with updates
docker-compose up -d
```

### Backup and Recovery:
```bash
# Backup logs and configuration
tar -czf backup-$(date +%Y%m%d).tar.gz logs/ .env

# Restore from backup
tar -xzf backup-20240101.tar.gz
```

---

## 🎯 Enterprise Features

- ✅ **Auto-Restart** - Container restarts automatically
- ✅ **Health Monitoring** - Built-in health checks
- ✅ **Resource Limits** - Memory and CPU constraints
- ✅ **Log Persistence** - Logs saved to host system
- ✅ **Security Hardening** - Non-root user, minimal image
- ✅ **Network Isolation** - Dedicated Docker network
- ✅ **Configuration Management** - Environment-based config
- ✅ **Monitoring Ready** - Structured logging and metrics

---

## 📞 Need Help?

### For Your Network Team:
1. **Docker Desktop Issues**: Check Docker Desktop settings
2. **Network Connectivity**: Verify FortiManager access
3. **Credentials**: Validate FortiManager API access
4. **Performance**: Monitor with `docker stats`

### Quick Health Check:
```bash
# Test all components
curl http://localhost:12000/health
curl http://localhost:12000/api/brands
curl http://localhost:12000/api/fortimanager
```

Your Network Device MCP Server is now **enterprise-ready** with Docker Desktop deployment! 🚀
