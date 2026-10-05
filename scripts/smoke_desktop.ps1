param(
    [int]$Port = 8890
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateRoot = Join-Path $env:LOCALAPPDATA "ORION-V3"
$ReadyFile = Join-Path $StateRoot "desktop-ready.json"
$ErrorFile = Join-Path $StateRoot "desktop-error.log"
$UiExe = Join-Path $Repo "dist\windows\ORION.exe"
$BuildInfo = Join-Path $Repo "dist\windows\build-info.json"

if (!(Test-Path -LiteralPath $UiExe -PathType Leaf)) {
    throw "ORION_DESKTOP_EXE> FAIL | missing $UiExe"
}
Write-Host "ORION_DESKTOP_EXE> PASS" -ForegroundColor Green

$health = Invoke-RestMethod -Uri ("http://127.0.0.1:" + $Port + "/api/health") -TimeoutSec 3
if (!$health.ok) { throw "ORION_DESKTOP_RUNTIME> FAIL | backend unhealthy" }
Write-Host ("ORION_DESKTOP_RUNTIME> PASS | " + $health.running_commit) -ForegroundColor Green

if (!(Test-Path -LiteralPath $BuildInfo -PathType Leaf)) {
    throw "ORION_DESKTOP_BUILD_INFO> FAIL | build-info.json missing"
}
$build = Get-Content -LiteralPath $BuildInfo -Raw | ConvertFrom-Json
$head = (& git.exe -C $Repo rev-parse HEAD).Trim()

if ([string]$build.commit -ne $head) {
    throw ("ORION_DESKTOP_BUILD_MATCH> FAIL | exe " + $build.commit + " != repo " + $head)
}
if ([string]$health.running_commit -ne $head) {
    throw ("ORION_DESKTOP_RUNTIME_MATCH> FAIL | runtime " + $health.running_commit + " != repo " + $head)
}
Write-Host ("ORION_DESKTOP_BUILD_MATCH> PASS | " + $head) -ForegroundColor Green

$ui = Get-CimInstance Win32_Process -Filter "Name='ORION.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath -ieq $UiExe
    } |
    Select-Object -First 1

if (!$ui) {
    throw "ORION_DESKTOP_PROCESS> FAIL | ORION.exe not running"
}
Write-Host ("ORION_DESKTOP_PROCESS> PASS | PID " + $ui.ProcessId) -ForegroundColor Green

$ready = $null
for ($i = 0; $i -lt 40; $i++) {
    if (Test-Path -LiteralPath $ReadyFile -PathType Leaf) {
        try {
            $ready = Get-Content -LiteralPath $ReadyFile -Raw | ConvertFrom-Json
            if ([int]$ready.pid -eq [int]$ui.ProcessId -and [string]$ready.url -eq ("http://127.0.0.1:" + $Port + "/v3/")) {
                break
            }
        } catch {}
    }

    if (Test-Path -LiteralPath $ErrorFile -PathType Leaf) {
        $detail = (Get-Content -LiteralPath $ErrorFile -Raw -ErrorAction SilentlyContinue).Trim()
        if ($detail) {
            throw ("ORION_DESKTOP_READY> FAIL | " + $detail)
        }
    }

    Start-Sleep -Milliseconds 300
}

if (!$ready -or [int]$ready.pid -ne [int]$ui.ProcessId) {
    throw "ORION_DESKTOP_READY> FAIL | native shell never reported STRATA ready"
}
Write-Host "ORION_DESKTOP_READY> PASS | STRATA loaded inside ORION.exe" -ForegroundColor Green

$startProductSource = Get-Content -LiteralPath (Join-Path $Repo "scripts\start_product_ui.ps1") -Raw
if ($startProductSource -match 'Start-Process\s+\("?http://127\.0\.0\.1') {
    throw "ORION_NO_EXTERNAL_BROWSER> FAIL | backend launcher still opens a browser"
}
Write-Host "ORION_NO_EXTERNAL_BROWSER> PASS" -ForegroundColor Green

try {
    $ollama = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 3
    Write-Host "ORION_OLLAMA_RUNTIME> PASS" -ForegroundColor Green
} catch {
    throw "ORION_OLLAMA_RUNTIME> FAIL | Ollama API is not reachable on 127.0.0.1:11434"
}

$ollamaOwnerFile = Join-Path $StateRoot "ollama-owner.json"
if (Test-Path -LiteralPath $ollamaOwnerFile -PathType Leaf) {
    $owner = Get-Content -LiteralPath $ollamaOwnerFile -Raw | ConvertFrom-Json
    $owned = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$owner.pid) -ErrorAction SilentlyContinue
    if (
        !$owned -or
        $owned.Name -ine "ollama.exe" -or
        [string]$owner.opened_by -ne "ORION-V3" -or
        [string]$owner.command -ne "serve"
    ) {
        throw "ORION_OLLAMA_OWNERSHIP> FAIL | ownership record does not match a live ORION-started serve process"
    }
    Write-Host ("ORION_OLLAMA_OWNERSHIP> PASS | ORION-owned PID " + $owner.pid) -ForegroundColor Green
} else {
    Write-Host "ORION_OLLAMA_OWNERSHIP> PASS | pre-existing Ollama left unowned" -ForegroundColor Green
}

$indexSource = Get-Content -LiteralPath (Join-Path $Repo "ui\strata\index.html") -Raw
$nativeSource = Get-Content -LiteralPath (Join-Path $Repo "desktop\ORION.UI\MainWindow.xaml.cs") -Raw
if ($indexSource -notmatch 'id="closeOrion"' -or $nativeSource -notmatch 'orion-close') {
    throw "ORION_CLOSE_CONTROL> FAIL | native CLOSE control contract missing"
}
Write-Host "ORION_CLOSE_CONTROL> PASS" -ForegroundColor Green

foreach ($required in @("START ORION.bat", "STOP ORION.bat", "scripts\start_orion.ps1", "scripts\stop_orion.ps1")) {
    if (!(Test-Path -LiteralPath (Join-Path $Repo $required) -PathType Leaf)) {
        throw ("ORION_LAUNCH_PROTOCOL> FAIL | missing " + $required)
    }
}
Write-Host "ORION_LAUNCH_PROTOCOL> PASS" -ForegroundColor Green
Write-Host "ORION_DESKTOP_SMOKE> PASS" -ForegroundColor Green
