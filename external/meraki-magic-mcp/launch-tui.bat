@echo off
REM Meraki Magic TUI Launcher
REM Interactive dashboard for Meraki network management

echo ========================================
echo   Meraki Magic TUI Dashboard
echo   Multi-Organization Management
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: uv venv
    pause
    exit /b 1
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if textual is installed
python -c "import textual" 2>nul
if errorlevel 1 (
    echo Installing required dependencies...
    uv pip install textual python-dotenv
)

REM Launch TUI
echo Starting dashboard...
echo.
python meraki_tui.py

pause
