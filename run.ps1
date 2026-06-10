# SheetGuard launcher (PowerShell).
# Runs setup automatically if the project is not ready yet.

param(
    [switch]$NonInteractive
)

$ErrorActionPreference = "Stop"
. "$PSScriptRoot\scripts\ensure-environment.ps1"
exit (Invoke-SheetGuardRun -ProjectRoot $PSScriptRoot -NonInteractive:$NonInteractive)
