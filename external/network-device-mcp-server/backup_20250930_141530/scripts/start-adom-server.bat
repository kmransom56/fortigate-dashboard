@echo off
echo ========================================
echo   Network MCP Server - ADOM SUPPORT
echo ========================================
echo.

cd /d "C:\Users\keith.ransom\network-device-mcp-server"

echo 🎯 NEW ADOM FEATURES:
echo    ✅ ADOM selection and discovery
echo    ✅ Full device listing (no 10-device limit)  
echo    ✅ Pagination for thousands of devices
echo    ✅ Real FortiManager integration
echo.

echo 📊 Starting ADOM-enabled server...
echo.

rem Use the new ADOM-enabled version
venv\Scripts\python.exe rest_api_server_adom_support.py

pause