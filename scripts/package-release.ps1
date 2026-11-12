<#
.SYNOPSIS
  Packages the Windows NSIS installer and Portable .exe release artifacts.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

if (Test-Path "C:\Program Files\nodejs") {
    $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
}

& (Join-Path $PSScriptRoot "build-windows.ps1")

$IconScript = Join-Path $RepoRoot "packages\brand-assets\icons\generate_icons.py"
if (Test-Path $IconScript) {
    python $IconScript 2>$null
}

$WinAppDir = Join-Path $RepoRoot "apps\windows"
Push-Location $WinAppDir
Write-Host "Packaging Windows NSIS & Portable installers with electron-builder..." -ForegroundColor Cyan
npm run dist:win
Pop-Location

Write-Host "Release artifacts written to apps/windows/release/" -ForegroundColor Green
