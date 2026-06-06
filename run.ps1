Set-Location $PSScriptRoot

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "SheetGuard is not set up on this machine yet."
    Write-Host ""
    Write-Host "Run setup.ps1 first (one-time setup), then run this script again."
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Starting SheetGuard..."
& $venvPython main.py
