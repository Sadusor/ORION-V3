param(
    [int]$Port = 8890,
    [switch]$NoBrowser
)

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$State = Join-Path $env:LOCALAPPDATA "ORION-V3"
$PidFile = Join-Path $State "product-ui.pid"
$OutLog = Join-Path $State "product-ui.out.log"
$ErrLog = Join-Path $State "product-ui.err.log"
New-Item -ItemType Directory -Force -Path $State | Out-Null

function Resolve-Python {
    foreach ($name in @("python.exe","py.exe")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    throw "Python 3.11+ not found."
}

function Stop-OldProductUi {
    $pids = @()
    if (Test-Path -LiteralPath $PidFile) {
        $raw = Get-Content -LiteralPath $PidFile -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($raw -match '^\d+$') { $pids += [int]$raw }
    }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Name -match '^python(w)?\.exe$' -and
            $_.CommandLine -and
            $_.CommandLine -match 'orion_v3[\\/]product_server\.py'
        } |
        ForEach-Object {
            if ($pids -notcontains [int]$_.ProcessId) { $pids += [int]$_.ProcessId }
        }
    foreach ($pidValue in $pids) {
        $p = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $pidValue) -ErrorAction SilentlyContinue
        if ($p -and $p.CommandLine -match 'orion_v3[\\/]product_server\.py') {
            & taskkill.exe /PID $pidValue /T /F 2>$null | Out-Null
        }
    }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
}

Stop-OldProductUi
$python = Resolve-Python
$pairCode = "{0:D6}" -f (Get-Random -Minimum 0 -Maximum 1000000)
$server = Join-Path $Repo "src\orion_v3\product_server.py"
if (!(Test-Path -LiteralPath $server)) { throw "Product server missing: $server" }

Remove-Item $OutLog,$ErrLog -Force -ErrorAction SilentlyContinue
$args = @($server, "--host", "0.0.0.0", "--port", [string]$Port, "--pair-code", $pairCode)
$proc = Start-Process -FilePath $python -WorkingDirectory $Repo -ArgumentList $args -WindowStyle Hidden -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog -PassThru

$health = $null
for ($i=0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 300
    try {
        $health = Invoke-RestMethod -Uri ("http://127.0.0.1:" + $Port + "/api/health") -TimeoutSec 2
        if ($health.ok) { break }
    } catch {}
}
if (!$health -or !$health.ok) {
    $err = if (Test-Path $ErrLog) { (Get-Content $ErrLog -Tail 40) -join [Environment]::NewLine } else { "" }
    throw ("ORION V3 product server did not become healthy." + [Environment]::NewLine + $err)
}

$ztIp = Get-NetAdapter -ErrorAction SilentlyContinue |
    Where-Object { ($_.Name -match "ZeroTier" -or $_.InterfaceDescription -match "ZeroTier") -and $_.Status -eq "Up" } |
    ForEach-Object {
        Get-NetIPAddress -InterfaceIndex $_.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object { $_.AddressState -eq "Preferred" -and $_.IPAddress -notmatch "^169\.254\." } |
            Select-Object -ExpandProperty IPAddress -First 1
    } |
    Select-Object -First 1

Write-Host ""
Write-Host "ORION_V3_PRODUCT_UI> PASS" -ForegroundColor Green
Write-Host ("RUNTIME_COMMIT> " + $health.running_commit) -ForegroundColor Green
Write-Host ("PAIR_CODE> " + $pairCode) -ForegroundColor Cyan
Write-Host ("PC_URL> http://127.0.0.1:" + $Port + "/v3/") -ForegroundColor Green
if ($ztIp) {
    Write-Host ("PHONE_URL> http://" + $ztIp + ":" + $Port + "/v3/") -ForegroundColor Green
} else {
    Write-Host ("PHONE_URL> use the PC private IP on port " + $Port + "/v3/") -ForegroundColor Yellow
}
Write-Host ("PID> " + $proc.Id)
Write-Host "PHASE_A> live UI + pairing + truthful read surfaces; actions not yet connected are refused." -ForegroundColor Yellow

if (!$NoBrowser) {
    Start-Process ("http://127.0.0.1:" + $Port + "/v3/")
}
