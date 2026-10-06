param(
    [Parameter(Mandatory=$true)][string]$ExpectedCommit,
    [Parameter(Mandatory=$true)][string]$PreviousCommit,
    [switch]$Worker,
    [string]$TaskName = ""
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateRoot = Join-Path $env:LOCALAPPDATA "ORION-V3"
$StatusPath = Join-Path $StateRoot "update-status.json"
$LogPath = Join-Path $StateRoot "update-main.log"
$StageRoot = Join-Path $StateRoot "update-stage"
$StageWindows = Join-Path $StageRoot "windows"
$BackupRoot = Join-Path $StateRoot "update-backup"
$BackupWindows = Join-Path $BackupRoot "windows"
$LiveWindows = Join-Path $Repo "dist\windows"

New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null

function Write-Status {
    param(
        [Parameter(Mandatory=$true)][string]$State,
        [string]$Message = "",
        [string]$Commit = ""
    )
    @{
        schema = "orion-v3.update-status/1"
        state = $State
        message = $Message
        commit = $Commit
        updated_at = [DateTimeOffset]::Now.ToString("O")
    } | ConvertTo-Json | Set-Content -LiteralPath $StatusPath -Encoding UTF8
}

function Log([string]$Message) {
    Add-Content -LiteralPath $LogPath -Encoding UTF8 -Value (
        "[" + [DateTimeOffset]::Now.ToString("O") + "] " + $Message
    )
}

function Remove-OwnTask {
    if (!$TaskName) { return }
    try {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    } catch {
        try { & schtasks.exe /Delete /TN $TaskName /F 2>$null | Out-Null } catch {}
    }
}

if (!$Worker) {
    $task = "ORION-V3-Update-" + [Guid]::NewGuid().ToString("N")
    $identity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
    $powerShellExe = (Get-Process -Id $PID).Path

    $args = @(
        "-NoProfile",
        "-ExecutionPolicy","Bypass",
        "-WindowStyle","Hidden",
        "-File",('"' + $PSCommandPath + '"'),
        "-ExpectedCommit",$ExpectedCommit,
        "-PreviousCommit",$PreviousCommit,
        "-Worker",
        "-TaskName",$task
    ) -join " "

    try {
        $action = New-ScheduledTaskAction -Execute $powerShellExe -Argument $args
        $trigger = New-ScheduledTaskTrigger -Once -At ((Get-Date).AddYears(1))
        $principal = New-ScheduledTaskPrincipal -UserId $identity -LogonType Interactive -RunLevel Limited
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
        Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
        Start-ScheduledTask -TaskName $task
    }
    catch {
        Write-Status -State "failed" -Message ("Could not arm Windows update task: " + $_.Exception.Message) -Commit $ExpectedCommit
        try { Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue } catch {}
        exit 1
    }

    $deadline = (Get-Date).AddSeconds(8)
    $ack = $false
    do {
        Start-Sleep -Milliseconds 150
        if (Test-Path -LiteralPath $StatusPath -PathType Leaf) {
            try {
                $status = Get-Content -LiteralPath $StatusPath -Raw | ConvertFrom-Json
                if (
                    [string]$status.commit -eq $ExpectedCommit -and
                    [string]$status.state -in @("testing","building","restarting","starting","verifying","pass","failed")
                ) {
                    $ack = $true
                    break
                }
            } catch {}
        }
    } while ((Get-Date) -lt $deadline)

    if (!$ack) {
        Write-Status -State "failed" -Message "Windows update task was created but did not acknowledge." -Commit $ExpectedCommit
        try { Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue } catch {}
        exit 1
    }

    Write-Host "ORION_UPDATE_WORKER> STARTED"
    Write-Host ("TARGET_COMMIT> " + $ExpectedCommit)
    exit 0
}

Remove-Item -LiteralPath $LogPath -Force -ErrorAction SilentlyContinue
$ActivatedWindows = $false
$Stopped = $false

function Restore-Previous {
    Log "Attempting previous ORION recovery."

    try {
        $head = (& git.exe -C $Repo rev-parse HEAD).Trim()
        if ($LASTEXITCODE -eq 0 -and $head -eq $ExpectedCommit -and $PreviousCommit -and $PreviousCommit -ne $ExpectedCommit) {
            & git.exe -C $Repo reset --hard $PreviousCommit *>> $LogPath
        }
    } catch {
        Log ("Source rollback warning: " + $_.Exception.Message)
    }

    if ($ActivatedWindows -and (Test-Path -LiteralPath $BackupWindows -PathType Container)) {
        try {
            Remove-Item -LiteralPath $LiveWindows -Recurse -Force -ErrorAction SilentlyContinue
            Move-Item -LiteralPath $BackupWindows -Destination $LiveWindows
        } catch {
            Log ("Windows build rollback warning: " + $_.Exception.Message)
        }
    }

    try {
        & cmd.exe /d /c ('"' + (Join-Path $Repo "START ORION.bat") + '"') *>> $LogPath
    } catch {
        Log ("Recovery start warning: " + $_.Exception.Message)
    }
}

try {
    Start-Sleep -Milliseconds 800

    $head = (& git.exe -C $Repo rev-parse HEAD).Trim()
    if ($LASTEXITCODE -ne 0 -or $head -ne $ExpectedCommit) {
        throw "Updated ORION source no longer matches the approved target commit."
    }

    Write-Status -State "testing" -Message "Running ORION regression gates" -Commit $ExpectedCommit
    Log "Running chat-history regression."
    & python.exe (Join-Path $Repo "src\orion_v3\modules\chat_history_test.py") *>> $LogPath
    if ($LASTEXITCODE -ne 0) { throw "Chat-history regression failed." }

    Log "Running STRATA regression suite."
    Push-Location (Join-Path $Repo "ui\strata")
    try {
        & python.exe "tests\run_tests.py" --no-browser *>> $LogPath
        if ($LASTEXITCODE -ne 0) { throw "STRATA regression suite failed." }
    } finally {
        Pop-Location
    }

    Write-Status -State "building" -Message "Building staged PC UI and latest Android APK" -Commit $ExpectedCommit

    Remove-Item -LiteralPath $StageRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $StageRoot | Out-Null

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo "scripts\build_desktop.ps1") -OutputDirectory $StageWindows *>> $LogPath
    if ($LASTEXITCODE -ne 0) { throw "Updated ORION desktop build failed." }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo "android\scripts\build.ps1") *>> $LogPath
    if ($LASTEXITCODE -ne 0) { throw "Updated ORION Android build failed." }

    $apk = Join-Path $Repo "dist\ORION-V3-debug.apk"
    if (!(Test-Path -LiteralPath $apk -PathType Leaf)) {
        throw "Updated Android APK was not produced."
    }

    Write-Status -State "restarting" -Message "Activating tested ORION build" -Commit $ExpectedCommit

    Remove-Item -LiteralPath $BackupRoot -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

    if (Test-Path -LiteralPath $LiveWindows -PathType Container) {
        Move-Item -LiteralPath $LiveWindows -Destination $BackupWindows
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo "scripts\stop_orion.ps1") *>> $LogPath
    $Stopped = $true
    if ($LASTEXITCODE -ne 0) { throw "Current ORION did not stop cleanly." }

    Move-Item -LiteralPath $StageWindows -Destination $LiveWindows
    $ActivatedWindows = $true
    Remove-Item -LiteralPath $StageRoot -Recurse -Force -ErrorAction SilentlyContinue

    Write-Status -State "starting" -Message "Starting updated ORION" -Commit $ExpectedCommit
    & cmd.exe /d /c ('"' + (Join-Path $Repo "START ORION.bat") + '"') *>> $LogPath
    if ($LASTEXITCODE -ne 0) { throw "ORION restart launcher failed." }

    Write-Status -State "verifying" -Message "Waiting for updated ORION runtime" -Commit $ExpectedCommit
    $running = ""
    for ($i=0; $i -lt 80; $i++) {
        Start-Sleep -Milliseconds 350
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8890/api/health" -TimeoutSec 2
            $running = [string]$health.running_commit
            if ($health.ok -and $running -eq $ExpectedCommit) { break }
        } catch {}
    }

    if ($running -ne $ExpectedCommit) {
        throw ("Updated ORION runtime did not report expected commit " + $ExpectedCommit + ".")
    }

    Remove-Item -LiteralPath $BackupRoot -Recurse -Force -ErrorAction SilentlyContinue
    Write-Status -State "pass" -Message "ORION PC restarted; latest Android APK is ready to install." -Commit $ExpectedCommit
    Log ("UPDATE PASS " + $ExpectedCommit)
    Remove-OwnTask
}
catch {
    $message = $_.Exception.Message
    Log ("UPDATE FAIL " + $message)

    if ($Stopped) {
        try {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo "scripts\stop_orion.ps1") *>> $LogPath
        } catch {}
    }

    Restore-Previous
    Write-Status -State "failed" -Message ($message + " | previous ORION recovery attempted") -Commit $PreviousCommit
    Remove-OwnTask
    exit 1
}
