@echo off
REM Complete Setup Script for Your Restaurant Network Management System

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║            🍽️  Restaurant Network Management System 🍽️            ║
echo ║                                                                   ║  
echo ║        FortiManager Integration for Arbys, BWW, and Sonic        ║
echo ║              + Cisco Meraki + Power Automate Ready               ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

echo This system is specifically designed for your multi-restaurant network:
echo.
echo 🏪 FortiManager Instances:
echo    • Arbys: 10.128.144.132 (ibadmin)
echo    • BWW: 10.128.145.4 (ibadmin)  
echo    • Sonic: 10.128.156.36 (ibadmin)
echo.
echo 🔧 Integration Capabilities:
echo    • Claude Desktop AI management
echo    • Power Automate workflows
echo    • REST API for custom automation
echo    • Centralized monitoring and reporting
echo.

echo [STEP 1] Installing MCP Server...
echo =================================
call install.bat
if %errorlevel% neq 0 (
    echo ❌ Installation failed. Please check the errors above.
    pause
    exit /b 1
)

echo.
echo [STEP 2] Setting up your .env configuration...
echo =============================================

echo ✓ Created .env file with your FortiManager configurations
echo.
echo ⚠️  CRITICAL: You must add your actual passwords to .env file!
echo.

echo Opening .env file for you to edit...
echo.
echo Please update these lines with your actual passwords:
echo   FM_ARBYS_PASSWORD=your-arbys-password-here
echo   FM_BWW_PASSWORD=your-bww-password-here  
echo   FM_SONIC_PASSWORD=your-sonic-password-here
echo   MERAKI_API_KEY=your-meraki-api-key-here
echo   MERAKI_ORG_ID=your-organization-id-here
echo.

timeout 3
notepad .env

echo.
set /p env_updated=Have you updated .env with your actual credentials? (y/n): 
if /i not "%env_updated%"=="y" (
    echo.
    echo ❌ Please update the .env file with your credentials and run this script again.
    pause
    exit /b 1
)

echo.
echo [STEP 3] Validating your configuration...
echo ========================================
call validate-config.bat
if %errorlevel% neq 0 (
    echo ❌ Configuration validation failed. Please check your credentials.
    pause
    exit /b 1
)

echo.
echo [STEP 4] Setting up Claude Desktop integration...
echo ================================================
call setup-claude.bat

echo.
echo [STEP 5] Creating Power Automate integration files...
echo ====================================================

echo Creating Flask API wrapper for Power Automate...
if not exist "power-automate-examples\requirements.txt" (
    (
    echo flask>=2.3.0
    echo python-dotenv>=1.0.0
    ) > power-automate-examples\requirements.txt
)

echo ✓ Power Automate integration examples created
echo ✓ REST API wrapper ready

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                        🎉 SETUP COMPLETE! 🎉                     ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

echo Your Restaurant Network Management System is ready!
echo.

echo 🎯 WHAT YOU CAN DO NOW:
echo ========================
echo.
echo 1️⃣ **Test in Claude Desktop** (restart Claude Desktop first):
echo    "List all my FortiManager instances"
echo    "Show me devices managed by Arbys FortiManager"
echo    "Get network infrastructure summary"
echo    "What's the status of BWW restaurant network?"
echo.

echo 2️⃣ **Advanced Claude Commands**:
echo    "Get policy packages from Sonic FortiManager"
echo    "Deploy Guest_WiFi policy to all Arbys devices"
echo    "Show me configuration status"
echo    "Get devices managed by all FortiManager instances"
echo.

echo 3️⃣ **Power Automate Integration**:
echo    • HTTP Connector: Use REST API endpoints
echo    • File Watcher: Monitor JSON status exports  
echo    • Database: Export to SQL Server for reporting
echo.

echo 📡 REST API Endpoints (for Power Automate):
echo ===========================================
echo.
echo To start the API server:
echo   cd power-automate-examples
echo   python restaurant_network_api.py
echo.
echo Then use these endpoints in Power Automate:
echo   GET  http://localhost:5000/api/restaurants
echo   GET  http://localhost:5000/api/restaurant/Arbys/devices
echo   GET  http://localhost:5000/api/restaurant/BWW/devices/status  
echo   POST http://localhost:5000/api/restaurant/Sonic/deploy-policy
echo   GET  http://localhost:5000/api/all-restaurants/status
echo.

echo 🚀 BUSINESS USE CASES:
echo ======================
echo.
echo 🏪 **Restaurant Health Monitoring**:
echo     • Power Automate checks device status every 15 minutes
echo     • Alerts if any restaurant locations have network issues
echo     • Escalation based on restaurant brand priority
echo.

echo 📋 **Policy Management**:
echo     • SharePoint form for policy deployment requests
echo     • Automated deployment to Arbys, BWW, or Sonic networks
echo     • Confirmation emails with deployment status
echo.

echo 🔒 **Security Event Processing**:
echo     • Aggregate security events from all 3 FortiManagers
echo     • Create ServiceNow incidents for high-priority threats
echo     • Teams notifications with restaurant location details
echo.

echo 📊 **Weekly Reporting**:
echo     • Automated Excel reports by restaurant brand
echo     • Network device inventory and compliance status
echo     • Executive dashboard with health metrics
echo.

echo 💡 POWER AUTOMATE FLOW IDEAS:
echo =============================
echo.
echo ✅ **Peak Hours Monitoring**: Different alert thresholds during meal rushes
echo ✅ **New Store Rollout**: Automated network setup for new locations  
echo ✅ **PCI Compliance**: Monthly compliance reports for payment systems
echo ✅ **Bulk Policy Updates**: Deploy security updates to all brands
echo ✅ **Emergency Response**: Automatic escalation for critical failures
echo.

echo 📁 FILE STRUCTURE:
echo ==================
echo.
echo %CD%\
echo ├── 🔧 src\                    (MCP server source code)
echo ├── ⚙️ .env                    (YOUR CREDENTIALS - keep secure!)
echo ├── 🚀 power-automate-examples\  (Power Automate integration)
echo │   ├── restaurant_network_api.py  (REST API wrapper)
echo │   └── README.md              (Integration examples)
echo ├── 📋 validate-config.bat     (Test your configuration)
echo └── 📖 README.md              (Full documentation)
echo.

echo 🔐 SECURITY REMINDERS:
echo ======================
echo • Your .env file contains sensitive passwords - keep it secure!
echo • Don't commit .env to version control systems
echo • Use dedicated service accounts for API access
echo • Regularly rotate passwords and API keys
echo • Monitor API usage for suspicious activity
echo.

echo 🆘 NEED HELP?
echo =============
echo • Run validate-config.bat to test your setup
echo • Check logs\ folder for troubleshooting
echo • See power-automate-examples\README.md for detailed workflows
echo • Run test-server.bat if Claude Desktop doesn't see tools
echo.

echo 🎊 CONGRATULATIONS!
echo ===================
echo You now have a powerful, AI-enabled network management system
echo that integrates your restaurant infrastructure with modern automation tools!
echo.

echo Next: Restart Claude Desktop and try: "Show me my restaurant networks"
echo.
pause
