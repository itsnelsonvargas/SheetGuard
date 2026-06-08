# Shared setup/run helpers for SheetGuard on Windows.
# Dot-source from setup.ps1 / run.ps1, or run via setup.bat / run.bat.

$script:PythonMinVersion = [Version]"3.10.0"
$script:PinnedPythonVersion = "3.12.9"
$script:PinnedPythonInstaller = "https://www.python.org/ftp/python/$($script:PinnedPythonVersion)/python-$($script:PinnedPythonVersion)-amd64.exe"

function Write-SetupHeader {
    param([string]$Title = "SheetGuard - Environment setup")
    Write-Host ""
    Write-Host "========================================"
    Write-Host "  $Title"
    Write-Host "========================================"
    Write-Host ""
}

function Write-SetupStep {
    param([string]$Message)
    Write-Host ">> $Message"
}

function Wait-ForEnter {
    param([switch]$NonInteractive)
    if (-not $NonInteractive) {
        Read-Host "Press Enter to exit"
    }
}

function Invoke-PythonQuiet {
    param(
        [string]$PythonExe,
        [string[]]$Arguments
    )

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        & $PythonExe @Arguments 2>$null | Out-Null
        return $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
}

function Test-PythonVersion {
    param([string]$PythonExe)
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        return $false
    }

    $exitCode = Invoke-PythonQuiet $PythonExe @(
        "-c", "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)"
    )
    return $exitCode -eq 0
}

function Get-PythonVersionString {
    param([string]$PythonExe)
    if (-not (Test-Path -LiteralPath $PythonExe)) {
        return $null
    }

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $version = & $PythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $version) {
            return $null
        }
        return $version.Trim()
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
}

function Invoke-PythonExe {
    param(
        [string]$PythonExe,
        [string[]]$Arguments
    )

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $PythonExe @Arguments | Out-Null
        if ($null -ne $LASTEXITCODE) {
            return [int]$LASTEXITCODE
        }
        return 0
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }
}

function Test-SystemPythonPath {
    param([string]$PythonPath)

    if ($PythonPath -match "\\\.venv\\") {
        return $false
    }
    if ($PythonPath -match "\\WindowsApps\\") {
        return $false
    }
    if ($PythonPath -match "\\Microsoft\\WindowsApps\\") {
        return $false
    }
    return $true
}

function Resolve-PyLauncherPython {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if (-not $pyLauncher) {
        return $null
    }

    $previousErrorAction = $ErrorActionPreference
    $ErrorActionPreference = "SilentlyContinue"
    try {
        $resolved = & $pyLauncher.Source -3 -c "import sys; print(sys.executable)" 2>$null
    }
    finally {
        $ErrorActionPreference = $previousErrorAction
    }

    if ($LASTEXITCODE -ne 0 -or -not $resolved) {
        return $null
    }

    $resolved = $resolved.Trim()
    if (-not (Test-SystemPythonPath $resolved)) {
        return $null
    }

    return $resolved
}

function Get-PythonSearchPaths {
    $paths = New-Object System.Collections.Generic.List[string]

    $launcherPython = Resolve-PyLauncherPython
    if ($launcherPython) {
        $paths.Add($launcherPython) | Out-Null
    }

    $roots = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python"),
        (Join-Path $env:LOCALAPPDATA "Python"),
        ${env:ProgramFiles},
        ${env:ProgramFiles(x86)}
    ) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

    foreach ($root in $roots) {
        Get-ChildItem -Path $root -Filter "python.exe" -Recurse -ErrorAction SilentlyContinue |
            Where-Object { Test-SystemPythonPath $_.FullName } |
            ForEach-Object { $paths.Add($_.FullName) }
    }

    foreach ($name in @("python", "python3")) {
        $command = Get-Command $name -ErrorAction SilentlyContinue
        if ($command -and (Test-SystemPythonPath $command.Source)) {
            $paths.Add($command.Source) | Out-Null
        }
    }

    return $paths | Select-Object -Unique
}

function Find-PythonExecutable {
    $candidates = Get-PythonSearchPaths
    $best = $null
    $bestVersion = [Version]"0.0.0"

    foreach ($candidate in $candidates) {
        $resolved = $candidate

        if (-not (Test-PythonVersion $resolved)) {
            continue
        }

        $versionText = Get-PythonVersionString $resolved
        if (-not $versionText) {
            continue
        }

        $version = [Version]$versionText
        if ($version -ge $bestVersion) {
            $best = $resolved
            $bestVersion = $version
        }
    }

    return $best
}

function Add-PythonToSessionPath {
    $roots = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python"),
        (Join-Path $env:LOCALAPPDATA "Python")
    )

    foreach ($pythonRoot in $roots) {
        if (-not (Test-Path -LiteralPath $pythonRoot)) {
            continue
        }

        Get-ChildItem -Path $pythonRoot -Directory -ErrorAction SilentlyContinue |
            ForEach-Object {
                $scripts = Join-Path $_.FullName "Scripts"
                $env:PATH = "$($_.FullName);$scripts;$env:PATH"
            }
    }
}

