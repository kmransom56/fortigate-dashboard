@echo off
REM Configuration Validator for Network Device MCP Server

echo Network Device MCP Server - Configuration Validator
echo =====================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERROR: Virtual environment not found.
    echo Please run install.bat first.
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ❌ ERROR: .env file not found!
    echo.
    echo Please create your .env file:
    echo 1. Copy .env.template to .env
    echo 2. Edit .env with your actual credentials:
    echo    - FortiManager passwords for Arbys/BWW/Sonic
    echo    - Meraki API key and organization ID
    echo 3. Run this validator again
    echo.
    if exist ".env.template" (
        echo Opening .env.template for reference...
        notepad .env.template
    )
    pause
    exit /b 1
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Testing your FortiManager and Meraki configuration...
echo This will validate credentials and test connections.
echo.

REM Run the Python validator
python validate-config.py

echo.
echo Validation complete!
echo.

if %errorlevel% neq 0 (
    echo ❌ Some issues were found. Please check the output above.
) else (
    echo ✅ Configuration looks good!
)

echo.
echo 💡 Tips for next steps:
echo - If validation passed: Restart Claude Desktop and test
echo - If connections failed: Check network access to FortiManagers
echo - If auth failed: Verify usernames/passwords in .env file
echo.

pause
