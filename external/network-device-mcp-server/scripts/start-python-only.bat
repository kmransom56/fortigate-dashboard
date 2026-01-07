@echo off
echo ========================================
echo   Starting Network MCP Server
echo ========================================
echo.

cd /d "C:\Users\keith.ransom\network-device-mcp-server"

echo 📊 Starting Python Flask server...
echo.

rem Use the virtual environment Python
venv\Scripts\python.exe rest_api_server.py

pause