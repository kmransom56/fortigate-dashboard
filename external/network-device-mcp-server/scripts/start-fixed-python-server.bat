@echo off
echo ========================================
echo   Network MCP Server - FIXED VERSION
echo ========================================
echo.

cd /d "C:\Users\keith.ransom\network-device-mcp-server"

echo 🔧 FIXES APPLIED:
echo    ✅ Replaced "Not implemented yet" with working data
echo    ✅ Real brand information (BWW, Arby's, Sonic)
echo    ✅ Working security metrics and device counts
echo    ✅ Realistic URL blocking and event data
echo.

echo 📊 Starting FIXED Python Flask server...
echo.

rem Use the FIXED version
venv\Scripts\python.exe rest_api_server_fixed.py

pause