@echo off
cd /d "%~dp0"
echo 🚀 Starting Network Device MCP Server...
echo ======================================

REM Check if Docker Desktop is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Desktop is not running.
    echo.
    echo Please start Docker Desktop and try again.
    echo.
    echo If Docker Desktop is not installed:
    echo 📥 Download from: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ❌ .env file not found.
    echo.
    echo Please run setup-auto-start.bat first to configure the application.
    pause
    exit /b 1
)

REM Start the container
echo 🔄 Starting container...
docker-compose up -d

if errorlevel 1 (
    echo ❌ Failed to start container.
    echo.
    echo 🔍 Check the error messages above.
    echo 📊 View logs with: docker-compose logs
    pause
    exit /b 1
)

REM Wait for service to be ready
echo ⏳ Waiting for service to start...
timeout /t 10 /nobreak >nul

REM Check if service is healthy
echo 🏥 Checking service health...
curl -f http://localhost:12000/health >nul 2>&1

if errorlevel 1 (
    echo ⚠️  Service health check failed.
    echo.
    echo The container may still be starting up.
    echo 🌐 Try accessing: http://localhost:12000
    echo 📊 Check logs: docker-compose logs
    echo 🔄 Check status: docker-compose ps
    echo.
    echo If the service doesn't start, check your .env file credentials.
) else (
    echo ✅ Service is healthy!
)

echo.
echo 🎉 Network Device MCP Server is running!
echo ========================================
echo 🌐 Web Interface: http://localhost:12000
echo 📊 API Documentation: http://localhost:12000/api
echo 🏥 Health Check: http://localhost:12000/health
echo.
echo 🔍 Test ADOM Discovery:
echo   curl http://localhost:12000/api/fortimanager/bww/adoms
echo   curl http://localhost:12000/api/fortimanager/arbys/adoms
echo   curl http://localhost:12000/api/fortimanager/sonic/adoms
echo.
echo 📝 Your team can now access the application at:
echo   http://localhost:12000
echo.
echo 🛑 To stop the server:
echo   Press any key to stop and exit
echo   OR run: docker-compose down
echo.

REM Wait for user to press key
pause >nul

REM Stop the container
echo 🛑 Stopping Network Device MCP Server...
docker-compose down

echo ✅ Server stopped successfully.
pause
