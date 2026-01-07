# Network Access Setup Guide
**Enable Team Access to Your MCP Web Dashboard**

## 🌐 Overview

This guide will help you set up network access so your teammates can use the Network Device MCP Dashboard from their computers on your network.

## 🔧 Step 1: Find Your Computer's IP Address

### Method 1: Command Line
```cmd
ipconfig
```
Look for your main network adapter's IPv4 address (usually starts with 192.168.x.x or 10.x.x.x)

### Method 2: PowerShell
```powershell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.*"} | Select-Object IPAddress, InterfaceAlias
```

### Method 3: Windows Settings
1. Open Settings → Network & Internet
2. Click "Properties" for your active connection
3. Note the IPv4 address

**Example:** Your IP might be `192.168.1.100`

## 🔥 Step 2: Configure Windows Firewall

### Option A: Quick Setup (Recommended)
Run this batch file as Administrator:

```cmd
@echo off
echo Configuring Windows Firewall for MCP Dashboard...

REM Allow inbound traffic on port 5000
netsh advfirewall firewall add rule name="MCP Network Dashboard" dir=in action=allow protocol=TCP localport=5000

REM Allow outbound traffic (usually enabled by default)
netsh advfirewall firewall add rule name="MCP Network Dashboard Out" dir=out action=allow protocol=TCP localport=5000

echo Firewall configured successfully!
echo Your team can now access the dashboard at: http://%computername%:5000
echo Or using IP address: http://[YOUR-IP]:5000
pause
```

Save this as `setup-firewall.bat` and run as Administrator.

### Option B: Manual Firewall Setup
1. **Open Windows Defender Firewall**
   - Press Win+R, type `wf.msc`, press Enter

2. **Create Inbound Rule**
   - Click "Inbound Rules" → "New Rule"
   - Select "Port" → Next
   - Select "TCP" → Specific Local Ports: `5000`
   - Select "Allow the connection" → Next
   - Check all profiles (Domain, Private, Public) → Next
   - Name: "MCP Network Dashboard" → Finish

3. **Create Outbound Rule** (if needed)
   - Repeat above steps for "Outbound Rules"

## 🚀 Step 3: Start the Dashboard Server

### For Network Access
Update your `start-web-dashboard.bat` to bind to all network interfaces:

```batch
@echo off
echo Starting MCP Dashboard for Network Access...

call venv\Scripts\activate.bat

REM Set Flask to listen on all network interfaces
set FLASK_RUN_HOST=0.0.0.0
set FLASK_RUN_PORT=5000

python rest_api_server.py

pause
```

### Or Modify `rest_api_server.py`
Ensure the last line uses `host='0.0.0.0'`:
```python
app.run(host='0.0.0.0', port=5000, debug=True)
```

## 👥 Step 4: Share Access with Your Team

### Internal URLs to Share
Replace `[YOUR-IP]` with your actual IP address:

```
Main Dashboard: http://[YOUR-IP]:5000
API Documentation: http://[YOUR-IP]:5000/api
Health Check: http://[YOUR-IP]:5000/health

Examples:
- http://192.168.1.100:5000
- http://10.0.0.50:5000
```

### Create Team Access Document
```markdown
# MCP Dashboard Access

## 🌐 Web Dashboard
**URL:** http://[YOUR-IP]:5000

## 🔍 Quick Start
1. Open the URL in any web browser
2. Click "Store Investigation" 
3. Select brand (BWW, Arby's, Sonic)
4. Enter store ID (e.g., 155)
5. Click "Start Investigation"

## 📊 Available Features
- Store security analysis
- URL blocking reports  
- FortiManager status
- Real-time monitoring
- Professional reports

## ❓ Troubleshooting
- **Page won't load:** Contact IT Admin
- **Connection error:** Server may be offline
- **No data showing:** Check store ID or contact IT

**IT Contact:** [Your Name] - [Your Email/Phone]
```

## 🔒 Step 5: Security Considerations

### Network Security
```batch
REM Only allow access from your internal network
REM Example: Only allow 192.168.1.x network
netsh advfirewall firewall set rule name="MCP Network Dashboard" new remoteip=192.168.1.0/24
```

### Access Control Options
1. **IP-based restrictions** (above)
2. **Windows Authentication** (if needed)
3. **VPN-only access** for remote workers
4. **Time-based restrictions** for business hours only

## 🖥️ Step 6: Advanced Network Setup

### Static IP Assignment
For consistent access, consider setting a static IP:

1. **Open Network Settings**
2. **Change adapter options**
3. **Right-click your network adapter** → Properties
4. **Select "Internet Protocol Version 4"** → Properties
5. **Choose "Use the following IP address"**
6. **Enter:** IP, Subnet, Gateway, DNS

### Port Forwarding (If Needed)
If your team is on different network segments:

1. **Access your router's admin panel** (usually 192.168.1.1)
2. **Find Port Forwarding settings**
3. **Forward external port 5000 to your computer's IP:5000**
4. **Save and restart router**

## 📊 Step 7: Monitoring and Maintenance

### Check Dashboard Status
```cmd
REM Test if dashboard is accessible
curl http://localhost:5000/health

REM Test from network
curl http://[YOUR-IP]:5000/health
```

### Monitor Team Usage
The dashboard shows connection status and can log access:
- Green dot = Server running
- Team members' browsers will show real-time status
- Check server console for access logs

### Automatic Startup (Production)
Create a Windows Service or Scheduled Task:

```cmd
REM Using Task Scheduler
schtasks /create /tn "MCP Dashboard" /tr "C:\path\to\start-web-dashboard.bat" /sc onstart /ru System
```

## 🎯 Step 8: Team Training

### Quick Training Checklist
- [ ] Share dashboard URL with team
- [ ] Demo store investigation process
- [ ] Explain security health scores
- [ ] Show where to find exported reports
- [ ] Provide troubleshooting contacts

### Team Capabilities
Once network access is set up, your team can:
✅ Investigate any store across all brands
✅ Monitor security events in real-time
✅ Generate professional reports
✅ Access FortiManager status
✅ No Claude Desktop or technical knowledge required

## 🚨 Troubleshooting Network Access

### Common Issues

**"Connection Refused" Error:**
```cmd
REM Check if server is running
netstat -an | findstr :5000

REM Check firewall status
netsh advfirewall firewall show rule name="MCP Network Dashboard"
```

**"Page Not Found" Error:**
- Verify server is running with `0.0.0.0` binding
- Check firewall rules are active
- Confirm IP address is correct

**Slow Response:**
- Check network bandwidth
- Monitor server resource usage
- Consider upgrading hardware if needed

**Team Can't Access:**
- Verify they're on the same network
- Check their firewall/antivirus settings
- Test with `ping [YOUR-IP]` first

---

## 📋 Final Checklist

Before going live with your team:

- [ ] Server starts successfully
- [ ] Firewall rules configured
- [ ] Dashboard accessible via IP
- [ ] Health check returns "healthy"
- [ ] Store investigation works
- [ ] Reports export correctly
- [ ] Team members can access URL
- [ ] Backup server restart procedure documented

**Your Network Device MCP Dashboard is now ready for team access!** 🎉

**Next:** Consider implementing the additional network tools from your `network_tools.txt` for even more functionality.