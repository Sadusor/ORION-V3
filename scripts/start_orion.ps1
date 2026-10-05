param(
    [int]$Port = 8890
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$StateRoot = Join-Path $env:LOCALAPPDATA "ORION-V3"
$LauncherPidFile = Join-Path $StateRoot "launcher.pid"
$ZeroTierUiOwner = Join-Path $StateRoot "zerotier-ui-owner.json"
$OllamaOwner = Join-Path $StateRoot "ollama-owner.json"
$UiExe = Join-Path $Repo "dist\windows\ORION.exe"
$StartProduct = Join-Path $Repo "scripts\start_product_ui.ps1"
$StopOrion = Join-Path $Repo "scripts\stop_orion.ps1"
$LifecycleLog = Join-Path $StateRoot "launcher.log"

New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null

function Log([string]$Message) {
    Add-Content -LiteralPath $LifecycleLog -Encoding UTF8 -Value (([DateTimeOffset]::Now.ToString("O")) + " " + $Message)
}

function Get-OrionUi {
    return @(
        Get-CimInstance Win32_Process -Filter "Name='ORION.exe'" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.ExecutablePath -and
                $_.ExecutablePath -ieq $UiExe
            }
    )
}

function Open-ZeroTierDesktop {
    $candidates = @(
        "C:\Program Files (x86)\ZeroTier\One\zerotier_desktop_ui.exe",
        "C:\Program Files\ZeroTier\One\zerotier_desktop_ui.exe"
    )

    $exe = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    if (!$exe) {
        Remove-Item -LiteralPath $ZeroTierUiOwner -Force -ErrorAction SilentlyContinue
        return @{ Open = $false; Owned = $false; Pid = $null }
    }

    $running = @(Get-CimInstance Win32_Process -Filter "Name='zerotier_desktop_ui.exe'" -ErrorAction SilentlyContinue)
    if ($running.Count -gt 0) {
        Remove-Item -LiteralPath $ZeroTierUiOwner -Force -ErrorAction SilentlyContinue
        return @{ Open = $true; Owned = $false; Pid = [int]$running[0].ProcessId }
    }

    $started = Start-Process -FilePath $exe -PassThru
    Start-Sleep -Milliseconds 500

    $live = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $started.Id) -ErrorAction SilentlyContinue
    if (!$live) {
        $live = Get-CimInstance Win32_Process -Filter "Name='zerotier_desktop_ui.exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.ExecutablePath -and $_.ExecutablePath -ieq $exe } |
            Select-Object -First 1
    }

    if (!$live) {
        Remove-Item -LiteralPath $ZeroTierUiOwner -Force -ErrorAction SilentlyContinue
        return @{ Open = $false; Owned = $false; Pid = $null }
    }

    @{
        pid = [int]$live.ProcessId
        executable = $exe
        opened_by = "ORION-V3"
        opened_at = [DateTimeOffset]::Now.ToString("O")
    } | ConvertTo-Json | Set-Content -LiteralPath $ZeroTierUiOwner -Encoding UTF8

    return @{ Open = $true; Owned = $true; Pid = [int]$live.ProcessId }
}

function Get-ZeroTierStatus {
    $service = Get-Service -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match "ZeroTier" -or $_.DisplayName -match "ZeroTier" } |
        Select-Object -First 1

    $adapter = Get-NetAdapter -ErrorAction SilentlyContinue |
        Where-Object {
            ($_.Name -match "ZeroTier" -or $_.InterfaceDescription -match "ZeroTier") -and
            $_.Status -eq "Up"
        } |
        Select-Object -First 1

    if ($service -and $service.Status -eq "Running" -and $adapter) {
        $ip = Get-NetIPAddress -InterfaceIndex $adapter.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object {
                $_.AddressState -eq "Preferred" -and
                $_.IPAddress -notmatch "^169\.254\."
            } |
            Select-Object -ExpandProperty IPAddress -First 1
        return @{ Online = $true; Ip = $ip }
    }

    return @{ Online = $false; Ip = $null }
}
function Test-OllamaApi {
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:11434/api/tags" -Method Get -TimeoutSec 2
        return $null -ne $response
    } catch {
        return $false
    }
}

