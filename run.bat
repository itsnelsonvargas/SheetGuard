@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo SheetGuard is not set up on this machine yet.
    echo.
    echo Run setup.bat first ^(one-time setup^), then run this script again.
    echo.
    pause
    exit /b 1
)

echo Installing dependencies (if needed)...
.venv\Scripts\python.exe -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Could not install dependencies. Run setup.bat again.
    pause
    exit /b 1
)

echo Starting SheetGuard...
.venv\Scripts\python.exe main.py
if errorlevel 1 pause
