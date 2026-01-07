@echo off
echo 🚀 Setting up Network Device MCP Server Auto-Start...
echo ===================================================

REM Check if Docker Desktop is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Desktop is not installed.
    echo 📥 Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/
    echo.
    echo After installation, run this script again to set up auto-start.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from template...
    copy .env.docker .env
    echo ✅ Created .env file from template.
    echo.
    echo 📝 IMPORTANT: Please edit the .env file with your FortiManager credentials:
    echo    - FMG_IP=your-fortimanager-ip
    echo    - FMG_USERNAME=your-username
    echo    - FMG_PASSWORD=your-password
    echo.
    echo After editing .env, run this script again.
    notepad .env
    pause
    exit /b 1
)

REM Build the Docker image
echo 🔨 Building Docker image...
docker-compose build

if errorlevel 1 (
    echo ❌ Failed to build Docker image.
    echo Please check the Docker build output for errors.
    pause
    exit /b 1
)

REM Test the container
echo 🧪 Testing container startup...
docker-compose up -d

REM Wait for service to be ready
echo ⏳ Waiting for service to start...
timeout /t 15 /nobreak >nul

REM Check if service is healthy
curl -f http://localhost:12000/health >nul 2>&1
if errorlevel 1 (
    echo ❌ Service health check failed.
    echo.
    echo 🔍 Troubleshooting steps:
    echo 1. Check Docker Desktop is running
    echo 2. Check .env file has correct credentials
    echo 3. View logs: docker-compose logs
    echo 4. Check status: docker-compose ps
    echo.
    docker-compose logs
    pause
    exit /b 1
)

echo ✅ Container is running successfully!

REM Stop the test container
echo 🛑 Stopping test container...
docker-compose down

REM Create startup batch file
echo 📝 Creating startup batch file...
(
    echo @echo off
    echo cd /d "%~dp0"
    echo echo Starting Network Device MCP Server...
    echo docker-compose up -d
    echo timeout /t 5 /nobreak ^>nul
    echo echo Network Device MCP Server is running at: http://localhost:12000
    echo echo Press any key to stop the server...
    echo pause ^>nul
    echo docker-compose down
) > "start-server.bat"

echo ✅ Created start-server.bat

REM Create desktop shortcut
echo 📌 Creating desktop shortcut...
set "shortcut_path=%USERPROFILE%\Desktop\Network Device MCP Server.lnk"
set "target_path=%~dp0start-server.bat"
set "working_dir=%~dp0"

powershell -Command "
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('%shortcut_path%')
$Shortcut.TargetPath = '%target_path%'
$Shortcut.WorkingDirectory = '%working_dir%'
$Shortcut.IconLocation = 'cmd.exe,0'
$Shortcut.Description = 'Start Network Device MCP Server'
$Shortcut.Save()
"

if exist "%shortcut_path%" (
    echo ✅ Desktop shortcut created successfully!
) else (
    echo ⚠️  Could not create desktop shortcut automatically.
    echo You can manually create a shortcut to: %~dp0start-server.bat
)

echo.
echo 🎉 SETUP COMPLETE!
echo ==================
echo.
echo 🚀 To start the server:
echo    Option 1: Double-click the desktop shortcut
echo    Option 2: Run: docker-compose up -d
echo    Option 3: Run: .\start-server.bat
echo.
echo 🌐 Access the application at: http://localhost:12000
echo.
echo 📝 Configuration:
echo    - Edit .env file with your FortiManager credentials
echo    - The server will auto-start with Docker Desktop
echo    - Logs are saved to the ./logs directory
echo.
echo 🛑 To stop the server:
echo   docker-compose down
echo.
echo 💡 PowerShell Note:
echo   If you get a "command not found" error, use:
echo   .\start-server.bat
echo   .\setup-auto-start.bat
echo.
echo ✅ Your Network Device MCP Server is ready for your team!
echo.

pause
