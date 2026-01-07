<#!
.SYNOPSIS
  Activates the project virtual environment automatically and optionally runs a command.

.EXAMPLE
  ./activate_venv.ps1
  Activates .venv and drops into an interactive shell.

.EXAMPLE
  ./activate_venv.ps1 -Run "pytest -q"
  Activates .venv then runs pytest.
#>
param(
    [string]$Run = ''
)

$ErrorActionPreference = 'Stop'

$venvPath = Join-Path $PSScriptRoot '.venv'
$activateScript = Join-Path $venvPath 'Scripts/Activate.ps1'

if (-not (Test-Path $activateScript)) {
    Write-Host "[INFO] Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv $venvPath
    if ($LASTEXITCODE -ne 0) { throw "Failed to create virtual environment" }
    Write-Host "[OK] Virtual environment created." -ForegroundColor Green
    & $activateScript
    python -m ensurepip --upgrade | Out-Null
    python -m pip install --upgrade pip | Out-Null
    if (Test-Path (Join-Path $PSScriptRoot 'requirements.txt')) {
        Write-Host "[INFO] Installing dependencies from requirements.txt" -ForegroundColor Yellow
        pip install -r requirements.txt
    }
} else {
    & $activateScript
}

Write-Host "[VENV] Active: $([System.Environment]::GetEnvironmentVariable('VIRTUAL_ENV'))" -ForegroundColor Cyan

if ($Run) {
    Write-Host "[RUN] $Run" -ForegroundColor Magenta
    Invoke-Expression $Run
} else {
    Write-Host "Type 'deactivate' to exit the virtual environment." -ForegroundColor Gray
}
