@echo off
echo ========================================
echo   Network MCP Server - Environment Diagnosis
echo ========================================
echo.

echo 🔍 CHECKING PYTHON INSTALLATION...
echo.
echo Python in PATH:
where python 2>nul || echo ❌ Python not found in PATH
echo.
echo Python in virtual environment:
if exist "venv\Scripts\python.exe" (
    echo ✅ Python found in virtual environment
    echo Version:
    "venv\Scripts\python.exe" --version 2>nul || echo ❌ Virtual environment Python error
) else (
    echo ❌ Virtual environment not found or broken
)

echo.
echo 🔍 CHECKING NODE.JS INSTALLATION...
echo.
echo Node.js in PATH:
where node 2>nul || echo ❌ Node.js not found in PATH
echo.
echo NPM in PATH:
where npm 2>nul || echo ❌ NPM not found in PATH

echo.
echo 📦 CHECKING PROJECT FILES...
echo.
if exist "rest_api_server.py" (
    echo ✅ Python Flask server found
) else (
    echo ❌ Python Flask server missing
)

if exist "server_noc_fixed.js" (
    echo ✅ Node.js server found
) else (
    echo ❌ Node.js server missing
)

if exist "requirements.txt" (
    echo ✅ Python requirements file found
) else (
    echo ❌ Python requirements file missing
)

if exist "package.json" (
    echo ✅ Node.js package file found
) else (
    echo ❌ Node.js package file missing
)

echo.
echo 🌐 CHECKING PORTS...
echo.
echo Port 5000 (Python Flask):
netstat -ano | findstr ":5000" && echo ✅ Something is running on port 5000 || echo ❌ Nothing on port 5000
echo.
echo Port 5001 (Node.js):
netstat -ano | findstr ":5001" && echo ✅ Something is running on port 5001 || echo ❌ Nothing on port 5001

echo.
echo ========================================
echo 📋 RECOMMENDED ACTIONS:
echo ========================================
echo.

echo If Python not found in PATH:
echo 1. Install Python from python.org
echo 2. OR activate virtual environment:
echo    venv\Scripts\activate.bat
echo.
echo If Node.js not found:
echo 1. Install Node.js from nodejs.org
echo 2. OR use Python-only mode
echo.
echo If virtual environment broken:
echo 1. python -m venv venv
echo 2. venv\Scripts\activate.bat
echo 3. pip install -r requirements.txt
echo.
echo ========================================
pause