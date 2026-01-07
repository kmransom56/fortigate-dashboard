@echo off
echo.
echo ========================================================================
echo   🚀 Network Device Management - One-Click Docker Setup
echo ========================================================================
echo.
echo This will start your complete network device management system:
echo   - FastAPI Backend Server    (http://localhost:8000)
echo   - Web Dashboard            (http://localhost:12000) 
echo   - Health monitoring and logging
echo.
echo Requirements: Docker Desktop must be installed and running
echo.
pause

echo.
echo 📋 Checking Docker installation...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed or not running
    echo.
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    echo Then restart this script.
    pause
    exit /b 1
)

docker compose version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not available
    echo Please update Docker Desktop to the latest version
    pause
    exit /b 1
)

echo ✅ Docker is ready!
echo.

echo 🏗️  Building and starting containers...
echo This may take a few minutes on first run...
echo.

docker compose -f docker-compose.production.yml up --build -d

if errorlevel 1 (
    echo.
    echo ❌ Failed to start containers
    echo Check the error messages above and try again
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo   ✅ SUCCESS! Your Network Device Management System is running
echo ========================================================================
echo.
echo 🌐 Web Dashboard:      http://localhost:12000
echo 🔧 FastAPI Backend:    http://localhost:8000
echo 📖 API Documentation:  http://localhost:8000/docs
echo.
echo 🔍 To view logs:       docker compose -f docker-compose.production.yml logs -f
echo 🛑 To stop:           docker compose -f docker-compose.production.yml down
echo 📊 To view status:     docker compose -f docker-compose.production.yml ps
echo.
echo Opening dashboard in your default browser...
timeout /t 3 /nobreak >nul
start http://localhost:12000

echo.
echo Press any key to open the logs view, or close this window to continue...
pause
docker compose -f docker-compose.production.yml logs -f