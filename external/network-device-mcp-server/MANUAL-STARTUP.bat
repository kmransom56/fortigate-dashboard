@echo off
echo =================================================
echo   Network Management Platform - MANUAL STARTUP
echo =================================================
echo.
echo This script will manually start the full application.
echo It ensures the environment is active and stops any old processes
echo before launching the main application in a new window.
echo.

echo 📋 STEP 1: Check Virtual Environment
if exist "venv\Scripts\activate.bat" (
    echo ✅ Virtual environment found.
) else (
    echo ❌ Virtual environment not found. Please run COMPLETE-SETUP.bat first.
    pause
    exit /b 1
)

echo.
echo 📋 STEP 2: Activate Virtual Environment
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated.

echo.
echo 📋 STEP 3: Kill Existing Processes
echo Stopping any running Python processes to ensure a clean start...
taskkill /f /im python.exe 2>nul
echo ✅ Stale processes stopped.

echo.
echo 📋 STEP 4: Starting the Application...
echo ========================================
echo 🚀 Launching the platform...
echo ========================================
echo.
echo The application will now start in a new window.
echo You can access the web dashboard at http://localhost:5000
echo.

start "Network Management Platform" cmd /c start-full-adom-integration.bat

echo.
echo =================================================================
echo ✅ Startup command has been issued.
echo Please check the new window for application logs and status.
echo =================================================================
echo.
pause