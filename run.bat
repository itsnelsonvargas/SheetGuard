@echo off
cd /d "%~dp0"

REM Prefer PowerShell launcher (auto-runs setup when needed)
where powershell >nul 2>&1
if not errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run.ps1" -NonInteractive
    exit /b %ERRORLEVEL%
)

REM Batch fallback
if not exist ".venv\Scripts\python.exe" (
    echo SheetGuard is not set up on this machine yet.
    echo Running setup.bat ...
    echo.
    call "%~dp0setup.bat"
    if errorlevel 1 exit /b 1
)

echo Installing dependencies (if needed)...
.venv\Scripts\python.exe -m pip install -r requirements.txt -q --disable-pip-version-check
if errorlevel 1 (
    echo ERROR: Could not install dependencies. Run setup.bat again.
    pause
    exit /b 1
)

echo Starting SheetGuard...
.venv\Scripts\python.exe main.py
if errorlevel 1 pause
