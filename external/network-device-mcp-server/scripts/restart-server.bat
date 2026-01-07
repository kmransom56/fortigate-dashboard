@echo off
REM Network Device MCP Server Restart Script

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║              🔄 Network Device MCP Server Restart 🔄               ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

echo [STEP 1] Stopping existing MCP server processes...
echo ==================================================

REM Kill any existing Python processes that might be running the MCP server
taskkill /F /IM python.exe /FI "WINDOWTITLE eq Network Device MCP*" 2>nul
taskkill /F /IM python.exe /FI "COMMANDLINE eq *network-device-mcp-server*" 2>nul

echo ✓ Existing processes stopped

echo.
echo [STEP 2] Waiting for cleanup...
echo ==============================
timeout /t 3 /nobreak >nul
echo ✓ Cleanup complete

echo.
echo [STEP 3] Starting Network Device MCP Server...
echo =============================================

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERROR: Virtual environment not found.
    echo Please run install.bat first to set up the environment.
    pause
    exit /b 1
)

REM Start the server in a new window
start "Network Device MCP Server" cmd /k "call venv\Scripts\activate.bat && python src\main.py"

echo ✓ Server started in new window

echo.
echo [STEP 4] Verification...
echo =======================
timeout /t 2 /nobreak >nul

REM Check if the process is running
tasklist /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq Network Device MCP Server*" 2>nul | find "python.exe" >nul
if %errorlevel% equ 0 (
    echo ✅ Server is running successfully!
) else (
    echo ⚠️  Server may not be running - check the server window for errors
)

echo.
echo ╔═══════════════════════════════════════════════════════════════════╗
echo ║                         🎉 RESTART COMPLETE 🎉                   ║
echo ╚═══════════════════════════════════════════════════════════════════╝
echo.

echo 📋 NEXT STEPS:
echo ==============
echo.
echo 1️⃣ **If you're using Claude Desktop:**
echo    → Completely restart Claude Desktop application
echo    → Wait 30 seconds after restart
echo    → Test with: "List FortiManager instances"
echo.

echo 2️⃣ **If Claude tools still don't work:**
echo    → Run: setup-claude.bat
echo    → Restart Claude Desktop again
echo    → Check server window for any error messages
echo.

echo 3️⃣ **To verify the fix worked:**
echo    → Try: "Show me BWW Store 155 information"
echo    → Try: "Get devices from BWW FortiManager"
echo    → Try: "List all FortiManager instances"
echo.

echo 🔍 TROUBLESHOOTING:
echo ===================
echo • Server window shows errors → Check .env file configuration
echo • Claude still can't see tools → Run setup-claude.bat
echo • "Function not found" errors → The fix didn't apply - contact support
echo.

echo Server window is running in background. Close this window when done.
echo.
pause
