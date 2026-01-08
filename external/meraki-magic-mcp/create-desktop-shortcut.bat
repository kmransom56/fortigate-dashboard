@echo off
REM Desktop Shortcut Creator for Meraki Magic TUI
REM Handles paths with spaces properly

echo ========================================
echo Creating Meraki Magic TUI Shortcut
echo ========================================
echo.

REM Get the actual Desktop path
for /f "tokens=3*" %%i in ('reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders" /v Desktop') do set DESKTOP=%%j
REM Expand environment variables in path
call set DESKTOP=%DESKTOP%

echo Desktop path: %DESKTOP%
echo.

REM Create shortcut for Meraki Magic TUI with Chat
echo Creating shortcut: Meraki Magic Dashboard...
powershell -Command "$WS = New-Object -ComObject WScript.Shell; $SC = $WS.CreateShortcut('%DESKTOP%\Meraki Magic Dashboard.lnk'); $SC.TargetPath = '%~dp0launch-tui.bat'; $SC.WorkingDirectory = '%~dp0'; $SC.IconLocation = 'shell32.dll,165'; $SC.Description = 'Interactive Meraki Dashboard with AI Chat'; $SC.Save()"

if exist "%DESKTOP%\Meraki Magic Dashboard.lnk" (
    echo   [OK] Created: Meraki Magic Dashboard.lnk
) else (
    echo   [ERROR] Failed to create Meraki Magic shortcut
)

echo.
echo ========================================
echo Shortcut Created Successfully!
echo ========================================
echo.
echo Desktop shortcut:
echo   - Meraki Magic Dashboard.lnk
echo.
echo Features:
echo   - Browse all Meraki organizations
echo   - View networks, devices, clients
echo   - Chat interface for queries
echo   - Keyboard shortcuts (1-4)
echo.
echo Launch from your desktop!
echo.

pause
