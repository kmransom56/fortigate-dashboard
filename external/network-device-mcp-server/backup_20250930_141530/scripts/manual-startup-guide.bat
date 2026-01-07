@echo off
echo ========================================
echo   Network MCP Server - MANUAL STARTUP
echo ========================================
echo.
echo STEP 1: Open TWO Command Prompt windows
echo.
echo STEP 2: In FIRST window, run:
echo    cd "C:\Users\keith.ransom\network-device-mcp-server"
echo    venv\Scripts\python.exe rest_api_server.py
echo.
echo STEP 3: In SECOND window, run:
echo    cd "C:\Users\keith.ransom\network-device-mcp-server"
echo    node server_noc_fixed.js
echo.
echo STEP 4: Access your platform:
echo    http://localhost:5001 (Full interface)
echo    http://localhost:5000 (API only)
echo.
echo ========================================
echo If you don't have Node.js installed:
echo 1. Just run the Python server (STEP 2 only)
echo 2. Use http://localhost:5000 directly
echo ========================================
echo.
echo Press any key to open first command prompt...
pause > nul

start cmd /k "cd /d "C:\Users\keith.ransom\network-device-mcp-server" && echo Ready for: venv\Scripts\python.exe rest_api_server.py"

echo.
echo Press any key to open second command prompt...
pause > nul

start cmd /k "cd /d "C:\Users\keith.ransom\network-device-mcp-server" && echo Ready for: node server_noc_fixed.js"

echo.
echo ✅ Both command prompts opened!
echo Follow the instructions in each window.
echo.
pause