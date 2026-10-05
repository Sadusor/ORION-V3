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
    & $Adb shell uiautomator dump /sdcard/orion-v3-ui.xml | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "uiautomator dump failed." }
    return (& $Adb shell cat /sdcard/orion-v3-ui.xml) -join "`n"
}

$adb = Resolve-Adb
$devices = @(& $adb devices) | Where-Object { $_ -match "\tdevice$" }
if (@($devices).Count -lt 1) {
    throw "ORION_ANDROID_SMOKE> FAIL | no authorized Android device"
}

Write-Host "ORION_ANDROID_DEVICE> PASS" -ForegroundColor Green

& $adb logcat -c | Out-Null
& $adb shell am force-stop com.sadusor.orionv3 | Out-Null
& $adb shell monkey -p com.sadusor.orionv3 -c android.intent.category.LAUNCHER 1 | Out-Null
Start-Sleep -Seconds 4

$ui = Dump-Ui $adb

if (($ui -match "OPEN ORION") -or ($ui -match "CHECK ORION") -or ($ui -match "OPEN ZEROTIER")) {
    throw "ORION_ANDROID_DIRECT_UI> FAIL | obsolete launcher/dashboard detected"
}

$realSurface =
    ($ui -match "Pair this device") -or
    ($ui -match "Ask ORION") -or
    ($ui -match "CONNECTING") -or
    ($ui -match "ORION")

if (!$realSurface) {
    $logs = (& $adb logcat -d -s ORIONV3:I chromium:E "*:S") -join "`n"
Write-Host ""
Write-Host "===== ORION ANDROID WEBVIEW LOG =====" -ForegroundColor Cyan
Write-Host $logs

if ($logs -match "DOM probe:") {
    Write-Host "ORION_ANDROID_DOM_PROBE> PASS" -ForegroundColor Green
} else {
    Write-Host "ORION_ANDROID_DOM_PROBE> FAIL | no DOM probe from loaded page" -ForegroundColor Red
}

if ($logs -match "JS .*Uncaught|JS .*ReferenceError|JS .*TypeError|chromium.*ERROR") {
    throw "ORION_ANDROID_WEBVIEW> FAIL | JavaScript/WebView error detected"
}

Write-Host "ORION_ANDROID_SMOKE> PASS" -ForegroundColor Green
