@echo off
echo =========================================================
echo  Voice-Enabled Network Management Platform - NOC Style
echo =========================================================
echo.

echo Installing Node.js dependencies...
call npm install
echo.

echo Starting NOC-Style Platform...
echo.
echo Python Backend: http://localhost:5000 (Flask)
echo Node.js Frontend: http://localhost:5001 (NOC Interface)  
echo.

echo Press Ctrl+C to stop both servers
echo.

:: Start both servers concurrently
start /B python rest_api_server.py
timeout /t 3 /nobreak > nul
start /B node server_noc_style.js

echo =========================================================
echo  Platform Started Successfully!
echo.
echo  🌐 NOC Dashboard: http://localhost:5001
echo  📊 Original Dashboard: http://localhost:5000  
echo  🔧 Health Check: http://localhost:5001/health
echo =========================================================
echo.

pause