@echo off
REM Simple Claude Desktop Configuration Setup (No PowerShell Required)

echo Simple Claude Desktop Configuration Setup
echo =========================================
echo.

set "CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json"
set "SERVER_PATH=%CD%"

if not exist "%APPDATA%\Claude" (
    echo Creating Claude configuration directory...
    mkdir "%APPDATA%\Claude"
)

echo Creating Claude Desktop configuration...
echo Config file: %CLAUDE_CONFIG%
echo Server path: %SERVER_PATH%

REM Create the JSON configuration file directly
(
echo {
echo   "mcpServers": {
echo     "filesystem": {
echo       "command": "npx",
echo       "args": [
echo         "@modelcontextprotocol/server-filesystem",
echo         "C:\\Users\\keith.ransom"
echo       ]
echo     },
echo     "network-devices": {
echo       "command": "python",
echo       "args": [
echo         "%SERVER_PATH%\\src\\main.py"
echo       ],
echo       "env": {
echo         "PYTHONPATH": "%SERVER_PATH%\\src",
echo         "CONFIG_FILE": "%SERVER_PATH%\\config\\devices.json"
echo       }
echo     },
echo     "github": {
echo       "command": "npx",
echo       "args": ["@modelcontextprotocol/server-github"],
echo       "env": {
echo         "GITHUB_PERSONAL_ACCESS_TOKEN": ""
echo       }
echo     }
echo   },
echo   "globalShortcut": "Ctrl+Alt+Space"
echo }
) > "%CLAUDE_CONFIG%"

if %errorlevel% neq 0 (
    echo ERROR: Failed to create configuration file
    pause
    exit /b 1
)

echo.
echo ✓ Claude Desktop configuration created successfully!
echo.
echo Configuration details:
echo - Config location: %CLAUDE_CONFIG%
echo - Network Device MCP Server: %SERVER_PATH%\src\main.py
echo - Device config file: %SERVER_PATH%\config\devices.json
echo.

echo Next steps:
echo.
echo 1. **Edit your device configuration:**
echo    notepad config\devices.json
echo    (Add your actual FortiGate/FortiManager/Meraki credentials)
echo.
echo 2. **Install Python dependencies:**
echo    install.bat
echo.
echo 3. **Test the server:**
echo    test-server.bat  
echo.
echo 4. **Restart Claude Desktop completely**
echo    (Close and reopen the application)
echo.
echo 5. **Test in Claude Desktop:**
echo    Try: "Show me network device management tools"
echo.

echo Checking Python installation...
python --version
if %errorlevel% neq 0 (
    echo.
    echo ⚠️  WARNING: Python not found via 'python' command
    echo.
    echo Options to fix:
    echo 1. Install Python from https://python.org (check "Add to PATH")
    echo 2. Try using 'py' instead (Windows Python Launcher)
    echo 3. Manually edit the config to use full Python path
    echo.
    echo To use 'py' command instead, edit %CLAUDE_CONFIG%
    echo and change "command": "python" to "command": "py"
)

echo.
pause