@echo off
REM Network Device MCP Server Installation Script

echo Installing Network Device Management MCP Server
echo ===============================================
echo.

REM Check Python installation - try multiple commands
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    echo ✓ Python found via 'python' command
    goto :python_found
)

py --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=py
    echo ✓ Python found via 'py' command
    goto :python_found
)

python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    echo ✓ Python found via 'python3' command
    goto :python_found
)

echo ❌ ERROR: Python is not installed or not in PATH
echo.
echo Please install Python 3.8+ from https://python.org/
echo Make sure to check "Add Python to PATH" during installation
echo.
echo Alternative: Install from Microsoft Store or use winget:
echo   winget install Python.Python.3.12
echo.
pause
exit /b 1

:python_found

REM Check if we're in the right directory
if not exist "src\main.py" (
    echo ❌ ERROR: Please run this script from the network-device-mcp-server directory
    echo Current directory: %CD%
    echo Expected files: src\main.py, requirements.txt
    pause
    exit /b 1
)

echo ✓ In correct directory

REM Create virtual environment
echo.
echo Creating Python virtual environment...
%PYTHON_CMD% -m venv venv
if %errorlevel% neq 0 (
    echo ❌ ERROR: Failed to create virtual environment
    echo.
    echo This might be because:
    echo 1. Python venv module is not installed
    echo 2. Insufficient permissions
    echo 3. Disk space issues
    echo.
    echo Try running: %PYTHON_CMD% -m pip install --user virtualenv
    pause
    exit /b 1
)

echo ✓ Virtual environment created

REM Activate virtual environment and install requirements
echo.
echo Installing Python dependencies...

REM Check which activation script to use
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else if exist "venv\bin\activate" (
    call venv\bin\activate
) else (
    echo ❌ ERROR: Could not find virtual environment activation script
    pause
    exit /b 1
)

python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo ⚠️  Warning: Could not upgrade pip, continuing...
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ ERROR: Failed to install Python dependencies
    echo.
    echo Try running manually:
    echo 1. venv\Scripts\activate.bat
    echo 2. pip install -r requirements.txt
    echo.
    echo If that fails, check your internet connection and try:
    echo pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt
    pause
    exit /b 1
)

echo ✓ Dependencies installed

REM Create necessary directories
echo.
echo Creating directories...
if not exist "logs" mkdir logs
if not exist "backups" mkdir backups  
if not exist "reports" mkdir reports
if not exist "power-automate-integration" mkdir power-automate-integration

echo ✓ Directories created

REM Copy configuration template
if not exist "config\devices.json.user" (
    copy "config\devices.json" "config\devices.json.user" >nul
    echo ✓ Configuration template copied to devices.json.user
)

REM Create a script to run the server
echo Creating run script...
(
echo @echo off
echo REM Network Device MCP Server Runner
echo call "%CD%\venv\Scripts\activate.bat"
echo %PYTHON_CMD% "%CD%\src\main.py" %%*
) > run-server.bat

echo ✓ Run script created: run-server.bat

echo.
echo ✅ Installation completed successfully!
echo.
echo 📁 What was installed:
echo   - Python virtual environment (venv/)
echo   - Required Python packages (MCP, httpx, etc.)
echo   - Configuration template (config/devices.json.user)
echo   - Directory structure (logs/, backups/, reports/)
echo   - Server runner script (run-server.bat)
echo.
echo 🚀 Next steps:
echo   1. Edit config\devices.json.user with your actual device credentials
echo   2. Run: setup-claude.bat (to add this server to Claude Desktop)
echo   3. Test: test-server.bat (to verify everything works)
echo   4. Restart Claude Desktop
echo.
echo 💡 Tips:
echo   - Use run-server.bat to manually start the server
echo   - Check logs/ folder for troubleshooting
echo   - See README.md for detailed documentation
echo.
echo ⚙️  Python command used: %PYTHON_CMD%
echo    (This will be used in Claude Desktop configuration)
echo.
pause