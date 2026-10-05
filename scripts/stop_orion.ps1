param(
    [int]$PreserveLauncherPid = 0
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateRoot = Join-Path $env:LOCALAPPDATA "ORION-V3"
$PidFile = Join-Path $StateRoot "product-ui.pid"
$PairCodeFile = Join-Path $StateRoot "pair-code.txt"
$LauncherPidFile = Join-Path $StateRoot "launcher.pid"
$ReadyFile = Join-Path $StateRoot "desktop-ready.json"
$ErrorFile = Join-Path $StateRoot "desktop-error.log"
$ZeroTierUiOwner = Join-Path $StateRoot "zerotier-ui-owner.json"
$UiExe = Join-Path $Repo "dist\windows\ORION.exe"

function Stop-ProcessTree {
    param(
        [Parameter(Mandatory=$true)][int]$ProcessId,
        [Parameter(Mandatory=$true)][string]$Label
    )

    if ($ProcessId -eq $PID -or ($PreserveLauncherPid -gt 0 -and $ProcessId -eq $PreserveLauncherPid)) {
        return
    }

    $proc = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $ProcessId) -ErrorAction SilentlyContinue
    if (!$proc) { return }

    Write-Host ("Stopping " + $Label + " PID " + $ProcessId + "...")
    & taskkill.exe /PID $ProcessId /T /F 2>$null | Out-Null
}

Write-Host ""
Write-Host "Stopping ORION..." -ForegroundColor Cyan

# Native ORION window(s), exact executable path only.
$uiProcesses = @(
    Get-CimInstance Win32_Process -Filter "Name='ORION.exe'" -ErrorAction SilentlyContinue |
        Where-Object {
            $_.ExecutablePath -and
            $_.ExecutablePath -ieq $UiExe
        }
)

foreach ($proc in $uiProcesses) {
    Stop-ProcessTree -ProcessId ([int]$proc.ProcessId) -Label "ORION UI"
}

# ORION product runtime.
$serverPids = @()

if (Test-Path -LiteralPath $PidFile -PathType Leaf) {
    $rawPid = Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($rawPid -match '^\d+$') {
        $candidate = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $rawPid) -ErrorAction SilentlyContinue
        if (
            $candidate -and
            $candidate.CommandLine -and
            $candidate.CommandLine -match 'orion_v3[\\/]product_server\.py'
        ) {
            $serverPids += [int]$rawPid
        }
    }
}

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -match '^python(w)?\.exe$' -and
        $_.CommandLine -and
        $_.CommandLine -match 'orion_v3[\\/]product_server\.py'
    } |
    ForEach-Object {
        $pidValue = [int]$_.ProcessId
        if ($serverPids -notcontains $pidValue) { $serverPids += $pidValue }
    }

foreach ($pidValue in $serverPids) {
    Stop-ProcessTree -ProcessId $pidValue -Label "ORION runtime"
}

Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PairCodeFile -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $ReadyFile -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $ErrorFile -Force -ErrorAction SilentlyContinue

# Close ZeroTier desktop UI only if ORION opened that exact process.
if (Test-Path -LiteralPath $ZeroTierUiOwner -PathType Leaf) {
    try {
        $owner = Get-Content -LiteralPath $ZeroTierUiOwner -Raw | ConvertFrom-Json
        $owned = Get-CimInstance Win32_Process -Filter ("ProcessId=" + [int]$owner.pid) -ErrorAction SilentlyContinue

        if (
            $owned -and
            $owned.Name -ieq "zerotier_desktop_ui.exe" -and
            $owned.ExecutablePath -and
            $owned.ExecutablePath -ieq [string]$owner.executable -and
            [string]$owner.opened_by -eq "ORION-V3"
        ) {
            Write-Host ("Closing ORION-opened ZeroTier desktop UI PID " + $owned.ProcessId + "...")
            & taskkill.exe /PID ([int]$owned.ProcessId) /F 2>$null | Out-Null
            Write-Host "ZEROTIER_UI> CLOSED (ORION-owned UI only)" -ForegroundColor Green
        } else {
            Write-Host "ZEROTIER_UI> ownership record stale; no unrelated process killed." -ForegroundColor DarkGray
        }
    } catch {
        Write-Host ("ZEROTIER_UI> ownership record unreadable: " + $_.Exception.Message) -ForegroundColor Yellow
    } finally {
        Remove-Item -LiteralPath $ZeroTierUiOwner -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "ZEROTIER_UI> LEFT OPEN (not owned by ORION)" -ForegroundColor DarkGray
}

# Kill stale hidden lifecycle host(s), except the one currently performing cleanup.
$launcherProcesses = @(
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^(powershell|pwsh)\.exe$' -and
            $_.CommandLine -and
            $_.CommandLine -match 'scripts[\\/]start_orion\.ps1'
        }
)

foreach ($proc in $launcherProcesses) {
    Stop-ProcessTree -ProcessId ([int]$proc.ProcessId) -Label "ORION lifecycle host"
}

Remove-Item -LiteralPath $LauncherPidFile -Force -ErrorAction SilentlyContinue

Start-Sleep -Milliseconds 350

$remainingUi = @(
    Get-CimInstance Win32_Process -Filter "Name='ORION.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -and $_.ExecutablePath -ieq $UiExe }
)
$remainingServer = @(
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^python(w)?\.exe$' -and
            $_.CommandLine -and
            $_.CommandLine -match 'orion_v3[\\/]product_server\.py'
        }
)

if ($remainingUi.Count -gt 0 -or $remainingServer.Count -gt 0) {
    throw (
        "ORION_STOP> FAIL | UI=" + $remainingUi.Count +
        " RUNTIME=" + $remainingServer.Count
    )
}

Write-Host "ORION_STOP> PASS | UI=0 RUNTIME=0" -ForegroundColor Green
Write-Host "ZEROTIER_SERVICE> LEFT RUNNING/UNCHANGED (shared transport)" -ForegroundColor DarkGray
