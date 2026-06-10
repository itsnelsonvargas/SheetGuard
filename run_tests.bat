@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Running setup first...
    call "%~dp0setup.bat"
    if errorlevel 1 exit /b 1
)

.venv\Scripts\python.exe -m pip install -r requirements.txt -q --disable-pip-version-check
.venv\Scripts\python.exe -m pytest tests --verbose
pause
