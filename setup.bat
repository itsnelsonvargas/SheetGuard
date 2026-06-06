@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo ========================================
echo   SheetGuard - First-time setup
echo ========================================
echo.

call :find_python
if errorlevel 1 goto :install_python
goto :create_venv

:install_python
echo Python 3.10+ was not found on this PC.
echo.

where winget >nul 2>&1
if errorlevel 1 goto :no_winget

echo Installing Python 3.12 via winget (this may take a few minutes)...
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
if errorlevel 1 (
    echo.
    echo ERROR: winget could not install Python.
    goto :manual_install
)

REM winget installs to a user folder; add common paths for this session
set "PATH=%LocalAppData%\Programs\Python\Python312;%LocalAppData%\Programs\Python\Python312\Scripts;%PATH%"

call :find_python
if errorlevel 1 (
    echo.
    echo Python was installed but is not available in this window yet.
    echo Close this window, open a new one, and run setup.bat again.
    pause
    exit /b 1
)
goto :create_venv

:no_winget
echo winget is not available on this PC.
goto :manual_install

:manual_install
echo.
echo Please install Python 3.10 or newer manually:
echo   https://www.python.org/downloads/
echo.
echo During installation, check "Add python.exe to PATH".
echo Then run setup.bat again.
pause
exit /b 1

:create_venv
echo Using: %PYTHON_CMD%
echo.

if exist ".venv\Scripts\python.exe" (
    echo Virtual environment already exists - updating dependencies...
) else (
    echo Creating virtual environment in .venv ...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
)

echo Installing dependencies from requirements.txt ...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Could not install dependencies.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Setup complete!
echo   Double-click run.bat to start SheetGuard.
echo ========================================
echo.
pause
exit /b 0

:find_python
set "PYTHON_CMD="
where py >nul 2>&1 && (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>nul && set "PYTHON_CMD=py -3"
)
if defined PYTHON_CMD exit /b 0

where python >nul 2>&1 && (
    python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>nul && set "PYTHON_CMD=python"
)
if defined PYTHON_CMD exit /b 0

exit /b 1
