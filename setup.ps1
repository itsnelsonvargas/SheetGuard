Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host ""
Write-Host "========================================"
Write-Host "  SheetGuard - First-time setup"
Write-Host "========================================"
Write-Host ""

function Test-Python310 {
    param([string[]]$LaunchArgs)
    & @LaunchArgs -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Find-Python {
    if ((Get-Command py -ErrorAction SilentlyContinue) -and (Test-Python310 @("py", "-3"))) {
        return @("py", "-3")
    }
    if ((Get-Command python -ErrorAction SilentlyContinue) -and (Test-Python310 @("python"))) {
        return @("python")
    }
    return $null
}

$pythonCmd = Find-Python

if (-not $pythonCmd) {
    Write-Host "Python 3.10+ was not found on this PC."
    Write-Host ""

    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "winget is not available on this PC."
        Write-Host ""
        Write-Host "Please install Python 3.10 or newer manually:"
        Write-Host "  https://www.python.org/downloads/"
        Write-Host ""
        Write-Host 'During installation, check "Add python.exe to PATH".'
        Write-Host "Then run setup.ps1 again."
        Read-Host "Press Enter to exit"
        exit 1
    }

    Write-Host "Installing Python 3.12 via winget (this may take a few minutes)..."
    winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ERROR: winget could not install Python."
        Write-Host ""
        Write-Host "Please install Python 3.10 or newer manually:"
        Write-Host "  https://www.python.org/downloads/"
        Read-Host "Press Enter to exit"
        exit 1
    }

    $env:PATH = "$env:LOCALAPPDATA\Programs\Python\Python312;$env:LOCALAPPDATA\Programs\Python\Python312\Scripts;$env:PATH"
    $pythonCmd = Find-Python

    if (-not $pythonCmd) {
        Write-Host ""
        Write-Host "Python was installed but is not available in this window yet."
        Write-Host "Close this window, open a new one, and run setup.ps1 again."
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ("Using: " + ($pythonCmd -join " "))
Write-Host ""

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
    Write-Host "Virtual environment already exists - updating dependencies..."
} else {
    Write-Host "Creating virtual environment in .venv ..."
    & @pythonCmd -m venv .venv
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r requirements.txt

Write-Host ""
Write-Host "========================================"
Write-Host "  Setup complete!"
Write-Host "  Double-click run.bat to start SheetGuard."
Write-Host "========================================"
Write-Host ""
Read-Host "Press Enter to exit"
