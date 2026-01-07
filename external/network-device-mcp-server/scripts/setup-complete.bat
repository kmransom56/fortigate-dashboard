@echo off
REM Master Setup Script for Network Device MCP Server
REM This script sets up everything needed for FortiGate/FortiManager/Meraki automation

echo ╔══════════════════════════════════════════════════════════════╗
echo ║           Network Device Management MCP Server              ║  
echo ║         FortiGate + FortiManager + Meraki Integration       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo This script will set up a complete network device management solution
echo that integrates with Claude Desktop and Power Automate for automation.
echo.

REM Step 1: Install the MCP server
echo [1/4] Installing Network Device MCP Server...
echo ============================================
call install.bat
if %errorlevel% neq 0 (
    echo ERROR: Installation failed
    pause
    exit /b 1
)

echo.
echo [2/4] Setting up Claude Desktop integration...  
echo ==============================================
call setup-claude-config.bat

echo.
echo [3/4] Creating Power Automate integration examples...
echo ====================================================

REM Create Power Automate integration folder
if not exist "power-automate-integration" mkdir power-automate-integration

REM Create example REST API wrapper
echo Creating REST API wrapper for Power Automate...
(
echo # Simple Flask wrapper for Power Automate integration
echo from flask import Flask, jsonify, request
echo import asyncio
echo import sys
echo import os
echo.
echo # Add the MCP server to path
echo sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'^)^)
echo.
echo from main import NetworkDeviceMCPServer
echo.
echo app = Flask(__name__^)
echo mcp_server = NetworkDeviceMCPServer(^)
echo.
echo @app.route('/api/health'^)
echo def health_check(^):
echo     return jsonify({"status": "healthy", "service": "network-device-mcp"}^)
echo.
echo @app.route('/api/devices/status'^)  
echo def get_device_status(^):
echo     """Get status of all network devices"""
echo     # This would call the MCP server tools
echo     return jsonify({"status": "success", "devices": []}^)
echo.
echo @app.route('/api/fortigate/&lt;host&gt;/status'^)
echo def get_fortigate_status(host^):
echo     """Get FortiGate device status - callable from Power Automate"""
echo     # Implementation would call FortiGate MCP tools
echo     return jsonify({"host": host, "status": "online"}^)
echo.
echo if __name__ == '__main__':
echo     app.run(host='0.0.0.0', port=5000^)
) > power-automate-integration\api_wrapper.py

REM Create Power Automate workflow examples
echo Creating Power Automate workflow templates...
(
echo # Power Automate Integration Examples
echo.
echo ## Method 1: HTTP Request to API Wrapper
echo 1. Create HTTP connector in Power Automate
echo 2. Set URL to: http://localhost:5000/api/devices/status  
echo 3. Set Method to: GET
echo 4. Parse JSON response and trigger actions based on device status
echo.
echo ## Method 2: File-Based Integration  
echo 1. MCP server writes device status to: C:\temp\network_status.json
echo 2. Power Automate monitors file for changes
echo 3. When file updates, read JSON and process device status
echo 4. Trigger alerts/actions based on status changes
echo.
echo ## Method 3: Database Integration
echo 1. MCP server writes status to SQL Server/Excel
echo 2. Power Automate polls database for changes
echo 3. Process status changes and trigger workflows
echo.
echo ## Example Workflows:
echo.
echo ### Device Health Monitoring
echo - Trigger: HTTP request every 15 minutes
echo - Action: Get device status from MCP server
echo - Condition: If CPU ^> 80%% or device offline
echo - Action: Send Teams/Email alert to network admin
echo.
echo ### Policy Deployment Automation  
echo - Trigger: SharePoint list item created (new policy request^)
echo - Action: Call FortiManager MCP tool to deploy policy
echo - Action: Update SharePoint with deployment status
echo - Action: Email requestor with results
echo.
echo ### Security Event Processing
echo - Trigger: Scheduled (every 5 minutes^)
echo - Action: Get security events from all platforms
echo - Condition: If high-priority security event detected
echo - Action: Create ServiceNow incident
echo - Action: Send SMS alert to security team
echo.
echo ### Network Inventory Reporting
echo - Trigger: Scheduled (weekly^)
echo - Action: Get device inventory from all platforms
echo - Action: Create Excel report with device details
echo - Action: Email report to management
echo - Action: Update CMDB with current device info
) > power-automate-integration\README.md

echo.
echo [4/4] Final setup and testing...
echo ===============================

echo Creating example device configuration...
if not exist "config\devices.json.example" (
    copy "config\devices.json" "config\devices.json.example"
)

echo Testing server startup...
call test-server.bat

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Setup Complete!                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Your Network Device Management MCP Server is now ready!
echo.
echo 📁 Project Structure:
echo    %CD%\
echo    ├── src\                     (MCP server source code^)
echo    ├── config\                  (Device configurations^) 
echo    ├── power-automate-integration\  (Power Automate examples^)
echo    └── logs\                    (Server logs^)
echo.
echo 🔧 Next Steps:
echo.
echo 1. **Configure Your Devices:**
echo    Edit: config\devices.json.user
echo    Add your actual FortiGate/FortiManager/Meraki credentials
echo.
echo 2. **Test in Claude Desktop:**
echo    - Restart Claude Desktop completely
echo    - Look for "network-devices" tools
echo    - Try: "Show me the status of my FortiGate devices"
echo.
echo 3. **Power Automate Integration:**
echo    - Review examples in power-automate-integration\
echo    - Set up HTTP connectors to call MCP tools
echo    - Create file watchers for automated monitoring
echo.
echo 4. **Device Management Capabilities:**
echo    ✓ FortiGate: System status, interfaces, policies, VPN tunnels
echo    ✓ FortiManager: Device management, policy deployment
echo    ✓ Meraki: Organization/network/device management
echo    ✓ Multi-platform reporting and automation
echo.
echo 🚀 Example Claude Commands:
echo    "Get the system status of all my FortiGate devices"
echo    "Show me the interface status on FortiGate 192.168.1.99"  
echo    "List all devices managed by FortiManager"
echo    "Get the wireless networks in my Meraki organization"
echo    "Generate a network summary report"
echo.
echo 🔗 Power Automate Examples:
echo    - Automated device health monitoring
echo    - Policy deployment workflows  
echo    - Security event processing
echo    - Network inventory reporting
echo    - Compliance checking and remediation
echo.
echo For detailed instructions, see README.md
echo.
echo Questions? Check the troubleshooting section in README.md
echo or run test-server.bat to verify everything is working.
echo.
pause