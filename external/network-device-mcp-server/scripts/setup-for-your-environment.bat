@echo off
REM Setup Script for Your Specific FortiManager/Meraki Configuration

echo ╔══════════════════════════════════════════════════════════════╗
echo ║       Network Device MCP Server - Custom Configuration      ║  
echo ║     3 FortiManagers (Arbys/BWW/Sonic) + Meraki Integration  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo Setting up MCP server for your specific infrastructure:
echo - FortiManager Arbys (10.128.144.132)
echo - FortiManager BWW (10.128.145.4)  
echo - FortiManager Sonic (10.128.156.36)
echo - Cisco Meraki Dashboard
echo.

REM Step 1: Run basic installation
echo [1/4] Installing MCP server dependencies...
echo =========================================
call install.bat
if %errorlevel% neq 0 (
    echo ERROR: Installation failed
    pause
    exit /b 1
)

REM Step 2: Configure environment file
echo.
echo [2/4] Setting up environment configuration...
echo =============================================

echo.
echo ✓ Created .env file with your FortiManager configurations:
echo   - Arbys: 10.128.144.132 (ibadmin)
echo   - BWW: 10.128.145.4 (ibadmin)
echo   - Sonic: 10.128.156.36 (ibadmin)
echo.

echo ⚠️  IMPORTANT: You need to update .env with your actual passwords!
echo.
echo Opening .env file for you to edit...
timeout 3
notepad .env

echo.
echo Please update these values in the .env file:
echo - FM_ARBYS_PASSWORD=your-arbys-password-here
echo - FM_BWW_PASSWORD=your-bww-password-here
echo - FM_SONIC_PASSWORD=your-sonic-password-here
echo - MERAKI_API_KEY=your-meraki-api-key-here
echo - MERAKI_ORG_ID=your-organization-id-here
echo.

set /p credentials_updated=Have you updated the .env file with your credentials? (y/n): 
if /i not "%credentials_updated%"=="y" (
    echo.
    echo Please update the .env file and run this script again.
    echo Location: %CD%\.env
    pause
    exit /b 1
)

REM Step 3: Setup Claude Desktop integration
echo.
echo [3/4] Configuring Claude Desktop integration...
echo ==============================================
call setup-claude.bat
if %errorlevel% neq 0 (
    echo WARNING: Claude Desktop configuration may have issues
    echo You can configure manually if needed
)

REM Step 4: Test the server
echo.
echo [4/4] Testing server with your configuration...
echo ==============================================

echo Testing environment configuration...
call venv\Scripts\activate.bat

python -c "from src.config import get_config; c=get_config(); print(f'✓ Found {len(c.fortimanager_instances)} FortiManager instances'); print(f'✓ Meraki configured: {c.has_meraki_config()}'); [print(f'  - {fm[\"name\"]}: {fm[\"host\"]}') for fm in c.fortimanager_instances]"

if %errorlevel% neq 0 (
    echo ❌ Configuration test failed. Please check your .env file.
    pause
    exit /b 1
)

echo.
echo ✅ Configuration test passed!
echo.

echo Quick server startup test (10 seconds)...
timeout 10 python src\main.py 2>&1 | findstr /C:"FortiManager" /C:"Meraki" /C:"error" /C:"Error"

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Setup Complete!                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🎯 Your Network Device MCP Server is configured for:
echo.
echo 📡 FortiManager Instances:
echo    • Arbys (10.128.144.132) - Restaurant management
echo    • BWW (10.128.145.4) - Buffalo Wild Wings  
echo    • Sonic (10.128.156.36) - Drive-in locations
echo.
echo ☁️  Cisco Meraki Dashboard:
echo    • Cloud-managed devices and networks
echo.

echo 🚀 Try these commands in Claude Desktop:
echo.
echo "List all my FortiManager instances"
echo "Show me devices managed by Arbys FortiManager"  
echo "Get policy packages from BWW FortiManager"
echo "Show me my network infrastructure summary"
echo "What devices are managed by Sonic FortiManager?"
echo "Get my Meraki networks"
echo.

echo 🔧 Advanced Commands:
echo "Install policy package 'Guest_WiFi' to all devices in BWW"
echo "Get comprehensive network infrastructure summary" 
echo "Show me the current configuration status"
echo.

echo 🔗 Power Automate Integration Ideas:
echo ====================================
echo.
echo 💡 Restaurant Network Health Monitoring:
echo   • Schedule: Every 15 minutes
echo   • Action: Check device status across all 3 FortiManagers
echo   • Condition: If any location has device failures
echo   • Action: Send alert to network team with location details
echo.
echo 💡 Policy Deployment Workflow:
echo   • Trigger: SharePoint policy request form
echo   • Action: Deploy to specified restaurant group (Arbys/BWW/Sonic)
echo   • Action: Update tracking sheet with deployment status
echo   • Action: Email confirmation to requestor
echo.
echo 💡 Security Event Aggregation:
echo   • Schedule: Every 5 minutes
echo   • Action: Collect security events from all FortiManagers
echo   • Condition: If high-priority threats detected
echo   • Action: Create incident in ServiceNow
echo   • Action: Send SMS to security team with location
echo.
echo 💡 Network Inventory Reporting:
echo   • Schedule: Weekly
echo   • Action: Generate device inventory across all locations
echo   • Action: Create Excel report by restaurant brand
echo   • Action: Email to management with compliance status
echo.

echo 📋 Important Next Steps:
echo ========================
echo.
echo 1. **Restart Claude Desktop** completely (close and reopen)
echo 2. **Test in Claude**: "Show me my FortiManager instances"
echo 3. **Verify credentials**: Try connecting to each FortiManager
echo 4. **Set up Power Automate**: Use the integration examples above
echo.

echo 🔒 Security Notes:
echo ==================
echo • Your credentials are stored securely in .env file
echo • .env file should not be shared or committed to version control
echo • Consider using dedicated service accounts for API access
echo • Regularly rotate passwords and API keys
echo.

echo For detailed documentation, see README.md
echo For troubleshooting, run test-server.bat
echo.

pause
