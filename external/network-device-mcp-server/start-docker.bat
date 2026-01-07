@echo off
echo 🐳 Starting Network Device MCP Server with Docker...
echo =================================================

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from template...
    copy .env.docker .env
    echo ✅ Created .env file from template.
    echo 📝 Please edit .env file with your FortiManager credentials before running again.
    echo.
    echo Required settings in .env:
    echo   FMG_IP=your-fortimanager-ip
    echo   FMG_USERNAME=your-username
    echo   FMG_PASSWORD=your-password
    pause
    exit /b 1
)

REM Build and start the container
echo 🔨 Building Docker image...
docker-compose build

echo 🚀 Starting Network Device MCP Server...
docker-compose up -d

REM Wait for service to be ready
echo ⏳ Waiting for service to start...
timeout /t 10 /nobreak >nul

REM Check if service is healthy
curl -f http://localhost:12000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Service health check failed.
    echo 📊 Check logs with: docker-compose logs
    echo 🔍 Check status with: docker-compose ps
    pause
    exit /b 1
)

echo.
echo 🎉 SUCCESS! Network Device MCP Server is running!
echo =================================================
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
echo   docker-compose down
echo.
pause
