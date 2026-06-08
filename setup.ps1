# SheetGuard first-time setup (PowerShell).
# Usage: powershell -ExecutionPolicy Bypass -File setup.ps1

param(
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\scripts\ensure-environment.ps1"
exit (Invoke-SheetGuardSetup -ProjectRoot $PSScriptRoot -NonInteractive:$NonInteractive)
