@echo off
echo ========================================
echo   Network MCP Server - Manual Startup
echo ========================================
echo.

echo 🛑 Killing any existing Python processes...
taskkill /f /im python.exe 2>nul
echo.

echo ⏳ Waiting 2 seconds...
timeout /t 2 /nobreak >nul
echo.

echo 🐍 Starting Python Flask Server (Backend)...
echo    Expected URL: http://localhost:5000
echo.

cd /d "C:\Users\keith.ransom\network-device-mcp-server"

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting Flask server with verbose output...
python rest_api_server.py

pause