@echo off
REM Network Device Management Web Dashboard Launcher
REM For Team Access to MCP Server

echo ======================================================
echo    Network Device Management Web Dashboard
echo ======================================================
echo.
echo This will start a web interface that your team can use
echo to investigate stores, monitor security, and analyze
echo network devices across all restaurant brands.
echo.
echo Features:
echo  * Store Investigation Tool
echo  * Real-time Security Monitoring  
echo  * BWW, Arby's, Sonic Brand Dashboards
echo  * FortiManager Status
echo  * URL Blocking Analysis
echo  * Security Health Assessments
echo.

:check_environment
echo Checking environment...

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERROR: Virtual environment not found.
    echo.
    echo Please run install.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

REM Check if Flask is installed
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Checking Flask installation...
python -c "import flask" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Flask not found, installing...
    pip install flask flask-cors
    if %errorlevel% neq 0 (
        echo ❌ ERROR: Failed to install Flask
        pause
        exit /b 1
    )
    echo ✅ Flask installed successfully
)

echo Checking MCP server dependencies...
python -c "import mcp" 2>nul
if %errorlevel% neq 0 (
    echo ❌ ERROR: MCP package not installed
    echo Run install.bat to install dependencies
    pause
    exit /b 1
)

:start_server
echo.
echo ======================================================
echo Starting Web Dashboard Server...
echo ======================================================
echo.
echo 🌐 Dashboard will be available at: http://localhost:5000
echo 📊 Your team can access it from any browser
echo 🔄 The server will auto-reload when you make changes
echo.
echo Press Ctrl+C to stop the server
echo.

REM Set environment variables for better Flask experience
set FLASK_ENV=development
set FLASK_DEBUG=1

REM Start the web dashboard server
python rest_api_server.py

echo.
echo ======================================================
echo Server stopped
echo ======================================================
echo.
pause