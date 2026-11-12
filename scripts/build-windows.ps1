<#
.SYNOPSIS
  Builds all shared TypeScript packages, dashboard frontend, and Windows Electron shell.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

if (Test-Path "C:\Program Files\nodejs") {
    $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
}

$Packages = @(
    "packages\shared-types",
    "packages\api-client",
    "packages\workflow-schema",
    "packages\policy-engine",
    "apps\windows"
)

foreach ($Pkg in $Packages) {
    $FullPath = Join-Path $RepoRoot $Pkg
    if (Test-Path (Join-Path $FullPath "package.json")) {
        Write-Host "Building $Pkg ..." -ForegroundColor Cyan
        Push-Location $FullPath
        npm run build
        Pop-Location
    }
}

$DashboardDir = Join-Path $RepoRoot "apps\dashboard"
if (Test-Path (Join-Path $DashboardDir "package.json")) {
    Write-Host "Building apps/dashboard ..." -ForegroundColor Cyan
    Push-Location $DashboardDir
    npm run build
    Pop-Location
}

Write-Host "Windows build completed." -ForegroundColor Green
