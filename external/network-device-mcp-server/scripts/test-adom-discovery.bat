@echo off
echo ========================================
echo   ADOM Discovery and Testing Tool
echo ========================================
echo.

echo 🔍 This will help you find the correct ADOMs for your FortiManager instances
echo    and test the new device listing functionality.
echo.

set SERVER_URL=http://localhost:5000

echo 📡 Testing server health...
powershell -Command "try { $response = Invoke-RestMethod -Uri '%SERVER_URL%/health' -TimeoutSec 5; Write-Host '✅ Server is running' -ForegroundColor Green } catch { Write-Host '❌ Server not running - start it first!' -ForegroundColor Red; pause; exit }"

echo.
echo 🏢 DISCOVERING ADOMs for each brand...
echo.

echo 🍗 BWW FortiManager ADOM Discovery:
powershell -Command "$response = Invoke-RestMethod -Uri '%SERVER_URL%/api/fortimanager/bww/adoms'; $response | ConvertTo-Json -Depth 3"

echo.
echo 🥪 ARBY'S FortiManager ADOM Discovery:  
powershell -Command "$response = Invoke-RestMethod -Uri '%SERVER_URL%/api/fortimanager/arbys/adoms'; $response | ConvertTo-Json -Depth 3"

echo.
echo 🍔 SONIC FortiManager ADOM Discovery:
powershell -Command "$response = Invoke-RestMethod -Uri '%SERVER_URL%/api/fortimanager/sonic/adoms'; $response | ConvertTo-Json -Depth 3"

echo.
echo ========================================
echo 📋 BASED ON RESULTS ABOVE:
echo 1. Look for ADOMs with HIGH device counts (1000+)
echo 2. Use those ADOMs in your API calls
echo 3. Test with: %SERVER_URL%/api/fortimanager/bww/devices?adom=CORRECT_ADOM
echo ========================================
echo.

echo 🧪 TESTING DEFAULT DEVICE LISTING (first 50):
echo.

echo BWW devices (default ADOM):
powershell -Command "$response = Invoke-RestMethod -Uri '%SERVER_URL%/api/fortimanager/bww/devices?limit=5'; Write-Host \"Total devices: $($response.total_devices)\" -ForegroundColor Yellow; Write-Host \"Showing: $($response.showing_devices)\" -ForegroundColor Yellow"

echo.
echo ARBYS devices (default ADOM):  
powershell -Command "$response = Invoke-RestMethod -Uri '%SERVER_URL%/api/fortimanager/arbys/devices?limit=5'; Write-Host \"Total devices: $($response.total_devices)\" -ForegroundColor Yellow; Write-Host \"Showing: $($response.showing_devices)\" -ForegroundColor Yellow"

echo.
echo SONIC devices (default ADOM):
powershell -Command "$response = Invoke-RestMethod -Uri '%SERVER_URL%/api/fortimanager/sonic/devices?limit=5'; Write-Host \"Total devices: $($response.total_devices)\" -ForegroundColor Yellow; Write-Host \"Showing: $($response.showing_devices)\" -ForegroundColor Yellow"

echo.
echo ========================================
echo 🎯 NEXT STEPS:
echo 1. Note which ADOM has the most devices for each brand
echo 2. Update your web interface to use those ADOMs
echo 3. Test with: /api/fortimanager/BRAND/devices?adom=CORRECT_ADOM
echo 4. For all devices: /api/fortimanager/BRAND/devices?adom=CORRECT_ADOM (no limit)
echo 5. For pagination: /api/fortimanager/BRAND/devices?adom=CORRECT_ADOM&limit=100&offset=0
echo ========================================
echo.
pause