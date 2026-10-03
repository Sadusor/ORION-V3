$ErrorActionPreference = 'Stop'

function Fail([string]$Code, [string]$Detail) {
    Write-Host ($Code + '> FAIL')
    Write-Host ('DETAIL> ' + $Detail)
    if (Test-Path $LaunchLog) {
        Write-Host 'DESKTOP_STDOUT_TAIL>'
        Get-Content -LiteralPath $LaunchLog -Tail 80 -ErrorAction SilentlyContinue
    }
    if (Test-Path $LaunchErr) {
        Write-Host 'DESKTOP_STDERR_TAIL>'
        Get-Content -LiteralPath $LaunchErr -Tail 160 -ErrorAction SilentlyContinue
    }
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'V3_RUN_ID> V3-RUN-006'
Write-Host 'DESKTOP_VISIBLE_WINDOW> START'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Donor = Join-Path $RepoRoot 'external\OpenJarvis'
$Frontend = Join-Path $Donor 'frontend'
$SandboxHome = Join-Path $env:LOCALAPPDATA 'OrionV3\openjarvis-desktop-home'
$SandboxOpenJarvis = Join-Path $SandboxHome '.openjarvis'
$SandboxInference = Join-Path $SandboxOpenJarvis 'inference.json'
$RuntimeDir = Join-Path $env:LOCALAPPDATA 'OrionV3\desktop-runtime'
$LaunchLog = Join-Path $RuntimeDir 'openjarvis-desktop-v3.log'
$LaunchErr = Join-Path $RuntimeDir 'openjarvis-desktop-v3.err.log'
$ViteOverride = Join-Path $Frontend 'vite.orion-v3.config.ts'

if (-not (Test-Path $Donor)) {
    Fail 'OPENJARVIS_PIN' 'Pinned OpenJarvis checkout is missing.'
}
$DonorSha = (& git -C $Donor rev-parse HEAD).Trim()
if ($DonorSha -ne '309a4f1044ccfb2032264832a31fef2f1d314586') {
    Fail 'OPENJARVIS_PIN' ('Unexpected donor SHA: ' + $DonorSha)
}
Write-Host 'OPENJARVIS_PIN> PASS'

New-Item -ItemType Directory -Force -Path $SandboxOpenJarvis | Out-Null
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null

# Keep the isolated desktop inert. Never touch the user's real OpenJarvis HOME.
if (Test-Path $SandboxInference) {
    Remove-Item -LiteralPath $SandboxInference -Force
}
if (Test-Path $SandboxInference) {
    Fail 'DESKTOP_SANDBOX' 'Sandbox inference.json could not be cleared.'
}
Write-Host 'REAL_OPENJARVIS_HOME> UNTOUCHED'
Write-Host 'DESKTOP_SANDBOX_INFERENCE> ABSENT'

$tauriBin = Join-Path $Frontend 'node_modules\.bin\tauri.cmd'
if (-not (Test-Path $tauriBin)) {
    Fail 'TAURI_CLI' 'Local Tauri CLI is missing; run V3-RUN-004 dependency install first.'
}
Write-Host 'TAURI_CLI> FOUND'

@'
import { defineConfig, mergeConfig } from 'vite';
import baseConfig from './vite.config.ts';

export default mergeConfig(
  baseConfig,
  defineConfig({
    server: {
      watch: {
        ignored: ['**/src-tauri/target/**'],
      },
    },
  }),
);
'@ | Set-Content -LiteralPath $ViteOverride -Encoding UTF8

Write-Host 'VITE_RUST_TARGET_IGNORE> INSTALLED'

$OverridePath = Join-Path $RuntimeDir 'tauri-orion-v3.json'
@'
{
  "build": {
    "beforeDevCommand": "npx vite --config vite.orion-v3.config.ts"
  }
}
'@ | Set-Content -LiteralPath $OverridePath -Encoding UTF8

Remove-Item -LiteralPath $LaunchLog,$LaunchErr -Force -ErrorAction SilentlyContinue

# Clean only stale V3 desktop launchers from the previous isolated run.
# Match the exact V3 runtime script in the command line before killing any tree.
$stale = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -and (
        $_.CommandLine -like '*launch-openjarvis-v3.ps1*' -or
        $_.CommandLine -like '*launch-openjarvis-v3-visible.ps1*'
    )
}
foreach ($proc in $stale) {
    Write-Host ('STALE_V3_DESKTOP_LAUNCHER> CLEAN ' + $proc.ProcessId)
    & taskkill /PID $proc.ProcessId /T /F *> $null
}

$launchScript = Join-Path $RuntimeDir 'launch-openjarvis-v3-visible.ps1'
@(
    "`$env:HOME = '$SandboxHome'",
    "`$env:OPENJARVIS_ROOT = '$Donor'",
    "Set-Location '$Frontend'",
    "& '$tauriBin' dev --config '$OverridePath'"
) | Set-Content -LiteralPath $launchScript -Encoding UTF8

$launcher = Start-Process -FilePath 'powershell.exe' -ArgumentList @(
    '-NoProfile',
    '-ExecutionPolicy', 'Bypass',
    '-File', $launchScript
) -WindowStyle Hidden -RedirectStandardOutput $LaunchLog -RedirectStandardError $LaunchErr -PassThru

Write-Host ('DESKTOP_BUILD_LAUNCHER_PID> ' + $launcher.Id)

$deadline = (Get-Date).AddMinutes(4)
$visible = $null
while ((Get-Date) -lt $deadline) {
    $launcher.Refresh()
    $visible = Get-Process -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like '*OpenJarvis*'
    } | Select-Object -First 1

    if ($null -ne $visible) {
        break
    }

    if ($launcher.HasExited) {
        $detail = 'Tauri dev launcher exited before a visible OpenJarvis window appeared.'
        if ($null -ne $launcher.ExitCode) {
            $detail += ' Exit code ' + $launcher.ExitCode + '.'
        }
        Fail 'DESKTOP_VISIBLE_WINDOW' $detail
    }

    Start-Sleep -Seconds 2
}

if ($null -eq $visible) {
    Fail 'DESKTOP_VISIBLE_WINDOW' 'No visible OpenJarvis top-level window appeared before the verification deadline.'
}

$visible.Refresh()
Write-Host ('OPENJARVIS_WINDOW_PID> ' + $visible.Id)
Write-Host ('OPENJARVIS_WINDOW_TITLE> ' + $visible.MainWindowTitle)
Write-Host 'OPENJARVIS_VISIBLE_WINDOW> PASS'
Remove-Item -LiteralPath $ViteOverride -Force -ErrorAction SilentlyContinue
Write-Host 'VITE_OVERRIDE_CLEANUP> PASS'

# Verify the sandbox still has no confirmed source. The UI may write a pending
# file only after explicit user interaction; a confirmed source here would mean
# the desktop silently crossed the authority boundary.
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
            Fail 'DESKTOP_INERT_GUARD' 'Visible desktop has a confirmed standalone inference source.'
        }
    } catch {
        Fail 'DESKTOP_INERT_GUARD' 'Sandbox inference state is unreadable.'
    }
}
Write-Host 'DESKTOP_INERT_GUARD> PASS'

# The stock desktop should not have booted its managed API server in the
# isolated unconfigured HOME.
$port8000 = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue
if ($null -ne $port8000) {
    Write-Host 'JARVIS_PORT_8000> ALREADY_OR_EXTERNALLY_IN_USE'
} else {
    Write-Host 'JARVIS_PORT_8000> NOT_LISTENING'
}

Write-Host 'DESKTOP_UI_VISIBLE> PASS'
Write-Host 'STATUS> PASS'
exit 0
