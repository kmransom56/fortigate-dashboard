@echo off
REM Setup Claude Desktop Configuration for Network Device MCP Server

echo Setting up Claude Desktop Configuration
echo ======================================
echo.

set "CLAUDE_CONFIG=%APPDATA%\Claude\claude_desktop_config.json"
set "SERVER_PATH=%CD%"

if not exist "%APPDATA%\Claude" (
    echo Creating Claude configuration directory...
    mkdir "%APPDATA%\Claude"
)

echo Updating Claude Desktop configuration...
echo Server path: %SERVER_PATH%
echo Config file: %CLAUDE_CONFIG%

REM Create a temporary PowerShell script
echo $configPath = '%CLAUDE_CONFIG%' > temp_update_config.ps1
echo $serverPath = '%SERVER_PATH%' >> temp_update_config.ps1
echo try { >> temp_update_config.ps1
echo     if (Test-Path $configPath) { >> temp_update_config.ps1
echo         $config = Get-Content $configPath -Raw ^| ConvertFrom-Json >> temp_update_config.ps1
echo     } else { >> temp_update_config.ps1
echo         $config = @{} >> temp_update_config.ps1
echo     } >> temp_update_config.ps1
echo } catch { >> temp_update_config.ps1
echo     Write-Host "Creating new config file..." >> temp_update_config.ps1
echo     $config = @{} >> temp_update_config.ps1
echo } >> temp_update_config.ps1
echo if (-not $config.mcpServers) { >> temp_update_config.ps1
echo     $config ^| Add-Member -Type NoteProperty -Name 'mcpServers' -Value @{} -Force >> temp_update_config.ps1
echo } >> temp_update_config.ps1
echo $networkDeviceServer = @{ >> temp_update_config.ps1
echo     command = 'python' >> temp_update_config.ps1
echo     args = @("$serverPath\src\main.py") >> temp_update_config.ps1
echo     env = @{ >> temp_update_config.ps1
echo         PYTHONPATH = "$serverPath\src" >> temp_update_config.ps1
echo         CONFIG_FILE = "$serverPath\config\devices.json" >> temp_update_config.ps1
echo     } >> temp_update_config.ps1
echo } >> temp_update_config.ps1
echo $config.mcpServers ^| Add-Member -Type NoteProperty -Name 'network-devices' -Value $networkDeviceServer -Force >> temp_update_config.ps1
echo $config ^| ConvertTo-Json -Depth 10 ^| Set-Content $configPath >> temp_update_config.ps1
echo Write-Host "Claude Desktop configuration updated successfully!" >> temp_update_config.ps1

REM Run the PowerShell script
powershell -ExecutionPolicy Bypass -File temp_update_config.ps1

REM Clean up temporary file
del temp_update_config.ps1

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to update configuration automatically.
    echo.
    echo Manual setup required:
    echo 1. Open: %CLAUDE_CONFIG%
    echo 2. Add this section to mcpServers:
    echo.
    echo     "network-devices": {
    echo       "command": "python",
    echo       "args": ["%SERVER_PATH%\src\main.py"],
    echo       "env": {
    echo         "PYTHONPATH": "%SERVER_PATH%\src",
    echo         "CONFIG_FILE": "%SERVER_PATH%\config\devices.json"
    echo       }
    echo     }
    echo.
    pause
    exit /b 1
)

echo.
echo Configuration completed successfully!
echo.
echo The Network Device MCP Server has been added to Claude Desktop with these settings:
echo - Server name: network-devices
echo - Command: python %SERVER_PATH%\src\main.py
echo - Config file: %SERVER_PATH%\config\devices.json
echo.
echo IMPORTANT: 
echo 1. Make sure you have Python installed and accessible via 'python' command
echo 2. Edit config\devices.json with your actual device credentials
echo 3. Restart Claude Desktop completely for changes to take effect
echo 4. Look for network device management tools in Claude Desktop
echo.

echo Your MCP server provides these capabilities:
echo - FortiGate system status, interfaces, policies, VPN status
echo - FortiManager device management, policy installation  
echo - Meraki organization/network/device management
echo - Multi-platform network summary and reporting
echo.

echo For Power Automate integration:
echo - Use file-based triggers (server writes status to files)
echo - Create REST API wrapper around MCP tools
echo - Set up scheduled network health checks
echo.

echo Testing Python availability...
python --version
if %errorlevel% neq 0 (
    echo.
    echo WARNING: Python is not available via 'python' command
    echo You may need to:
    echo 1. Install Python from https://python.org
    echo 2. Add Python to your PATH
    echo 3. Or use 'py' instead of 'python' in the config
)

echo.
pause