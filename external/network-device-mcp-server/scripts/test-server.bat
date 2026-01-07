@echo off
REM Test Network Device MCP Server

echo Testing Network Device MCP Server
echo =================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERROR: Virtual environment not found.
    echo.
    echo Please run install.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Check if main.py exists
if not exist "src\main.py" (
    echo ❌ ERROR: MCP server source code not found.
    echo Expected: src\main.py
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if configuration file exists
if not exist "config\devices.json.user" (
    echo ⚠️  Warning: devices.json.user not found, using template
    if exist "config\devices.json" (
        copy "config\devices.json" "config\devices.json.user" >nul
        echo ✓ Copied template configuration
    ) else (
        echo ❌ ERROR: No configuration files found
        pause
        exit /b 1
    )
)

echo ✓ Configuration file: config\devices.json.user

REM Test Python and dependencies
echo.
echo Testing Python environment...
python --version
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python not available in virtual environment
    pause
    exit /b 1
)

echo Testing required packages...
python -c "import mcp; print('✓ MCP package installed')"
if %errorlevel% neq 0 (
    echo ❌ ERROR: MCP package not installed
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

python -c "import httpx; print('✓ httpx package installed')"
if %errorlevel% neq 0 (
    echo ❌ ERROR: httpx package not installed
    echo Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo.
echo ✅ All dependencies are installed correctly!
echo.
echo Testing MCP server startup...
echo.
echo ⚠️  This will start the MCP server in test mode.
echo    You should see MCP protocol initialization messages.
echo    Press Ctrl+C to stop the test when you see the messages.
echo.
echo If you see JSON-RPC messages, the server is working correctly!
echo.
pause

REM Test server startup with timeout
echo Starting server test (will auto-stop after 10 seconds)...
echo.

REM Set environment variables for testing
set CONFIG_FILE=%CD%\config\devices.json.user
set PYTHONPATH=%CD%\src

REM Run the server with a timeout
timeout 10 python src\main.py 2>&1

echo.
echo.
echo Test Results:
echo =============

if %errorlevel% equ 1 (
    echo ✅ Server test completed (timeout reached - this is normal)
    echo.
    echo If you saw JSON-RPC messages above, the server is working correctly!
    echo.
    echo Expected messages include:
    echo - Server initialization
    echo - Tool registration messages  
    echo - MCP protocol handshake
    echo.
) else (
    echo ⚠️  Server exited with code: %errorlevel%
    echo.
    echo If you saw error messages above, check:
    echo 1. Configuration file syntax (must be valid JSON)
    echo 2. Network connectivity to your devices
    echo 3. Device credentials in config\devices.json.user
    echo.
    echo Note: Connection errors to devices are OK for testing -
    echo       the server should still start and show available tools.
)

echo 🔧 Troubleshooting:
echo ==================
echo.
echo If you see import errors:
echo   → Run install.bat again
echo.
echo If you see JSON syntax errors:
echo   → Check config\devices.json.user for valid JSON
echo.
echo If you see network/connection errors:
echo   → This is normal if devices aren't configured yet
echo   → The server should still start and register tools
echo.
echo If Claude Desktop doesn't see the tools:
echo   → Run setup-claude.bat to configure Claude Desktop
echo   → Restart Claude Desktop completely
echo   → Check %APPDATA%\Claude\claude_desktop_config.json
echo.

echo 📋 Next Steps:
echo ==============
echo 1. Configure your devices: notepad config\devices.json.user
echo 2. Setup Claude Desktop: setup-claude.bat  
echo 3. Restart Claude Desktop
echo 4. Test in Claude: "Show me network device tools"
echo.
pause