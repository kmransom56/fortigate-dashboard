@echo off
echo.
echo ========================================================================
echo   🛑 Stopping Network Device Management System
echo ========================================================================
echo.

docker compose -f docker-compose.production.yml down

echo.
echo ✅ All containers stopped and removed
echo.
echo To start again, run: ONE-CLICK-START.bat
echo.
pause