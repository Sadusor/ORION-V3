param()

$ErrorActionPreference = "Stop"

function Resolve-Adb {
    $adb = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($adb) { return $adb.Source }

    foreach ($root in @(
        $env:ANDROID_SDK_ROOT,
        $env:ANDROID_HOME,
        "E:\Android\Sdk",
        (Join-Path $env:LOCALAPPDATA "Android\Sdk")
    )) {
        if ($root) {
            $candidate = Join-Path $root "platform-tools\adb.exe"
            if (Test-Path -LiteralPath $candidate) { return $candidate }
        }
    }

    throw "adb.exe was not found."
}

function Dump-Ui([string]$Adb) {
    try {
        & $Adb shell uiautomator dump /sdcard/orion-v3-ui.xml | Out-Null
        if ($LASTEXITCODE -ne 0) { return "" }
        return ((& $Adb shell cat /sdcard/orion-v3-ui.xml) -join "`n")
    } catch {
        return ""
    }
}

$adb = Resolve-Adb
$devices = @(& $adb devices) | Where-Object { $_ -match "\tdevice$" }
if (@($devices).Count -lt 1) {
    throw "ORION_ANDROID_DEVICE> FAIL | no authorized Android device"
}
Write-Host "ORION_ANDROID_DEVICE> PASS" -ForegroundColor Green

& $adb logcat -c | Out-Null
& $adb shell am force-stop com.sadusor.orionv3 | Out-Null
& $adb shell monkey -p com.sadusor.orionv3 -c android.intent.category.LAUNCHER 1 | Out-Null
Start-Sleep -Seconds 5

$ui = Dump-Ui $adb
$logs = ((& $adb logcat -d -s ORIONV3:I chromium:E "*:S") -join "`n")
$logLines = @($logs -split "`r?`n")
$tileWarnings = @($logLines | Where-Object { $_ -match "tile memory limits exceeded" })
$displayLines = @($logLines | Where-Object { $_ -notmatch "tile memory limits exceeded" })

Write-Host ""
Write-Host "===== ORION ANDROID WEBVIEW LOG =====" -ForegroundColor Cyan
if ($displayLines.Count -gt 0) {
    $displayLines | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "(no non-tile ORION WebView log lines captured)"
}
if ($tileWarnings.Count -gt 0) {
    Write-Host ("ORION_ANDROID_TILE_MEMORY_COUNT> " + $tileWarnings.Count) -ForegroundColor Yellow
}

if (($ui -match "OPEN ORION") -or ($ui -match "CHECK ORION") -or ($ui -match "OPEN ZEROTIER")) {
    throw "ORION_ANDROID_DIRECT_UI> FAIL | obsolete launcher/dashboard detected"
}
Write-Host "ORION_ANDROID_NO_LAUNCHER> PASS" -ForegroundColor Green

if ($logs -notmatch "page started:") {
    throw "ORION_ANDROID_WEBVIEW_START> FAIL | WebView never started loading STRATA"
}
Write-Host "ORION_ANDROID_WEBVIEW_START> PASS" -ForegroundColor Green

if ($logs -notmatch "page finished:") {
    throw "ORION_ANDROID_WEBVIEW_FINISH> FAIL | STRATA main page never finished loading"
}
Write-Host "ORION_ANDROID_WEBVIEW_FINISH> PASS" -ForegroundColor Green

if ($logs -notmatch "DOM probe:") {
    throw "ORION_ANDROID_DOM> FAIL | no DOM probe from loaded STRATA page"
}
Write-Host "ORION_ANDROID_DOM_PROBE> PASS" -ForegroundColor Green

if ($logs -match '"app":false') {
    throw "ORION_ANDROID_DOM> FAIL | #app missing"
}
if ($logs -match '"core":false') {
    throw "ORION_ANDROID_DOM> FAIL | #core missing"
}
if ($logs -match '"composer":false') {
    throw "ORION_ANDROID_DOM> FAIL | Ask ORION composer missing"
}
Write-Host "ORION_ANDROID_STRATA_DOM> PASS" -ForegroundColor Green

if ($logs -match "JS .*Uncaught|JS .*ReferenceError|JS .*TypeError") {
    throw "ORION_ANDROID_WEBVIEW> FAIL | JavaScript error detected"
}
Write-Host "ORION_ANDROID_JS> PASS" -ForegroundColor Green

if ($tileWarnings.Count -gt 0) {
    Write-Host ("ORION_ANDROID_TILE_MEMORY> WARN | " + $tileWarnings.Count + " renderer-pressure messages; visual screenshot check decides PASS/FAIL.") -ForegroundColor Yellow
} else {
    Write-Host "ORION_ANDROID_TILE_MEMORY> PASS" -ForegroundColor Green
}

if (($ui -match "Pair this device") -or ($ui -match "Ask ORION") -or ($ui -match "ORION")) {
    Write-Host "ORION_ANDROID_ACCESSIBILITY> PASS" -ForegroundColor Green
} else {
    Write-Host "ORION_ANDROID_ACCESSIBILITY> WARN | WebView text was not exposed to UIAutomator" -ForegroundColor Yellow
}

$screenDir = Join-Path $env:LOCALAPPDATA "ORION-V3\android"
$screenPath = Join-Path $screenDir "orion-screen.png"
New-Item -ItemType Directory -Force -Path $screenDir | Out-Null
Remove-Item -LiteralPath $screenPath -Force -ErrorAction SilentlyContinue

& $adb shell screencap -p /sdcard/orion-screen.png | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "ORION_ANDROID_SCREENSHOT> FAIL | screencap failed"
}
& $adb pull /sdcard/orion-screen.png $screenPath | Out-Null
if ($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $screenPath -PathType Leaf)) {
    throw "ORION_ANDROID_SCREENSHOT> FAIL | pull failed"
}
Write-Host ("ORION_ANDROID_SCREENSHOT> PASS | " + $screenPath) -ForegroundColor Green

$checker = Join-Path $PSScriptRoot "check_screen.py"
$pythonCandidates = @(
    (Join-Path $env:LOCALAPPDATA "ORION-V3\icon-renderer\venv\Scripts\python.exe"),
    "python.exe",
    "py.exe"
)
$python = $null
foreach ($candidate in $pythonCandidates) {
    if ([System.IO.Path]::IsPathRooted($candidate)) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            $python = $candidate
            break
        }
    } else {
        $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
        if ($cmd) {
            $python = $cmd.Source
            break
        }
    }
}
if (!$python) {
    throw "ORION_ANDROID_VISUAL> FAIL | Python not found"
}

$oldPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $python $checker $screenPath 2>&1 | Out-Host
$visualExit = $LASTEXITCODE
$ErrorActionPreference = $oldPreference

if ($visualExit -ne 0) {
    throw "ORION_ANDROID_VISUAL> FAIL | screen is effectively black"
}
Write-Host "ORION_ANDROID_VISUAL> PASS" -ForegroundColor Green

Write-Host "ORION_ANDROID_SMOKE> PASS" -ForegroundColor Green
