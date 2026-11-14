<# Electron owns desktop runtime startup; headless starts one backend. #>
[CmdletBinding()]
param([int]$Port = 8000, [switch]$Headless)
$ErrorActionPreference = "Stop"
$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$RuntimeDir = Join-Path $RepoRoot "services/local-runtime"
$ElectronDir = Join-Path $RepoRoot "apps/windows"
$VenvPython = Join-Path $RuntimeDir ".venv/Scripts/python.exe"
$PythonExe = if (Test-Path $VenvPython) { $VenvPython } else { "python" }
if (-not $Headless) {
    $ElectronExe = Join-Path $ElectronDir "node_modules/.bin/electron.cmd"
    if (-not (Test-Path (Join-Path $ElectronDir "dist/main.js")) -or -not (Test-Path $ElectronExe)) {
        throw "Build desktop and install dependencies first; or use -Headless with JAVO_OWNER_ACCESS_TOKEN configured."
    }
    Push-Location $ElectronDir
    try { & $ElectronExe .; exit $LASTEXITCODE } finally { Pop-Location }
}
if ([string]::IsNullOrWhiteSpace($env:JAVO_OWNER_ACCESS_TOKEN) -or $env:JAVO_OWNER_ACCESS_TOKEN.Length -lt 32) {
    throw "Set JAVO_OWNER_ACCESS_TOKEN to a random token of at least 32 characters before headless startup."
}
$StartArgs = @{
    FilePath = $PythonExe
    WindowStyle = "Hidden"
    ArgumentList = @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$Port")
    WorkingDirectory = $RuntimeDir
    PassThru = $true
}
$BackendProc = Start-Process @StartArgs
try {
    Write-Host "Runtime process started at http://127.0.0.1:$Port; readiness is not yet verified."
    Wait-Process -Id $BackendProc.Id
} finally {
    if (-not $BackendProc.HasExited) { Stop-Process -Id $BackendProc.Id }
}