function Resolve-OllamaExe {
    $cmd = Get-Command ollama.exe -ErrorAction SilentlyContinue
    if ($cmd -and (Test-Path -LiteralPath $cmd.Source -PathType Leaf)) {
        return $cmd.Source
    }

    foreach ($candidate in @(
        (Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"),
        "C:\Program Files\Ollama\ollama.exe"
    )) {
        if ($candidate -and (Test-Path -LiteralPath $candidate -PathType Leaf)) {
            return $candidate
        }
    }

    return $null
}

function Ensure-Ollama {
    if (Test-OllamaApi) {
        Remove-Item -LiteralPath $OllamaOwner -Force -ErrorAction SilentlyContinue
        return @{ Online = $true; Owned = $false; Pid = $null; Reason = "pre-existing" }
    }

    $existing = @(
        Get-CimInstance Win32_Process -Filter "Name='ollama.exe'" -ErrorAction SilentlyContinue
    )

    if ($existing.Count -gt 0) {
        for ($i = 0; $i -lt 20; $i++) {
            Start-Sleep -Milliseconds 250
            if (Test-OllamaApi) {
                Remove-Item -LiteralPath $OllamaOwner -Force -ErrorAction SilentlyContinue
                return @{ Online = $true; Owned = $false; Pid = [int]$existing[0].ProcessId; Reason = "pre-existing" }
            }
        }

        Remove-Item -LiteralPath $OllamaOwner -Force -ErrorAction SilentlyContinue
        return @{ Online = $false; Owned = $false; Pid = [int]$existing[0].ProcessId; Reason = "existing-process-not-ready" }
    }

    $exe = Resolve-OllamaExe
    if (!$exe) {
        Remove-Item -LiteralPath $OllamaOwner -Force -ErrorAction SilentlyContinue
        return @{ Online = $false; Owned = $false; Pid = $null; Reason = "ollama.exe-not-found" }
    }

    $ollamaLog = Join-Path $StateRoot "ollama-serve.log"
    $ollamaErr = Join-Path $StateRoot "ollama-serve.err.log"
    Remove-Item -LiteralPath $ollamaLog -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $ollamaErr -Force -ErrorAction SilentlyContinue

    $startArgs = @{
        FilePath = $exe
        ArgumentList = @("serve")
        WindowStyle = "Hidden"
        RedirectStandardOutput = $ollamaLog
        RedirectStandardError = $ollamaErr
        PassThru = $true
    }
    $started = Start-Process @startArgs

    $online = $false
    for ($i = 0; $i -lt 40; $i++) {
        Start-Sleep -Milliseconds 250

        $started.Refresh()
        if ($started.HasExited) {
            break
        }

        if (Test-OllamaApi) {
            $online = $true
            break
        }
    }

    if (!$online) {
        if (!$started.HasExited) {
            & taskkill.exe /PID $started.Id /T /F 2>$null | Out-Null
        }
        Remove-Item -LiteralPath $OllamaOwner -Force -ErrorAction SilentlyContinue
        return @{ Online = $false; Owned = $false; Pid = $started.Id; Reason = "serve-failed" }
    }

    @{
        pid = [int]$started.Id
        executable = $exe
        command = "serve"
        opened_by = "ORION-V3"
        opened_at = [DateTimeOffset]::Now.ToString("O")
    } | ConvertTo-Json | Set-Content -LiteralPath $OllamaOwner -Encoding UTF8

    return @{ Online = $true; Owned = $true; Pid = [int]$started.Id; Reason = "started-by-orion" }
}

try {
    if (!(Test-Path -LiteralPath $UiExe -PathType Leaf)) {
        throw "Native ORION UI has not been built: $UiExe"
    }

    $existing = @(Get-OrionUi)
    if ($existing.Count -gt 0) {
        Log ("ORION_UI> ALREADY RUNNING PID " + $existing[0].ProcessId)
        exit 0
    }

    Set-Content -LiteralPath $LauncherPidFile -Encoding ASCII -Value $PID

    # Remove stale ORION runtime/ownership from an interrupted previous session.
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopOrion -PreserveLauncherPid $PID
    if ($LASTEXITCODE -ne 0) { throw "Could not clean stale ORION processes." }
    Set-Content -LiteralPath $LauncherPidFile -Encoding ASCII -Value $PID

    $ztUi = Open-ZeroTierDesktop
    $zt = Get-ZeroTierStatus

    if ($zt.Online) {
        Log ("ZEROTIER> ONLINE " + $zt.Ip)
    } else {
        Log "ZEROTIER> OFFLINE - PC ORION works; phone needs the private network."
    }

    if ($ztUi.Open) {
        if ($ztUi.Owned) {
            Log ("ZEROTIER_UI> OPEN OWNED_BY_ORION PID " + $ztUi.Pid)
        } else {
            Log ("ZEROTIER_UI> OPEN PRE_EXISTING PID " + $ztUi.Pid)
        }
    } else {
        Log "ZEROTIER_UI> NOT FOUND"
    }

    $ollama = Ensure-Ollama
    if ($ollama.Online) {
        if ($ollama.Owned) {
            Log ("OLLAMA> ONLINE OWNED_BY_ORION PID " + $ollama.Pid)
        } else {
            $ollamaPidText = if ($ollama.Pid) { " PID " + $ollama.Pid } else { "" }
            Log ("OLLAMA> ONLINE PRE_EXISTING" + $ollamaPidText)
        }
    } else {
        Log ("OLLAMA> WARN " + $ollama.Reason + " - ORION UI will continue; Local Brain is not ready.")
    }

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StartProduct -Port $Port -NoBrowser
    if ($LASTEXITCODE -ne 0) {
        throw "ORION runtime failed to start."
    }

    $ui = Start-Process -FilePath $UiExe -WorkingDirectory (Split-Path $UiExe -Parent) -PassThru
    Start-Sleep -Seconds 2
    $ui.Refresh()

    if ($ui.HasExited) {
        throw ("ORION native UI exited during startup with code " + $ui.ExitCode + ".")
    }

    Log ("ORION_UI> PASS PID " + $ui.Id)

    # Lifecycle ownership: closing the native ORION window closes this session.
    Wait-Process -Id $ui.Id -ErrorAction SilentlyContinue
    Log "ORION_UI> CLOSED BY OWNER"

    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopOrion -PreserveLauncherPid $PID
    if ($LASTEXITCODE -ne 0) {
        Log "ORION_CLEANUP> FAIL"
        exit 1
    }

    Log "ORION_CLEANUP> PASS"
}
catch {
    Log ("ORION_LAUNCH> FAIL " + $_.Exception.Message)
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $StopOrion -PreserveLauncherPid $PID | Out-Null
    } catch {}
    exit 1
}
finally {
    Remove-Item -LiteralPath $LauncherPidFile -Force -ErrorAction SilentlyContinue
}
