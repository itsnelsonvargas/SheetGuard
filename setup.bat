@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

echo.
echo ========================================
echo   SheetGuard - First-time setup
echo ========================================
echo.

REM Primary path: PowerShell setup (richest fallbacks)
where powershell >nul 2>&1
if not errorlevel 1 (
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
    set "SETUP_EXIT=!ERRORLEVEL!"
    if !SETUP_EXIT! equ 0 exit /b 0
    echo.
    echo PowerShell setup did not finish successfully.
    echo Trying batch fallback...
    echo.
)

call :batch_setup
exit /b %ERRORLEVEL%

:batch_setup
call :find_python
if errorlevel 1 goto :install_python
goto :create_venv

:install_python
echo Python 3.10+ was not found on this PC.
echo.

where winget >nul 2>&1
if errorlevel 1 goto :download_python

echo Installing Python 3.12 via winget...
winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
if errorlevel 1 goto :download_python

call :refresh_python_path
call :find_python
if not errorlevel 1 goto :create_venv
echo.
echo Python was installed but is not available in this window yet.
echo Close this window, open a new one, and run setup.bat again.
pause
exit /b 1

:download_python
echo Trying direct Python installer download...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$url='https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe';" ^
  "$dst=Join-Path $env:TEMP 'sheetguard-python-installer.exe';" ^
  "try { Invoke-WebRequest -Uri $url -OutFile $dst -UseBasicParsing;" ^
  "  $p=Start-Process -FilePath $dst -ArgumentList '/quiet','InstallAllUsers=0','PrependPath=1','Include_pip=1','Include_launcher=1' -Wait -PassThru;" ^
  "  exit $p.ExitCode } catch { exit 1 }"
if errorlevel 1 goto :manual_install

call :refresh_python_path
call :find_python
if not errorlevel 1 goto :create_venv
goto :manual_install

:manual_install
echo.
echo Automatic Python installation did not succeed.
echo.
echo Install Python 3.10 or newer manually:
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
    .venv\Scripts\python.exe -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>nul
    if errorlevel 1 (
        echo Removing broken virtual environment...
        rmdir /s /q ".venv" 2>nul
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo Virtual environment found - verifying dependencies...
)

set "ATTEMPT=0"
:install_deps
set /a ATTEMPT+=1
echo Installing dependencies (attempt !ATTEMPT! of 3)...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt --default-timeout=120
if not errorlevel 1 goto :verify_setup
if !ATTEMPT! lss 3 (
    echo Dependency install failed. Retrying...
    timeout /t 5 /nobreak >nul
    goto :install_deps
)
echo ERROR: Could not install dependencies.
pause
exit /b 1

:verify_setup
.venv\Scripts\python.exe -c "import PySide6" 2>nul
if errorlevel 1 (
    echo ERROR: Setup finished but PySide6 is still missing.
    echo Delete the .venv folder and run setup.bat again.
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

:refresh_python_path
for /d %%D in ("%LocalAppData%\Programs\Python\Python3*") do (
    set "PATH=%%D;%%D\Scripts;%PATH%"
)
for /d %%D in ("%LocalAppData%\Python\pythoncore-*") do (
    set "PATH=%%D;%%D\Scripts;%PATH%"
)
if exist "%LocalAppData%\Python\bin\python.exe" (
    set "PATH=%LocalAppData%\Python\bin;%LocalAppData%\Python\bin\Scripts;%PATH%"
)
exit /b 0

:find_python
set "PYTHON_CMD="
call :refresh_python_path

where py >nul 2>&1 && (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>nul && set "PYTHON_CMD=py -3"
)
if defined PYTHON_CMD exit /b 0

for /f "delims=" %%P in ('dir /b /s "%LocalAppData%\Programs\Python\python.exe" "%LocalAppData%\Python\python.exe" 2^>nul') do (
    echo %%P | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        "%%P" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>nul && set "PYTHON_CMD=%%P" && exit /b 0
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    where python | findstr /i "WindowsApps" >nul
    if errorlevel 1 (
        python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" 2>nul && set "PYTHON_CMD=python"
    )
)
if defined PYTHON_CMD exit /b 0

exit /b 1
