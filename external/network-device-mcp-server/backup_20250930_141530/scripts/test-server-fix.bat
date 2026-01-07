@echo off
echo ========================================
echo   Testing Network MCP Server Fix
echo ========================================
echo.

echo 🧪 Running server connectivity tests...
echo.

echo 📊 Test 1: Python Flask Server (port 5000)
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:5000/health' -TimeoutSec 5; Write-Host '✅ Python server: ' $response.status -ForegroundColor Green } catch { Write-Host '❌ Python server: Not responding' -ForegroundColor Red }"

echo.
echo 🌐 Test 2: Node.js Proxy Server (port 5001)  
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:5001/health' -TimeoutSec 5; Write-Host '✅ Node server: ' $response.status -ForegroundColor Green } catch { Write-Host '❌ Node server: Not responding' -ForegroundColor Red }"

echo.
echo 📡 Test 3: API Proxy Test (through Node.js to Python)
powershell -Command "try { $response = Invoke-RestMethod -Uri 'http://localhost:5001/api/brands' -TimeoutSec 10; Write-Host '✅ API proxy: Working' -ForegroundColor Green } catch { Write-Host '❌ API proxy: Failed' -ForegroundColor Red }"

echo.
echo 🔍 Test 4: Web Interface Files
if exist "web\templates\index_noc_style.html" (
    echo ✅ Web interface: Files found
) else (
    echo ❌ Web interface: Missing files
)

echo.
echo ========================================
echo 📋 If tests fail:
echo 1. Run start-fixed-servers.bat first
echo 2. Wait 10 seconds for full startup
echo 3. Check for Python/Node.js installation
echo 4. Run this test again
echo ========================================
echo.
pause