# 🚀 One-Click Docker Setup for Network Device Management

This directory contains everything your coworkers need to run the complete Network Device Management system with **just Docker Desktop**.

## 📋 Prerequisites

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and start Docker Desktop
   - Make sure it's running (you'll see the Docker icon in your system tray)

## 🎯 One-Click Start

### For Windows Users:
1. **Double-click** `ONE-CLICK-START.bat`
2. Wait for the build and startup process
3. Your browser will automatically open to http://localhost:12000

### For Mac/Linux Users:
```bash
# Make the script executable
chmod +x one-click-start.sh

# Run it
./one-click-start.sh
```

## 🌐 What You Get

After starting, you'll have access to:

| Service | URL | Description |
|---------|-----|-------------|
| **Web Dashboard** | http://localhost:12000 | Main dashboard for monitoring devices |
| **FastAPI Backend** | http://localhost:8000 | REST API for device management |
| **API Documentation** | http://localhost:8000/docs | Interactive API documentation |

## 🔧 Management Commands

### Windows:
- **Start**: `ONE-CLICK-START.bat`
- **Stop**: `STOP-DOCKER.bat`

### Command Line (All Platforms):
```bash
# Start everything
docker compose -f docker-compose.production.yml up -d

# Stop everything
docker compose -f docker-compose.production.yml down

# View logs
docker compose -f docker-compose.production.yml logs -f

# Check status
docker compose -f docker-compose.production.yml ps

# Restart a specific service
docker compose -f docker-compose.production.yml restart web-dashboard
```

## 📊 System Components

The Docker setup includes:

1. **FastAPI Server** (Port 8000)
   - Handles device management API
   - JWT authentication
   - Database management
   - FortiManager integration

2. **Web Dashboard** (Port 12000)
   - User-friendly interface
   - Real-time device monitoring
   - Brand-specific views
   - Health status displays

3. **Persistent Storage**
   - Database files preserved between restarts
   - Log files accessible for troubleshooting
   - Configuration files mounted read-only

## 🔍 Troubleshooting

### "Docker is not installed or not running"
- Install Docker Desktop from the official website
- Make sure Docker Desktop is started
- You should see the Docker whale icon in your system tray

### "Port already in use"
```bash
# Check what's using the ports
netstat -an | findstr "8000\|12000"

# Stop conflicting services or change ports in docker-compose.production.yml
```

### "Container won't start"
```bash
# Check container logs
docker compose -f docker-compose.production.yml logs

# Rebuild containers
docker compose -f docker-compose.production.yml up --build --force-recreate
```

### "Can't access the dashboard"
1. Wait 2-3 minutes for full startup
2. Check if containers are running: `docker compose -f docker-compose.production.yml ps`
3. Check container health: `docker compose -f docker-compose.production.yml logs web-dashboard`

## 💾 Data Persistence

Your data is automatically saved in Docker volumes:
- `fastapi_data`: Database and application data
- `fastapi_logs`: Application logs
- `mcp_data`: MCP server data
- `mcp_logs`: MCP server logs

Data persists even when you stop and restart containers.

## 🔧 Configuration

### Environment Variables
Edit `docker-compose.production.yml` to customize:
- Database settings
- API keys and secrets
- Port mappings
- Resource limits

### Adding FortiManager Credentials
1. Edit the `config/` directory files
2. Restart containers: `docker compose -f docker-compose.production.yml restart`

## 📈 Performance

### Resource Usage
- **FastAPI Server**: ~200MB RAM, minimal CPU
- **Web Dashboard**: ~100MB RAM, minimal CPU
- **Total**: ~300MB RAM, 1% CPU when idle

### Scaling
To handle more load:
```bash
# Scale the FastAPI service
docker compose -f docker-compose.production.yml up -d --scale fastapi-server=3
```

## 🚨 Security Notes

### For Production Use:
1. Change default passwords in `docker-compose.production.yml`
2. Use environment files for secrets (not hardcoded values)
3. Enable HTTPS with a reverse proxy
4. Restrict network access to necessary ports only

### Default Credentials:
- **FastAPI Admin**: admin / admin123
- **Change these immediately in production!**

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Look at container logs: `docker compose -f docker-compose.production.yml logs`
3. Restart everything: `STOP-DOCKER.bat` then `ONE-CLICK-START.bat`
4. Contact your system administrator with log output

## 🎉 Success!

When everything is working, you should see:
- ✅ Green status indicators in Docker Desktop
- 🌐 Dashboard accessible at http://localhost:12000
- 📊 Device counts and health status displayed
- 🔧 API responding at http://localhost:8000/docs

**Happy monitoring!** 🚀