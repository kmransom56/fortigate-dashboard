@echo off
echo ========================================
echo   Network MCP Server - FULL ADOM INTEGRATION
echo ========================================
echo.

cd /d "C:\Users\keith.ransom\network-device-mcp-server"

echo 🎯 FULL ADOM INTEGRATION FEATURES:
echo    ✅ ADOM selector dropdowns in sidebar
echo    ✅ ADOM discovery buttons for each brand
echo    ✅ ADOM status badges and indicators
echo    ✅ Auto-discovery of best ADOMs on startup
echo    ✅ "View All Devices" buttons with ADOM support
echo    ✅ Real-time ADOM switching
echo    ✅ Enhanced brand sections with ADOM awareness
echo.

echo 📊 Starting FULL ADOM-INTEGRATED server...
echo.

rem Use the ADOM-enhanced version with new interface
venv\Scripts\python.exe src/rest_api_server_adom_support.py

pause
