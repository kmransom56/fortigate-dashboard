@echo off
echo =============================================
echo  FortiGate Dashboard Development Environment
echo =============================================
echo.

REM Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found. Using system Python.
)

echo.
echo Starting development file watcher...
echo.

python tools\watch_dev.py

pause
