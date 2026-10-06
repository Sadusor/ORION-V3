param(
    [switch]$Install,
    [switch]$BundleOfflineModel,
    [switch]$SkipOfflineModel,
    [string]$GradleVersion = "8.10.2"
)

$ErrorActionPreference = "Stop"
$AndroidRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RepoRoot = (Resolve-Path (Join-Path $AndroidRoot "..")).Path

function Resolve-Java {
    if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME "bin\java.exe"))) {
        return $env:JAVA_HOME
    }
    foreach ($candidate in @(
        "$env:ProgramFiles\Android\Android Studio\jbr",
        "$env:ProgramFiles\Android\Android Studio\jre"
    )) {
        if ($candidate -and (Test-Path (Join-Path $candidate "bin\java.exe"))) {
            return $candidate
        }
    }
    $java = Get-Command java.exe -ErrorAction SilentlyContinue
    if ($java) {
        return (Split-Path (Split-Path $java.Source -Parent) -Parent)
    }
    throw "Java 17+ was not found. Install Android Studio or set JAVA_HOME."
}

function Resolve-AndroidSdkRoot {
    foreach ($candidate in @(
        $env:ANDROID_SDK_ROOT,
        $env:ANDROID_HOME,
        "E:\Android\Sdk",
        (Join-Path $env:LOCALAPPDATA "Android\Sdk")
    )) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }
    throw "Android SDK root was not found."
}

function Resolve-Adb([string]$SdkRoot) {
    $adb = Get-Command adb.exe -ErrorAction SilentlyContinue
    if ($adb) { return $adb.Source }
    $candidate = Join-Path $SdkRoot "platform-tools\adb.exe"
    if (Test-Path $candidate) { return $candidate }
    throw "adb.exe was not found."
}

function Test-ModelHash([string]$Path, [string]$ExpectedSha256) {
    if (!(Test-Path -LiteralPath $Path -PathType Leaf)) { return $false }
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant() -eq $ExpectedSha256
}

function Prepare-OfflineModelAsset([string]$AndroidRoot, [bool]$Bundle) {
    $modelName = "Qwen3-0.6B-Q4_0.gguf"
    $modelUrl = "https://huggingface.co/ggml-org/Qwen3-0.6B-GGUF/resolve/main/Qwen3-0.6B-Q4_0.gguf"
    $expectedSha256 = "DA2572F16C06133561CE56ACCAA822216F2391EF4D37FBA427801CD6736417D4"
    $assetDir = Join-Path $AndroidRoot "app\src\main\assets\models"
    $assetPath = Join-Path $assetDir $modelName
    $cacheDir = Join-Path $env:LOCALAPPDATA "ORION-V3\models"
    $cachePath = Join-Path $cacheDir $modelName
    $partial = "$cachePath.partial"

    New-Item -ItemType Directory -Force -Path $assetDir, $cacheDir | Out-Null

    # Preserve a previously downloaded build copy before externalizing it.
    if (!(Test-ModelHash $cachePath $expectedSha256) -and
        (Test-ModelHash $assetPath $expectedSha256)) {
        Copy-Item -LiteralPath $assetPath -Destination $cachePath -Force
    }

    if (!$Bundle) {
        Remove-Item -LiteralPath $assetPath -Force -ErrorAction SilentlyContinue
        Write-Host "ORION_OFFLINE_MODEL> EXTERNALIZED (normal APK does not bundle GGUF)" -ForegroundColor Green
        return
    }

    if (!(Test-ModelHash $cachePath $expectedSha256)) {
        Remove-Item -LiteralPath $cachePath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue
        Write-Host "Downloading one-time bundled offline model ($modelName, about 429 MB)..." -ForegroundColor Cyan
        Invoke-WebRequest -Uri $modelUrl -OutFile $partial
        if (!(Test-ModelHash $partial $expectedSha256)) {
            Remove-Item -LiteralPath $partial -Force -ErrorAction SilentlyContinue
            throw "Offline model SHA256 verification failed."
        }
        Move-Item -LiteralPath $partial -Destination $cachePath -Force
    }

    Copy-Item -LiteralPath $cachePath -Destination $assetPath -Force
    if (!(Test-ModelHash $assetPath $expectedSha256)) {
        throw "Bundled offline model asset SHA256 verification failed."
    }
    Write-Host "ORION_OFFLINE_MODEL> BUNDLED ($modelName)" -ForegroundColor Green
}

$env:JAVA_HOME = Resolve-Java
$env:Path = "$env:JAVA_HOME\bin;$env:Path"
$sdkRoot = Resolve-AndroidSdkRoot

if ($BundleOfflineModel -and $SkipOfflineModel) {
    throw "Use either -BundleOfflineModel or -SkipOfflineModel, not both."
}
$bundleModel = $BundleOfflineModel -and !$SkipOfflineModel
Prepare-OfflineModelAsset $AndroidRoot $bundleModel

