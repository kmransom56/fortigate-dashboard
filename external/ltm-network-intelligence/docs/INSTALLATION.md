# 📦 Installation Guide

This guide will help you install and set up the LTM Network Intelligence Platform. Choose the method that best fits your environment.

## 🎯 Choose Your Installation Method

| Method | Best For | Time | Difficulty |
|--------|----------|------|------------|
| **[Quick Setup](#quick-setup-recommended)** | First-time users, testing | 5 minutes | ⭐ Easy |
| **[Docker](#docker-installation)** | Production, isolated environments | 3 minutes | ⭐ Easy |
| **[Native Python](#native-python-installation)** | Development, customization | 10 minutes | ⭐⭐ Medium |
| **[Repository Integration](#repository-integration)** | Existing kmransom56 repos | 15 minutes | ⭐⭐ Medium |

---

## 🚀 Quick Setup (Recommended)

Perfect for getting started quickly. The script automatically detects your system and chooses the best installation method.

### Prerequisites
- **Operating System**: Linux (Ubuntu 18.04+, CentOS 7+) or macOS 10.15+
- **Memory**: 4GB RAM minimum (8GB+ recommended)
- **Storage**: 10GB free space
- **Network**: Internet connection for downloading components

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/kmransom56/ltm-network-intelligence-platform.git
cd ltm-network-intelligence-platform

# 2. Make setup script executable and run
chmod +x scripts/quick_setup.sh
./scripts/quick_setup.sh
```

### What the Quick Setup Does
1. **System Detection**: Checks your OS and available software
2. **Dependency Installation**: Installs Python, Docker, or other needed tools
3. **Platform Setup**: Configures the LTM platform automatically
4. **Service Startup**: Starts all required services
5. **Health Check**: Verifies everything is working

### After Installation
- **Platform Dashboard**: http://localhost:8002
- **API Documentation**: http://localhost:8002/api/docs
- **Grafana Monitoring**: http://localhost:3000
- **Health Check**: `python unified_network_intelligence.py --health-check`

---

## 🐳 Docker Installation

Ideal for production deployments and isolated environments.

### Prerequisites
- **Docker**: 20.10+ ([Install Docker](https://docs.docker.com/get-docker/))
- **Docker Compose**: 1.29+ ([Install Docker Compose](https://docs.docker.com/compose/install/))
- **Memory**: 4GB RAM minimum
- **Storage**: 10GB free space

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/kmransom56/ltm-network-intelligence-platform.git
cd ltm-network-intelligence-platform

# 2. Start services with Docker Compose
docker-compose up -d

# 3. Check service status
docker-compose ps

# 4. View logs (optional)
docker-compose logs -f
```

### Docker Services Started
- **LTM Platform**: Main intelligence platform
- **Neo4j**: Knowledge graph database
- **Milvus**: Vector database for AI embeddings
- **Redis**: Caching and session management
- **PostgreSQL**: Audit logging and compliance
- **Grafana**: Monitoring dashboards
- **Prometheus**: Metrics collection

### Docker Management Commands
```bash
# Stop all services
docker-compose down

# Update services
docker-compose pull
docker-compose up -d

# View service logs
docker-compose logs [service-name]

# Access service shell
docker-compose exec ltm-platform bash
```

---

## 🐍 Native Python Installation

Best for development and when you need full control over the installation.

### Prerequisites
- **Python**: 3.8+ ([Download Python](https://www.python.org/downloads/))
- **pip**: Latest version (`python -m pip install --upgrade pip`)
- **Git**: For cloning repositories
- **System packages**: Build tools for some Python packages

### System Package Installation

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv build-essential libpq-dev
```

**CentOS/RHEL:**
```bash
sudo yum update
sudo yum install python3 python3-pip gcc gcc-c++ make postgresql-devel
```

**macOS:**
```bash
# Install Homebrew if not already installed
/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"

# Install Python and dependencies
brew install python@3.9 postgresql
```

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/kmransom56/ltm-network-intelligence-platform.git
cd ltm-network-intelligence-platform

# 2. Create and activate virtual environment
python3 -m venv ltm-venv
source ltm-venv/bin/activate  # On Windows: ltm-venv\\Scripts\\activate

# 3. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 4. Initialize the platform
python unified_network_intelligence.py --initialize

# 5. Start the platform
python unified_network_intelligence.py
```

### External Services Setup (Native Installation)

For native installation, you'll need to set up the external services manually:

#### Neo4j (Knowledge Graph Database)
```bash
# Download and install Neo4j Community Edition
# Ubuntu/Debian
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable 4.4' | sudo tee -a /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j

# Start Neo4j
sudo systemctl start neo4j
sudo systemctl enable neo4j

# Access: http://localhost:7474 (neo4j/neo4j -> change password)
```

#### Milvus (Vector Database)
```bash
# Download Milvus standalone
wget https://raw.githubusercontent.com/milvus-io/milvus/v2.2.0/scripts/standalone_embed.sh
bash standalone_embed.sh start

# Or using Docker
docker run -d --name milvus-standalone \\
  -p 19530:19530 -p 9091:9091 \\
  -v $(pwd)/volumes/milvus:/var/lib/milvus \\
  milvusdb/milvus:v2.2.0 milvus run standalone
```

#### Redis (Caching)
```bash
# Ubuntu/Debian
sudo apt install redis-server

# CentOS/RHEL
sudo yum install redis

# macOS
brew install redis

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

---

## 🔗 Repository Integration

Special setup for users with existing kmransom56 network management repositories.

### What This Does
- **Scans** for existing repositories in common locations
- **Integrates** with your current tools without modifying them
- **Enhances** functionality with LTM intelligence
- **Preserves** all existing workflows

### Prerequisites
- LTM Platform installed (any method above)
- Your existing repositories accessible on the system

### Integration Steps

```bash
# 1. Navigate to LTM platform directory
cd ltm-network-intelligence-platform

# 2. Run the specialized integration script
./scripts/setup_kmransom56_integration.sh

# The script will:
# - Scan for your existing repositories
# - Show what it found
# - Offer to clone missing repositories
# - Set up integrations automatically
```

### Supported Repositories

The integration script automatically recognizes and integrates with:

#### Core Network Management
- `network-ai-troubleshooter`
- `network-device-mcp-server`  
- `ai-research-platform`
- `network_device_utils`

#### Fortinet Ecosystem (20+ repositories)
- `FortiGate-Enterprise-Platform`
- `fortinet-manager`
- `fortigate-dashboard`
- `fortinet-ai-agent-core`
- And many more...

#### Cisco Meraki
- `meraki_management_application`
- `cisco-meraki-cli-enhanced`
- `meraki-explorer`

#### AI & Automation
- `ai-network-management-system`
- `autogen`
- `fortinet-troubleshooting-agents`

### Custom Integration Options

```bash
# Scan specific paths for repositories
./scripts/setup_kmransom56_integration.sh --scan-paths /path/to/your/repos

# Clone missing repositories to specific location
./scripts/setup_kmransom56_integration.sh --clone-base ~/my-repos

# Run only specific integration phases
./scripts/setup_kmransom56_integration.sh --phase core

# See all options
./scripts/setup_kmransom56_integration.sh --help
```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Core Platform Settings
LTM_SERVER_URL=http://localhost:8000
ENVIRONMENT=production

# Database Connections
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password

MILVUS_HOST=localhost
MILVUS_PORT=19530

REDIS_URL=redis://localhost:6379

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ltm_audit
POSTGRES_USER=ltm_user
POSTGRES_PASSWORD=your_postgres_password

# Device API Keys (add your actual keys)
FORTIGATE_API_KEY=your_fortigate_api_key
MERAKI_API_KEY=your_meraki_api_key

# Security Settings
JWT_SECRET_KEY=your_jwt_secret_key_change_in_production
ENCRYPTION_KEY=your_encryption_key_32_chars_long

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/ltm_platform.log
```

### Configuration Files

Key configuration files are located in the `config/` directory:

- `unified_config.json` - Main platform configuration
- `devices_enhanced.json` - Network device configurations  
- `security_config.json` - Security and compliance settings
- `kmransom56_integration_config.json` - Repository integration settings

---

## ✅ Verification

After installation, verify everything is working:

### Health Check
```bash
# Basic health check
python unified_network_intelligence.py --health-check

# Detailed system analysis
python unified_network_intelligence.py --analyze

# Generate dashboard
python unified_network_intelligence.py --dashboard
```

### Service Availability
- **Platform API**: http://localhost:8002/api/docs
- **Neo4j Browser**: http://localhost:7474
- **Grafana**: http://localhost:3000
- **Prometheus**: http://localhost:9090

### Test API Access
```bash
# Get authentication token
curl -X POST \"http://localhost:8002/api/auth/login\" \\
  -H \"Content-Type: application/json\" \\
  -d '{\"username\": \"admin\", \"password\": \"admin123\"}'

# Test device endpoint (use token from above)
curl -X GET \"http://localhost:8002/api/devices\" \\
  -H \"Authorization: Bearer YOUR_TOKEN_HERE\"
```

---

## 🔧 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Check what's using port 8002
sudo netstat -tlnp | grep :8002
sudo lsof -i :8002

# Kill the process if needed
sudo kill -9 [PID]
```

#### Permission Denied
```bash
# Fix script permissions
chmod +x scripts/*.sh

# Fix directory permissions
sudo chown -R $USER:$USER /path/to/ltm-platform
```

#### Database Connection Issues
```bash
# Test Neo4j connection
curl http://localhost:7474/db/neo4j/tx/commit

# Test Redis connection
redis-cli ping

# Check service status
sudo systemctl status neo4j
sudo systemctl status redis
```

#### Python Dependencies
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Update pip
pip install --upgrade pip

# Clear pip cache
pip cache purge
```

### Getting Help

1. **Check Logs**: `tail -f logs/ltm_platform.log`
2. **Run Health Check**: `python unified_network_intelligence.py --health-check`
3. **Check Service Status**: `docker-compose ps` (Docker) or `systemctl status [service]` (Native)
4. **Review Documentation**: See `/docs` folder for detailed guides

---

## 🎉 Next Steps

After successful installation:

1. **Configure Your Devices**: Edit `config/devices_enhanced.json`
2. **Set API Keys**: Update `.env` file with your device API keys
3. **Run First Analysis**: `python unified_network_intelligence.py --analyze`
4. **Explore Dashboards**: Visit http://localhost:8002/api/docs
5. **Integrate Repositories**: Run repository integration if you have existing tools

Ready to transform your network management! 🚀