$ErrorActionPreference = 'Stop'

function Fail([string]$Code, [string]$Detail) {
    Write-Host ($Code + '> FAIL')
    Write-Host ('DETAIL> ' + $Detail)
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'V3_RUN_ID> V3-RUN-004'
Write-Host 'DESKTOP_ISOLATED_LAUNCH> START'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Donor = Join-Path $RepoRoot 'external\OpenJarvis'
$Frontend = Join-Path $Donor 'frontend'
$SandboxHome = Join-Path $env:LOCALAPPDATA 'OrionV3\openjarvis-desktop-home'
$SandboxOpenJarvis = Join-Path $SandboxHome '.openjarvis'
$SandboxInference = Join-Path $SandboxOpenJarvis 'inference.json'

if (-not (Test-Path $Donor)) {
    Fail 'OPENJARVIS_PIN' 'Pinned OpenJarvis checkout is missing.'
}
$DonorSha = (& git -C $Donor rev-parse HEAD).Trim()
if ($DonorSha -ne '309a4f1044ccfb2032264832a31fef2f1d314586') {
    Fail 'OPENJARVIS_PIN' ('Unexpected donor SHA: ' + $DonorSha)
}
Write-Host 'OPENJARVIS_PIN> PASS'

New-Item -ItemType Directory -Force -Path $SandboxOpenJarvis | Out-Null

# The V3 desktop sandbox must begin unconfigured. Only the sandbox is touched;
# the user's real ~/.openjarvis is deliberately left unchanged.
if (Test-Path $SandboxInference) {
    Remove-Item -LiteralPath $SandboxInference -Force
}
if (Test-Path $SandboxInference) {
    Fail 'DESKTOP_SANDBOX' 'Could not clear sandbox inference state.'
}
Write-Host 'REAL_OPENJARVIS_HOME> UNTOUCHED'
Write-Host ('DESKTOP_SANDBOX_HOME> ' + $SandboxHome)
Write-Host 'DESKTOP_SANDBOX_INFERENCE> ABSENT'

$nodeRaw = (& node --version).Trim()
if ($LASTEXITCODE -ne 0 -or $nodeRaw -notmatch '^v(\d+)\.(\d+)\.(\d+)$') {
    Fail 'NODE' ('Could not parse Node version: ' + $nodeRaw)
}
$nodeMajor = [int]$Matches[1]
$nodeMinor = [int]$Matches[2]
if ($nodeMajor -lt 22 -or ($nodeMajor -eq 22 -and $nodeMinor -lt 22)) {
    Fail 'NODE' ('Pinned desktop requires Node >=22.22; found ' + $nodeRaw)
}
Write-Host ('NODE> PASS ' + $nodeRaw)

$npx = Get-Command npx -ErrorAction SilentlyContinue
if ($null -eq $npx) {
    Fail 'PINNED_NPM' 'npx is unavailable.'
}

Push-Location $Frontend
try {
    $npmPinned = (& npx --yes npm@11.19.0 --version).Trim()
    if ($LASTEXITCODE -ne 0 -or $npmPinned -notmatch '^11\.19\.') {
        Fail 'PINNED_NPM' ('Expected npm 11.19.x; got ' + $npmPinned)
    }
    Write-Host ('PINNED_NPM> PASS ' + $npmPinned)

    Write-Host 'DESKTOP_NPM_CI> RUN'
    & npx --yes npm@11.19.0 ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) {
        Fail 'DESKTOP_NPM_CI' 'Pinned npm dependency install failed.'
    }
    Write-Host 'DESKTOP_NPM_CI> PASS'

    $tauriBin = Join-Path $Frontend 'node_modules\.bin\tauri.cmd'
    if (-not (Test-Path $tauriBin)) {
        Fail 'TAURI_CLI' 'Local Tauri CLI was not installed.'
    }
    Write-Host 'TAURI_CLI> FOUND'

    # Override only the dev command so Tauri does not invoke the older global
    # npm. This temporary config lives outside the donor checkout.
    $RuntimeDir = Join-Path $env:LOCALAPPDATA 'OrionV3\desktop-runtime'
    New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
    $OverridePath = Join-Path $RuntimeDir 'tauri-orion-v3.json'
    @'
{
  "build": {
    "beforeDevCommand": "npx --yes npm@11.19.0 run dev"
  }
}
'@ | Set-Content -LiteralPath $OverridePath -Encoding UTF8

    # Launch in a child PowerShell with a V3-only HOME. The pinned desktop code
    # stays inert when no inference.json exists, so it cannot auto-start its
    # own Jarvis server or Ollama on this run.
    $launchScript = Join-Path $RuntimeDir 'launch-openjarvis-v3.ps1'
    @(
        "`$env:HOME = '$SandboxHome'",
        "`$env:OPENJARVIS_ROOT = '$Donor'",
        "Set-Location '$Frontend'",
        "& '$tauriBin' dev --config '$OverridePath'"
    ) | Set-Content -LiteralPath $launchScript -Encoding UTF8

    $child = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
        '-NoProfile',
        '-ExecutionPolicy', 'Bypass',
        '-File', $launchScript
    ) -WindowStyle Hidden -PassThru

    Write-Host ('DESKTOP_LAUNCHER_PID> ' + $child.Id)

    Start-Sleep -Seconds 8
    if ($child.HasExited) {
        Fail 'DESKTOP_LAUNCH' ('Tauri launcher exited early with code ' + $child.ExitCode)
    }

    # Re-check the sandbox. A stock fresh desktop is allowed to show setup UI,
    # but it must not have silently persisted/confirmed an inference source.
    if (Test-Path $SandboxInference) {
        try {
            $cfg = Get-Content -Raw -LiteralPath $SandboxInference | ConvertFrom-Json
            $confirmed = $false
            if ($null -ne $cfg.PSObject.Properties['confirmed']) {
                $confirmed = [bool]$cfg.confirmed
            } else {
                $confirmed = $true
            }
            if ($confirmed) {
                Stop-Process -Id $child.Id -Force -ErrorAction SilentlyContinue
                Fail 'DESKTOP_INERT_GUARD' 'Desktop created a confirmed inference source unexpectedly.'
            }
        } catch {
            Stop-Process -Id $child.Id -Force -ErrorAction SilentlyContinue
            Fail 'DESKTOP_INERT_GUARD' 'Sandbox inference state became unreadable.'
        }
    }

    Write-Host 'DESKTOP_INERT_GUARD> PASS'
    Write-Host 'JARVIS_BACKEND_AUTOSTART> BLOCKED_BY_SANDBOX'
    Write-Host 'OLLAMA_AUTOSTART> BLOCKED_BY_SANDBOX'
    Write-Host 'DESKTOP_UI_PROCESS> RUNNING'
    Write-Host 'DESKTOP_ISOLATED_LAUNCH> PASS'
    Write-Host 'STATUS> PASS'
}
finally {
    Pop-Location
}
