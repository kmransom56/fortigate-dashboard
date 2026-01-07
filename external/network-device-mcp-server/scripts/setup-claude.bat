@echo off
REM Master Setup Script - Tries multiple approaches to configure Claude Desktop

echo Claude Desktop Configuration Setup
echo ===================================
echo.

echo This script will try multiple methods to configure Claude Desktop.
echo.

REM Method 1: Try Python script (most reliable)
echo [Method 1] Trying Python-based configuration...
python setup_claude_config.py
if %errorlevel% equ 0 (
    echo ✓ Python method succeeded!
    goto :success
)

echo ❌ Python method failed, trying alternative...
echo.

REM Method 2: Try simple batch file approach  
echo [Method 2] Trying simple configuration method...
call setup-claude-config-simple.bat
if %errorlevel% equ 0 (
    echo ✓ Simple method succeeded!
    goto :success
)

echo ❌ Simple method failed, trying PowerShell...
echo.

REM Method 3: Try the fixed PowerShell approach
echo [Method 3] Trying PowerShell configuration...
call setup-claude-config.bat
if %errorlevel% equ 0 (
    echo ✓ PowerShell method succeeded!
    goto :success
)

REM All methods failed - manual instructions
echo.
echo ❌ All automatic methods failed. Manual setup required:
echo.
echo 1. Open this file in notepad:
echo    %APPDATA%\Claude\claude_desktop_config.json
echo.
echo 2. If the file doesn't exist, create it with this content:
echo.
echo {
echo   "mcpServers": {
echo     "network-devices": {
echo       "command": "python",
echo       "args": ["%CD%\\src\\main.py"],
echo       "env": {
echo         "PYTHONPATH": "%CD%\\src",
echo         "CONFIG_FILE": "%CD%\\config\\devices.json"
echo       }
echo     }
echo   }
echo }
echo.
echo 3. If the file exists, add the "network-devices" section to mcpServers
echo.
echo 4. Save and restart Claude Desktop
echo.
goto :end

:success
echo.
echo ✅ Configuration completed successfully!
echo.
echo Your Claude Desktop now includes the Network Device MCP Server.
echo.
echo 📋 What's configured:
echo - FortiGate device management
echo - FortiManager policy deployment  
echo - Meraki cloud management
echo - Multi-platform network reporting
echo.
echo 🚀 Next steps:
echo 1. Edit config\devices.json with your device credentials
echo 2. Run: install.bat
echo 3. Run: test-server.bat
echo 4. Restart Claude Desktop
echo 5. Try: "Show me my network devices" in Claude
echo.

:end
pause