$localProperties = Join-Path $AndroidRoot "local.properties"
$sdkForGradle = $sdkRoot.Replace("\", "\\")
Set-Content -LiteralPath $localProperties -Encoding ASCII -Value "sdk.dir=$sdkForGradle"

$cache = Join-Path $env:LOCALAPPDATA "ORION-V3\gradle"
$zip = Join-Path $cache "gradle-$GradleVersion-bin.zip"
$gradleHome = Join-Path $cache "gradle-$GradleVersion"
$gradleBat = Join-Path $gradleHome "bin\gradle.bat"
New-Item -ItemType Directory -Force -Path $cache | Out-Null

if (!(Test-Path $gradleBat)) {
    if (!(Test-Path $zip)) {
        Write-Host "Downloading Gradle $GradleVersion..." -ForegroundColor Cyan
        Invoke-WebRequest "https://services.gradle.org/distributions/gradle-$GradleVersion-bin.zip" -OutFile $zip
    }
    if (Test-Path $gradleHome) { Remove-Item $gradleHome -Recurse -Force }
    Expand-Archive -Path $zip -DestinationPath $cache -Force
}

$logDir = Join-Path $env:LOCALAPPDATA "ORION-V3\android"
$buildLog = Join-Path $logDir "build.log"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
Remove-Item $buildLog -Force -ErrorAction SilentlyContinue

Write-Host "Building ORION V3 APK..." -ForegroundColor Cyan
Push-Location $AndroidRoot
try {
    & $gradleBat --no-daemon :app:assembleDebug --stacktrace 2>&1 |
        Tee-Object -FilePath $buildLog
    $gradleExit = $LASTEXITCODE
    if ($gradleExit -ne 0) {
        Write-Host ""
        Write-Host "===== ORION V3 Android build failure summary =====" -ForegroundColor Red
        $matches = Select-String -Path $buildLog -Pattern @(
            "^e: ",
            "^error:",
            "FAILURE:",
            "What went wrong:",
            "Execution failed for task",
            "Could not resolve",
            "SDK location not found",
            "Unresolved reference",
            "Compilation error"
        ) -Context 2,4 -ErrorAction SilentlyContinue
        if ($matches) {
            $matches | Select-Object -Last 14 | ForEach-Object { Write-Host $_.ToString() }
        } else {
            Get-Content $buildLog -Tail 100 -ErrorAction SilentlyContinue
        }
        throw "Gradle build failed with exit code $gradleExit. Full log: $buildLog"
    }
} finally {
    Pop-Location
}

$apk = Join-Path $AndroidRoot "app\build\outputs\apk\debug\app-debug.apk"
if (!(Test-Path $apk)) {
    throw "APK was not created at expected path: $apk"
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($apk)
try {
    $ggufEntries = @($zip.Entries | Where-Object { $_.FullName -like "*.gguf" })
} finally {
    $zip.Dispose()
}
if ($bundleModel -and $ggufEntries.Count -lt 1) {
    throw "Bundled-model build is missing the GGUF asset."
}
if (!$bundleModel -and $ggufEntries.Count -gt 0) {
    throw "Normal update APK unexpectedly contains a GGUF model."
}
Write-Host ("ORION_APK_MODEL_POLICY> " + $(if ($bundleModel) { "BUNDLED" } else { "EXTERNALIZED" })) -ForegroundColor Green

$dist = Join-Path $RepoRoot "dist"
New-Item -ItemType Directory -Force -Path $dist | Out-Null
$distApk = Join-Path $dist "ORION-V3-debug.apk"
Copy-Item -LiteralPath $apk -Destination $distApk -Force

Write-Host ""
$apkMb = [Math]::Round((Get-Item -LiteralPath $distApk).Length / 1MB, 1)
Write-Host ("ORION_APK_MB> " + $apkMb)
Write-Host "ORION_V3_APK> PASS" -ForegroundColor Green
Write-Host ("APK> " + $distApk)
Write-Host "PACKAGE> com.sadusor.orionv3"

if ($Install) {
    $adb = Resolve-Adb $sdkRoot
    $deviceLines = @(& $adb devices) | Where-Object { $_ -match "\tdevice$" }
    if (@($deviceLines).Count -lt 1) {
        throw "No authorized Android device found."
    }

    Write-Host "Installing ORION V3..." -ForegroundColor Cyan
    & $adb install -r $distApk
    if ($LASTEXITCODE -ne 0) { throw "adb install failed with exit code $LASTEXITCODE." }

    & $adb shell am force-stop com.sadusor.orionv3 | Out-Null
    & $adb shell monkey -p com.sadusor.orionv3 -c android.intent.category.LAUNCHER 1 | Out-Null

    Write-Host "ORION_V3_ANDROID_INSTALL> PASS" -ForegroundColor Green
}
