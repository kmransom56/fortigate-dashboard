@echo off
echo ========================================
echo   Network MCP Server - Fixed Version
echo ========================================
echo.

echo 🔧 ISSUE FIXED:
echo    - Missing http-proxy-middleware dependency
echo    - Created simplified proxy server
echo    - No external dependencies needed
echo.

echo 🚀 STARTING SERVERS...
echo.

echo 📊 Starting Python Flask server (Backend API)...
start "Python API Server" cmd /k "cd /d "%~dp0" && python rest_api_server.py"

echo ⏳ Waiting 3 seconds for Python server to start...
timeout /t 3 /nobreak > nul

echo 🌐 Starting Node.js server (Frontend Interface)...
start "Node.js Frontend" cmd /k "cd /d "%~dp0" && node server_noc_fixed.js"

echo.
echo ========================================
echo ✅ SERVERS STARTING!
echo ========================================
echo 🌐 Web Interface: http://localhost:5001
echo 📊 API Backend:   http://localhost:5000  
echo 🔧 Health Check:  http://localhost:5001/health
echo ========================================
echo.
echo 📋 Next Steps:
echo 1. Wait for both servers to fully start
echo 2. Open http://localhost:5001 in your browser
echo 3. Test voice controls and API endpoints
echo.
pause