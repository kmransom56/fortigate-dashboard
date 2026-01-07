# Team Access Setup Guide

## 🌐 Web Dashboard for Your Team

Your Network Device Management system now has a user-friendly web interface that your teammates can access without needing Claude Desktop or technical knowledge.

## 🚀 Quick Start for Team Members

### 1. Access the Dashboard
Once the server is running, team members can access:
- **Main Dashboard**: `http://localhost:5000`
- **From other computers**: `http://[YOUR-IP]:5000`

### 2. Available Tools

#### 🔍 Store Investigation
- Select any brand (BWW, Arby's, Sonic)
- Enter store ID (e.g., 155, 1234) 
- Choose analysis period
- Get comprehensive security analysis

#### 🏪 Brand Overviews
- **Buffalo Wild Wings**: Infrastructure and security status
- **Arby's**: Device management and monitoring
- **Sonic Drive-In**: Network health and compliance

#### 🛡️ Security Monitoring
- Real-time security event tracking
- URL blocking analysis
- FortiManager status monitoring
- Compliance reporting

## 📋 For Team Members (No Technical Knowledge Required)

### How to Investigate a Store
1. **Click "Store Investigation" in the sidebar**
2. **Select the restaurant brand** from dropdown
3. **Enter the store number** (just the number, e.g., 155)
4. **Choose time period** (last 24 hours is recommended)
5. **Click "Start Investigation"**
6. **Review the results** in three tabs:
   - Security Health: Overall security score and status
   - URL Blocking: What websites are being blocked
   - Security Events: Recent security alerts and threats

### Understanding the Results

#### 🟢 Security Health Scores
- **90-100**: Excellent - Store is very secure
- **80-89**: Good - Store is secure with minor issues
- **70-79**: Warning - Store needs attention
- **Below 70**: Poor - Store requires immediate action

#### 📊 Common Issues to Look For
- **High URL blocking**: May indicate policy violations
- **Security events**: Could mean attempted attacks
- **System alerts**: Hardware or software issues
- **Policy violations**: Users accessing blocked content

#### ⚡ Quick Actions
- **Export reports**: Detailed data saved for further analysis
- **View recommendations**: Actionable steps to improve security
- **Real-time monitoring**: Status updates every minute

## 🔧 Setup Instructions for IT Admin

### Starting the Web Dashboard
```bash
# Option 1: Use the batch file (recommended)
start-web-dashboard.bat

# Option 2: Manual start
venv\Scripts\activate.bat
pip install flask flask-cors  # First time only
python rest_api_server.py
```

### Network Access for Team
To allow team access from other computers:

1. **Find your IP address**:
   ```cmd
   ipconfig
   ```

2. **Update firewall** (if needed):
   ```cmd
   # Allow port 5000 through Windows Firewall
   netsh advfirewall firewall add rule name="MCP Dashboard" dir=in action=allow protocol=TCP localport=5000
   ```

3. **Share the URL with team**:
   ```
   http://[YOUR-IP-ADDRESS]:5000
   ```

### Configuration for Production Use

#### Environment Variables
For production deployment, set these environment variables:
```bash
# FortiManager instances
FORTIMANAGER_BWW_HOST=10.128.145.4
FORTIMANAGER_BWW_USERNAME=admin
FORTIMANAGER_BWW_PASSWORD=your-password

FORTIMANAGER_ARBYS_HOST=your-arbys-fm-host
FORTIMANAGER_ARBYS_USERNAME=admin
FORTIMANAGER_ARBYS_PASSWORD=your-password

FORTIMANAGER_SONIC_HOST=your-sonic-fm-host
FORTIMANAGER_SONIC_USERNAME=admin
FORTIMANAGER_SONIC_PASSWORD=your-password

# Report locations
BACKUP_PATH=C:\temp\network-backups
REPORT_PATH=C:\temp\network-reports
```

#### Automatic Startup
To start the dashboard automatically:

1. **Create Windows Service** (recommended for production)
2. **Add to Startup Folder** for desktop systems
3. **Use Task Scheduler** for scheduled restarts

## 🔒 Security Considerations

### Access Control
- Dashboard runs on internal network only
- No external internet access required
- All data stays within your infrastructure

### Data Protection
- Reports exported to local file system
- No data sent to external services
- Audit trail of all investigations

### User Permissions
- Read-only access to network devices
- No configuration changes possible
- Safe for non-technical team members

## 📞 Support for Team Members

### Common Questions

**Q: "The page won't load"**
A: Check that the MCP server is running. Contact IT admin.

**Q: "I get 'Connection Error'"**
A: The server may be down. Try refreshing or contact IT admin.

**Q: "No data is showing"**
A: The device may be offline or not configured. Try a different store ID.

**Q: "What do these security events mean?"**
A: Check the recommendations section for explanations and next steps.

### Getting Help
1. Check the built-in documentation (Help section)
2. Contact IT admin for technical issues
3. Review exported reports for detailed analysis

## 🎯 Use Cases for Different Roles

### Store Operations Manager
- **Daily health checks**: Review security scores each morning
- **Incident response**: Investigate specific store issues
- **Compliance monitoring**: Ensure all stores meet security standards

### IT Support Specialist
- **Troubleshooting**: Investigate network issues at specific locations
- **Policy enforcement**: Monitor URL blocking and violations
- **Security analysis**: Review threat patterns across brands

### Regional Manager
- **Brand overviews**: Compare security across different restaurant brands
- **Performance monitoring**: Track security metrics over time
- **Reporting**: Generate executive summaries for leadership

---

## 📈 Benefits of Web Interface

✅ **No Claude Desktop required** - No message limits
✅ **Team-friendly** - Anyone can use it
✅ **Real-time data** - Always up to date
✅ **Comprehensive analysis** - All tools in one place
✅ **Professional reports** - Export detailed findings
✅ **Secure access** - Internal network only

Your team now has professional-grade network security monitoring that's as easy to use as any web application!