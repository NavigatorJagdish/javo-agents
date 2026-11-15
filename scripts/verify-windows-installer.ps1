<# CI-only NSIS install/reinstall checks inside a newly allocated temporary root. #>
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Installer)
$ErrorActionPreference = "Stop"
$installerPath = (Resolve-Path -LiteralPath $Installer).Path
if (-not $env:RUNNER_TEMP) { throw "This test requires an isolated CI runner temporary directory." }
$tempRoot = [IO.Path]::GetFullPath($env:RUNNER_TEMP).TrimEnd([IO.Path]::DirectorySeparatorChar)
$qaRoot = Join-Path $tempRoot ("javo-installer-" + [guid]::NewGuid().ToString("N"))
$installTarget = Join-Path $qaRoot "app"
$stateTarget = Join-Path $qaRoot "qa-profile"
New-Item -ItemType Directory -Path $stateTarget -Force | Out-Null

function Assert-IsolatedInstallTarget {
    $resolved = [IO.Path]::GetFullPath($installTarget)
    $expected = [IO.Path]::GetFullPath((Join-Path $qaRoot "app"))
    if ($resolved -cne $expected -or -not $resolved.StartsWith($tempRoot + [IO.Path]::DirectorySeparatorChar)) {
        throw "Installer test target escaped its isolated temporary root."
    }
    if (-not ([IO.Path]::GetFileName($qaRoot)).StartsWith("javo-installer-")) {
        throw "Unexpected installer test directory."
    }
}

$marker = Join-Path $stateTarget "owner-marker.txt"
Set-Content -LiteralPath $marker -Value "QA data must survive uninstall and reinstall" -NoNewline
$markerHash = (Get-FileHash -LiteralPath $marker -Algorithm SHA256).Hash
$control = Join-Path $stateTarget "runtime/runtime-control.json"
$previousProfile = $env:JAVO_SMOKE_PROFILE
$previousPreserve = $env:JAVO_SMOKE_PRESERVE_PROVIDER
$previousExpect = $env:JAVO_SMOKE_EXPECT_PROVIDER
$providerData = Join-Path $stateTarget "runtime/provider-config.enc"
$providerKey = Join-Path $stateTarget "runtime/provider-config.key.dpapi"
try {
    $env:JAVO_SMOKE_PROFILE = $stateTarget
    foreach ($cycle in @(1, 2)) {
        Write-Output "NSIS_QA_CYCLE_$cycle"
        $env:JAVO_SMOKE_PRESERVE_PROVIDER = if ($cycle -eq 1) { "1" } else { "0" }
        $env:JAVO_SMOKE_EXPECT_PROVIDER = if ($cycle -eq 2) { "1" } else { "0" }
        Assert-IsolatedInstallTarget
        # NSIS requires /D last and consumes the remaining directory argument.
        $setup = Start-Process -FilePath $installerPath -ArgumentList @("/S", "/D=$installTarget") -WindowStyle Hidden -PassThru -Wait
        if ($setup.ExitCode -ne 0) {
            # Diagnostic evidence only; never relax Windows protection or retry away a crash.
            Get-WinEvent -FilterHashtable @{LogName="Application"; Id=1000; StartTime=(Get-Date).AddMinutes(-2)} -ErrorAction SilentlyContinue |
                Where-Object Message -Like "*JavoAgents*" | Select-Object -First 3 TimeCreated, Message | Format-List | Out-Host
            throw "NSIS installation failed in cycle ${cycle}: $($setup.ExitCode)"
        }
        $appExe = Join-Path $installTarget "Javo Agents.exe"
        if (-not (Test-Path -LiteralPath $appExe)) { throw "Installed application is missing." }
        if ($cycle -eq 2 -and (Get-FileHash -LiteralPath $control -Algorithm SHA256).Hash -cne $savedControlHash) {
            throw "Reinstallation changed the preserved runtime control state."
        }
        if ($cycle -eq 2 -and ((Get-FileHash -LiteralPath $providerData -Algorithm SHA256).Hash -cne $savedProviderHash -or
            (Get-FileHash -LiteralPath $providerKey -Algorithm SHA256).Hash -cne $savedKeyHash)) {
            throw "Reinstallation changed encrypted provider data or its wrapped key."
        }
        node (Join-Path $PSScriptRoot "verify-packaged-desktop.cjs") $appExe
        if ($LASTEXITCODE -ne 0) { throw "Installed application lifecycle test failed." }
        $savedControlHash = (Get-FileHash -LiteralPath $control -Algorithm SHA256).Hash
        $savedProviderHash = (Get-FileHash -LiteralPath $providerData -Algorithm SHA256).Hash
        $savedKeyHash = (Get-FileHash -LiteralPath $providerKey -Algorithm SHA256).Hash
        $uninstallers = @(Get-ChildItem -LiteralPath $installTarget -File -Filter "Uninstall*.exe")
        if ($uninstallers.Count -ne 1) { throw "Expected one application uninstaller." }
        Assert-IsolatedInstallTarget
        # _?= keeps uninstall synchronous instead of returning from a self-copy launcher.
        $uninstall = Start-Process -FilePath $uninstallers[0].FullName -ArgumentList @("/S", "_?=$installTarget") -WindowStyle Hidden -PassThru -Wait
        if ($uninstall.ExitCode -ne 0) { throw "NSIS uninstallation failed: $($uninstall.ExitCode)" }
        $deadline = [DateTime]::UtcNow.AddSeconds(20)
        while ((Test-Path -LiteralPath $appExe) -and [DateTime]::UtcNow -lt $deadline) {
            Start-Sleep -Milliseconds 200
        }
        if (Test-Path -LiteralPath $appExe) { throw "Uninstaller did not remove the application." }
        if ((Get-FileHash -LiteralPath $marker -Algorithm SHA256).Hash -cne $markerHash -or
            (Get-FileHash -LiteralPath $control -Algorithm SHA256).Hash -cne $savedControlHash -or
            (Get-FileHash -LiteralPath $providerData -Algorithm SHA256).Hash -cne $savedProviderHash -or
            (Get-FileHash -LiteralPath $providerKey -Algorithm SHA256).Hash -cne $savedKeyHash) {
            throw "Uninstall changed the preserved QA profile."
        }
    }
    Write-Output "NSIS_INSTALL_REINSTALL_QA_PROFILE_PRESERVED_OK"
} finally {
    $env:JAVO_SMOKE_PROFILE = $previousProfile
    $env:JAVO_SMOKE_PRESERVE_PROVIDER = $previousPreserve
    $env:JAVO_SMOKE_EXPECT_PROVIDER = $previousExpect
}
# Preserve this fresh test root for runner-level cleanup; never remove unrelated data.
