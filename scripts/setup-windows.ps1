<#
.SYNOPSIS
  First-time Windows environment setup for Javo Agents.
.DESCRIPTION
  Creates Python virtual environment for services/local-runtime, installs Python
  dependencies, installs workspace JS dependencies if pnpm/npm is present, and
  generates Windows .ico/.png brand icons when Pillow is available.
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Write-Host "=== Javo Agents Windows Setup ===" -ForegroundColor Cyan
Write-Host "Workspace: $RepoRoot"

# 1. Check Python 3.11+
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.11+ is required on PATH. Download from https://www.python.org/downloads/"
}
python --version

# 2. Create venv in services/local-runtime/.venv
$RuntimeDir = Join-Path $RepoRoot "services\local-runtime"
$VenvDir = Join-Path $RuntimeDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating Python virtual environment at $VenvDir..." -ForegroundColor Yellow
    python -m venv $VenvDir
}

if (Test-Path (Join-Path $RuntimeDir "requirements.txt")) {
    Write-Host "Installing Python backend dependencies..." -ForegroundColor Yellow
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r (Join-Path $RuntimeDir "requirements.txt")
} elseif (Test-Path (Join-Path $RuntimeDir "pyproject.toml")) {
    Write-Host "Installing local-runtime package in editable mode..." -ForegroundColor Yellow
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -e $RuntimeDir
}

# 3. Generate Windows icons if Pillow is available
$IconScript = Join-Path $RepoRoot "packages\brand-assets\icons\generate_icons.py"
if (Test-Path $IconScript) {
    Write-Host "Checking Pillow for icon generation..." -ForegroundColor Yellow
    & $VenvPython $IconScript 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Optional: install Pillow (`pip install pillow`) to generate .ico/.png icons." -ForegroundColor DarkGray
    }
}

# 4. Check Node.js & pnpm
if (Test-Path "C:\Program Files\nodejs") {
    $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
}
if (Get-Command pnpm -ErrorAction SilentlyContinue) {
    Write-Host "Installing Node workspace packages via pnpm..." -ForegroundColor Yellow
    Push-Location $RepoRoot
    pnpm install
    Pop-Location
} else {
    Write-Host "pnpm not found. Install pnpm (`npm install -g pnpm`) to install JS/Electron packages." -ForegroundColor DarkYellow
}

Write-Host "Setup complete! Run .\scripts\start-windows.ps1 to launch Javo Agents." -ForegroundColor Green
