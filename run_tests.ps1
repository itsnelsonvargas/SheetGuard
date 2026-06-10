Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

. "$PSScriptRoot\scripts\ensure-environment.ps1"

$paths = Get-ProjectPaths $PSScriptRoot
if (-not (Test-ProjectSetup $paths.VenvPython)) {
    Write-Host "Running setup first..."
    $setupExit = Invoke-SheetGuardSetup -ProjectRoot $PSScriptRoot -NonInteractive
    if ($setupExit -ne 0) {
        exit $setupExit
    }
}

& $paths.VenvPython -m pip install -r $paths.Requirements -q --disable-pip-version-check
& $paths.VenvPython -m pytest tests --verbose
