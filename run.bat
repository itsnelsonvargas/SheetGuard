@echo off
cd /d "%~dp0"
echo Installing dependencies (if needed)...
py -3 -m pip install -r requirements.txt
if errorlevel 1 (
    python -m pip install -r requirements.txt
)
echo Starting SheetGuard...
py -3 main.py
if errorlevel 1 python main.py
pause
