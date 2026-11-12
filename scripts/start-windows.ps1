<#
.SYNOPSIS
  Starts the Javo Agents local FastAPI backend and Dashboard / Electron Desktop Shell.
#>
[CmdletBinding()]
param(
    [int]$Port = 8000,
    [switch]$Headless
)

$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeDir = Join-Path $RepoRoot "services\local-runtime"
$VenvPython = Join-Path $RuntimeDir ".venv\Scripts\python.exe"
$PythonExe = if (Test-Path $VenvPython) { $VenvPython } else { "python" }

if (Test-Path "C:\Program Files\nodejs") {
    $env:PATH = "C:\Program Files\nodejs;" + $env:PATH
}

Write-Host "Starting Javo Agents Local Runtime on http://127.0.0.1:$Port ..." -ForegroundColor Cyan

$BackendProc = Start-Process -FilePath $PythonExe `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port" `
    -WorkingDirectory $RuntimeDir `
    -PassThru

# Wait for /health/
$Healthy = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $resp = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health/" -TimeoutSec 2
        if ($resp.status) {
            $Healthy = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $Healthy) {
    Write-Warning "Backend did not respond on /health/ within 15s. Check logs."
} else {
    Write-Host "Local Runtime is healthy on port $Port." -ForegroundColor Green
}

if ($Headless) {
    Write-Host "Running in headless mode. Press Ctrl+C or stop PID $($BackendProc.Id) to exit."
    Wait-Process -Id $BackendProc.Id
    exit 0
}

$DashboardDir = Join-Path $RepoRoot "apps\dashboard"
$ElectronDir = Join-Path $RepoRoot "apps\windows"

if (Test-Path (Join-Path $ElectronDir "dist\main.js")) {
    Write-Host "Launching Electron Desktop Shell..." -ForegroundColor Cyan
    Push-Location $ElectronDir
    npx electron .
    Pop-Location
} elseif (Test-Path (Join-Path $DashboardDir "package.json")) {
    Write-Host "Launching Vite Dashboard in browser..." -ForegroundColor Cyan
    Push-Location $DashboardDir
    Start-Process "http://localhost:5173"
    npm run dev
    Pop-Location
} else {
    Write-Host "Backend running at http://127.0.0.1:$Port/docs" -ForegroundColor Green
    Wait-Process -Id $BackendProc.Id
}
