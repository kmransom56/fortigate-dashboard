# FortiGate Dashboard Development Automation

This document describes the complete automation setup for the FortiGate Dashboard development workflow.

## 🚀 Quick Start

1. **Setup Development Environment**
   ```bash
   python tools/setup_dev_environment.py
   ```

2. **Start Development with File Watching**
   ```bash
   start_dev_watch.bat
   ```

3. **Create a Backup**
   ```bash
   C:\users\south\Scripts\quick_backup.bat
   ```

## 📁 File Structure

```
fortigate-dashboard/
├── automation/                 # Automation scripts and configs
│   ├── logs/                  # Automation logs
│   ├── power_automate_integration.ps1
│   ├── power_automate_flow_template.json
│   └── webhook_listener.ps1
├── C:\users\south\Scripts/    # System-wide scripts
│   ├── backup_fortigate_dashboard.ps1
│   └── quick_backup.bat
├── tools/watch_dev.py              # File watcher for auto-restart
├── scripts/start_dev_watch.bat       # Start development environment
├── tools/fortigate_dev_helper.py   # FortiGate API development tools
└── tools/setup_dev_environment.py  # Automated environment setup
```

## 🔍 File Watchers for Auto-Restart

### Features
- **Real-time monitoring** of Python, HTML, CSS, JavaScript, JSON, and .env files
- **Automatic server restart** when files change
- **Intelligent throttling** to avoid rapid restarts
- **Virtual environment** auto-detection and activation

### Usage
```bash
start_dev_watch.bat  # Recommended
# or
python tools/watch_dev.py  # Direct
```

## 💾 Automated Backup Scripts

### PowerShell Backup Script
**Location**: `C:\users\south\Scripts\backup_fortigate_dashboard.ps1`

#### Features
- **Incremental backups** with timestamps
- **Git snapshot creation** before backups
- **Automatic cleanup** of old backups (keeps last 10)
- **Comprehensive logging** with detailed manifests

#### Usage
```powershell
.\backup_fortigate_dashboard.ps1
.\backup_fortigate_dashboard.ps1 -MaxBackups 15 -Verbose
```

### Quick Backup
```bash
C:\users\south\Scripts\quick_backup.bat
```

## 🔄 Power Automate Integration

### Core Integration Script
**Location**: `automation\power_automate_integration.ps1`

#### Available Actions
- `deploy` - Full deployment pipeline
- `backup` - Create backup
- `test` - Run test suite
- `status` - Get system status
- `restart` - Restart services

#### Usage
```powershell
.\power_automate_integration.ps1 -Action deploy -Environment production
.\power_automate_integration.ps1 -Action test -TeamsWebhookUrl "https://..."
```

### Webhook Listener
**Location**: `automation\webhook_listener.ps1`

#### API Endpoints
- `POST /webhook/deploy` - Trigger deployment
- `POST /webhook/backup` - Create backup  
- `POST /webhook/test` - Run tests
- `GET /health` - Health check

## 🔧 FortiGate API Development Helper

### Features
**Location**: `tools/fortigate_dev_helper.py`

#### Usage Examples
```bash
python tools/fortigate_dev_helper.py --test-connection
python tools/fortigate_dev_helper.py --test-all-endpoints
python tools/fortigate_dev_helper.py --export-responses
python tools/fortigate_dev_helper.py --monitor system/performance
python tools/fortigate_dev_helper.py --test-suite
```

#### Available Endpoints
- `system_status` - System status information
- `system_interface` - Network interfaces
- `dhcp_leases` - DHCP lease information
- `switch_managed` - Managed switches
- `detected_devices` - Detected devices

## ⚙️ Configuration

### Environment Variables (.env)
```bash
FORTIGATE_HOST=https://192.168.0.254
FORTIGATE_API_TOKEN=your-api-token-here
TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
NOTIFICATION_EMAIL=your-email@domain.com
```

## 🧪 Testing and Quality Assurance

### Available Scripts
- `run_tests.bat` - Run test suite
- `format_code.bat` - Format and lint code
- `quick_deploy.bat` - Deploy to production

## 🚨 Troubleshooting

### Common Issues
- **File Watcher**: Check Python virtual environment activation
- **Backup Script**: Verify PowerShell execution policy
- **API Connection**: Verify FortiGate host URL and API token
- **Power Automate**: Check PowerShell execution policy and file paths

### Log Locations
- Development logs: `automation/logs/`
- API logs: `automation/logs/api_requests/`
- Backup logs: `C:\users\south\backups\fortigate-dashboard\backup.log`

---
**Created by**: Automated Development Environment Setup
