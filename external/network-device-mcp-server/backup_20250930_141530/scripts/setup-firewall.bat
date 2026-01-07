@echo off
REM MCP Dashboard Network Access Firewall Setup
REM Run as Administrator

echo ========================================================
echo   MCP Dashboard - Network Access Firewall Setup
echo ========================================================
echo.
echo This will configure Windows Firewall to allow team access
echo to your Network Device MCP Dashboard on port 5000.
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ ERROR: This script must be run as Administrator
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo ✅ Running with Administrator privileges
echo.

REM Get current computer's IP address for display
echo 🔍 Detecting your network configuration...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr "IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set "COMPUTER_IP=%%b"
        goto :found_ip
    )
)
:found_ip

echo 📍 Your computer's IP address appears to be: %COMPUTER_IP%
echo.

echo 🔥 Configuring Windows Firewall...

REM Remove any existing rules first
netsh advfirewall firewall delete rule name="MCP Network Dashboard" >nul 2>&1
netsh advfirewall firewall delete rule name="MCP Network Dashboard Out" >nul 2>&1

REM Add inbound rule for port 5000
echo    Adding inbound rule for port 5000...
netsh advfirewall firewall add rule name="MCP Network Dashboard" dir=in action=allow protocol=TCP localport=5000

if %errorlevel% equ 0 (
    echo    ✅ Inbound rule added successfully
) else (
    echo    ❌ Failed to add inbound rule
    pause
    exit /b 1
)

REM Add outbound rule for port 5000
echo    Adding outbound rule for port 5000...
netsh advfirewall firewall add rule name="MCP Network Dashboard Out" dir=out action=allow protocol=TCP localport=5000

if %errorlevel% equ 0 (
    echo    ✅ Outbound rule added successfully
) else (
    echo    ❌ Failed to add outbound rule
    pause
    exit /b 1
)

echo.
echo ========================================================
echo   Firewall Configuration Complete! 🎉
echo ========================================================
echo.
echo Your team can now access the MCP Dashboard at:
echo.
if defined COMPUTER_IP (
    echo 🌐 Main Dashboard: http://%COMPUTER_IP%:5000
    echo 📊 API Access:     http://%COMPUTER_IP%:5000/api  
    echo 💚 Health Check:   http://%COMPUTER_IP%:5000/health
) else (
    echo 🌐 Main Dashboard: http://[YOUR-IP]:5000
    echo 📊 API Access:     http://[YOUR-IP]:5000/api
    echo 💚 Health Check:   http://[YOUR-IP]:5000/health
)
echo.
echo 📋 Next Steps:
echo 1. Start the MCP Dashboard server (start-web-dashboard.bat)
echo 2. Share the dashboard URL with your team
echo 3. Test access from another computer on your network
echo.
echo 🔒 Security Notes:
echo - Dashboard is only accessible from your local network
echo - No internet access is provided by default
echo - All data stays within your infrastructure
echo.
echo ⚠️  If you need to remove these firewall rules later:
echo    netsh advfirewall firewall delete rule name="MCP Network Dashboard"
echo    netsh advfirewall firewall delete rule name="MCP Network Dashboard Out"
echo.
pause