function Install-PythonWithWinget {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        return $false
    }

    Write-SetupStep "Installing Python 3.12 via winget..."
    winget install --id Python.Python.3.12 -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    Add-PythonToSessionPath
    return [bool](Find-PythonExecutable)
}

function Install-PythonWithChocolatey {
    if (-not (Get-Command choco -ErrorAction SilentlyContinue)) {
        return $false
    }

    Write-SetupStep "Installing Python 3.12 via Chocolatey..."
    choco install python312 -y --no-progress
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    Add-PythonToSessionPath
    return [bool](Find-PythonExecutable)
}

function Install-PythonWithInstaller {
    $installerPath = Join-Path $env:TEMP "sheetguard-python-installer.exe"

    try {
        Write-SetupStep "Downloading Python $script:PinnedPythonVersion installer..."
        Invoke-WebRequest -Uri $script:PinnedPythonInstaller -OutFile $installerPath -UseBasicParsing

        Write-SetupStep "Running Python installer (quiet mode)..."
        $process = Start-Process -FilePath $installerPath -ArgumentList @(
            "/quiet",
            "InstallAllUsers=0",
            "PrependPath=1",
            "Include_pip=1",
            "Include_launcher=1"
        ) -Wait -PassThru

        if ($process.ExitCode -ne 0) {
            return $false
        }

        Add-PythonToSessionPath
        Start-Sleep -Seconds 2
        return [bool](Find-PythonExecutable)
    }
    catch {
        Write-Host "Installer download failed: $($_.Exception.Message)"
        return $false
    }
    finally {
        if (Test-Path -LiteralPath $installerPath) {
            Remove-Item -LiteralPath $installerPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Show-ManualPythonInstructions {
    Write-Host ""
    Write-Host "Automatic Python installation did not succeed."
    Write-Host ""
    Write-Host "Install Python 3.10 or newer manually:"
    Write-Host "  https://www.python.org/downloads/"
    Write-Host ""
    Write-Host 'During installation, check "Add python.exe to PATH".'
    Write-Host "Then run setup.bat or setup.ps1 again."
    Write-Host ""
}

function Ensure-PythonInstalled {
    param([switch]$NonInteractive)

    $pythonExe = Find-PythonExecutable
    if ($pythonExe) {
        return $pythonExe
    }

    Write-Host "Python $($script:PythonMinVersion) or newer was not found."
    Write-Host ""

    if (Install-PythonWithWinget) { return Find-PythonExecutable }
    if (Install-PythonWithChocolatey) { return Find-PythonExecutable }
    if (Install-PythonWithInstaller) { return Find-PythonExecutable }

    Show-ManualPythonInstructions
    Wait-ForEnter -NonInteractive:$NonInteractive
    return $null
}

function Get-ProjectPaths {
    param([string]$ProjectRoot)

    return [pscustomobject]@{
        Root = $ProjectRoot
        Requirements = Join-Path $ProjectRoot "requirements.txt"
        Main = Join-Path $ProjectRoot "main.py"
        VenvDir = Join-Path $ProjectRoot ".venv"
        VenvPython = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    }
}

function Test-InternetConnection {
    try {
        $null = Invoke-WebRequest -Uri "https://pypi.org/simple/pip/" -Method Head -UseBasicParsing -TimeoutSec 15
        return $true
    }
    catch {
        return $false
    }
}

function Remove-BrokenVirtualEnvironment {
    param([string]$VenvDir)

    if (-not (Test-Path -LiteralPath $VenvDir)) {
        return
    }

    Write-SetupStep "Removing incomplete virtual environment..."
    Remove-Item -LiteralPath $VenvDir -Recurse -Force -ErrorAction SilentlyContinue
}

function Ensure-VirtualEnvironment {
    param(
        [string]$PythonExe,
        [string]$VenvDir,
        [string]$VenvPython
    )

    $needsRecreate = $false

    if (Test-Path -LiteralPath $VenvPython) {
        if (-not (Test-PythonVersion $VenvPython)) {
            $needsRecreate = $true
        }
    }
    elseif (Test-Path -LiteralPath $VenvDir) {
        $needsRecreate = $true
    }

    if ($needsRecreate) {
        Remove-BrokenVirtualEnvironment $VenvDir
    }

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        Write-SetupStep "Creating virtual environment in .venv ..."
        $exitCode = Invoke-PythonExe -PythonExe $PythonExe -Arguments @("-m", "venv", $VenvDir)
        if ($exitCode -ne 0) {
            Write-SetupStep "venv module failed; trying ensurepip bootstrap..."
            $exitCode = Invoke-PythonExe -PythonExe $PythonExe -Arguments @("-m", "pip", "install", "--upgrade", "pip", "virtualenv")
            if ($exitCode -eq 0) {
                $exitCode = Invoke-PythonExe -PythonExe $PythonExe -Arguments @("-m", "virtualenv", $VenvDir)
            }
        }

        if ($exitCode -ne 0 -or -not (Test-Path -LiteralPath $VenvPython)) {
            throw "Could not create virtual environment."
        }
    }
    else {
        Write-SetupStep "Virtual environment found - verifying dependencies..."
    }

    return $VenvPython
}

function Install-ProjectRequirements {
    param(
        [string]$VenvPython,
        [string]$RequirementsFile,
        [int]$MaxAttempts = 3
    )

    if (-not (Test-Path -LiteralPath $RequirementsFile)) {
        throw "Missing requirements file: $RequirementsFile"
    }

    if (-not (Test-InternetConnection)) {
        Write-Host ""
        Write-Host "WARNING: Could not reach PyPI. Setup needs internet on first run."
        Write-Host ""
    }

    $attempt = 0
    while ($attempt -lt $MaxAttempts) {
        $attempt++
        Write-SetupStep "Installing dependencies (attempt $attempt of $MaxAttempts)..."

        $pipExit = Invoke-PythonExe -PythonExe $VenvPython -Arguments @("-m", "pip", "install", "--upgrade", "pip")
        if ($pipExit -ne 0) {
            if ($attempt -ge $MaxAttempts) {
                throw "Could not upgrade pip."
            }
            Start-Sleep -Seconds 3
            continue
        }

        $reqExit = Invoke-PythonExe -PythonExe $VenvPython -Arguments @("-m", "pip", "install", "-r", $RequirementsFile, "--default-timeout=120")
        if ($reqExit -eq 0) {
            return
        }

        if ($attempt -lt $MaxAttempts) {
            Write-Host "Dependency install failed. Retrying..."
            Start-Sleep -Seconds 5
        }
    }

    throw "Could not install dependencies from requirements.txt."
}

function Test-ProjectSetup {
    param([string]$VenvPython)

    if (-not (Test-Path -LiteralPath $VenvPython)) {
        return $false
    }

    if (-not (Test-PythonVersion $VenvPython)) {
        return $false
    }

    $exitCode = Invoke-PythonQuiet $VenvPython @("-c", "import PySide6")
    return $exitCode -eq 0
}

function Invoke-SheetGuardSetup {
    param(
        [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
        [switch]$NonInteractive
    )

    $ErrorActionPreference = "Stop"
    Set-Location $ProjectRoot

    Write-SetupHeader

    $paths = Get-ProjectPaths $ProjectRoot
    $pythonExe = Ensure-PythonInstalled -NonInteractive:$NonInteractive
    if (-not $pythonExe) {
        return 1
    }

    $version = Get-PythonVersionString $pythonExe
    Write-SetupStep "Using Python $version at $pythonExe"

    try {
        $venvPython = Ensure-VirtualEnvironment -PythonExe $pythonExe -VenvDir $paths.VenvDir -VenvPython $paths.VenvPython
        Install-ProjectRequirements -VenvPython $venvPython -RequirementsFile $paths.Requirements

        if (-not (Test-ProjectSetup $venvPython)) {
            throw "Setup finished but PySide6 is still missing. Try deleting .venv and running setup again."
        }

        Write-Host ""
        Write-Host "========================================"
        Write-Host "  Setup complete!"
        Write-Host "  Run run.bat to start SheetGuard."
        Write-Host "========================================"
        Write-Host ""
        Wait-ForEnter -NonInteractive:$NonInteractive
        return 0
    }
    catch {
        Write-Host ""
        Write-Host "ERROR: $($_.Exception.Message)"
        Write-Host ""
        Wait-ForEnter -NonInteractive:$NonInteractive
        return 1
    }
}

function Invoke-SheetGuardRun {
    param(
        [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
        [switch]$NonInteractive
    )

    Set-Location $ProjectRoot
    $paths = Get-ProjectPaths $ProjectRoot

    if (-not (Test-ProjectSetup $paths.VenvPython)) {
        Write-Host "SheetGuard is not ready yet. Running setup..."
        Write-Host ""
        $setupExit = Invoke-SheetGuardSetup -ProjectRoot $ProjectRoot -NonInteractive:$NonInteractive
        if ($setupExit -ne 0) {
            return $setupExit
        }
    }

    Write-Host "Installing dependencies (if needed)..."
    $reqExit = Invoke-PythonExe -PythonExe $paths.VenvPython -Arguments @("-m", "pip", "install", "-r", $paths.Requirements, "-q", "--disable-pip-version-check")
    if ($reqExit -ne 0) {
        Write-Host "ERROR: Could not verify dependencies. Run setup.bat again."
        Wait-ForEnter -NonInteractive:$NonInteractive
        return 1
    }

    Write-Host "Starting SheetGuard..."
    $runExit = Invoke-PythonExe -PythonExe $paths.VenvPython -Arguments @($paths.Main)
    if ($runExit -ne 0 -and -not $NonInteractive) {
        Wait-ForEnter
    }
    return $runExit
}
