@echo off
REM Network Device MCP Server - Usage Examples
REM Choose how to run your MCP server without Claude Desktop

echo Network Device MCP Server - Usage Options
echo ==========================================
echo.

:menu
echo Choose an option:
echo.
echo 1. Direct Python Client (Recommended)
echo 2. REST API Server (Web/HTTP access)
echo 3. Command Line Interface (CLI)
echo 4. Show usage examples
echo 5. Exit
echo.
set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto python_client
if "%choice%"=="2" goto rest_api
if "%choice%"=="3" goto cli
if "%choice%"=="4" goto examples
if "%choice%"=="5" goto exit
goto menu

:python_client
echo.
echo Starting Direct Python Client...
echo ================================
echo.
echo This will run Python scripts that call MCP tools directly.
echo No message limits, full access to all tools.
echo.
call venv\Scripts\activate.bat
python direct_mcp_client.py
pause
goto menu

:rest_api
echo.
echo Starting REST API Server...
echo ===========================
echo.
echo This creates HTTP endpoints for your MCP tools.
echo Access via web browser or HTTP clients.
echo.
echo Installing Flask if needed...
call venv\Scripts\activate.bat
pip install flask flask-cors
echo.
echo Starting server at http://localhost:5000
python rest_api_server.py
pause
goto menu

:cli
echo.
echo Command Line Interface Examples...
echo ==================================
echo.
call venv\Scripts\activate.bat
echo.
echo Example: List supported brands
python mcp_cli.py brands
echo.
echo Example: Investigate BWW Store 155
python mcp_cli.py investigate BWW 155
echo.
pause
goto menu

:examples
echo.
echo Usage Examples:
echo ===============
echo.
echo 1. DIRECT PYTHON:
echo    python direct_mcp_client.py
echo    # Then modify the script to investigate specific stores
echo.
echo 2. REST API (after starting server):
echo    http://localhost:5000/api/brands
echo    http://localhost:5000/api/stores/bww/155/security
echo    http://localhost:5000/api/stores/arbys/1234/url-blocking
echo.
echo 3. COMMAND LINE:
echo    python mcp_cli.py brands
echo    python mcp_cli.py security BWW 155
echo    python mcp_cli.py blocking ARBYS 1234 --period 7d
echo    python mcp_cli.py investigate SONIC 789
echo.
echo 4. POWER AUTOMATE INTEGRATION:
echo    Use REST API endpoints in Power Automate HTTP actions
echo    Reports automatically saved to C:\temp\network-reports\
echo.
pause
goto menu

:exit
echo.
echo Goodbye!
exit /b 0