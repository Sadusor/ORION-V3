param(
    [string]$Configuration = "Release",
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Project = Join-Path $Repo "desktop\ORION.UI\ORION.csproj"
$Output = if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    Join-Path $Repo "dist\windows"
} else {
    [System.IO.Path]::GetFullPath($OutputDirectory)
}

if (!(Test-Path -LiteralPath $Project -PathType Leaf)) {
    throw "Native ORION project not found: $Project"
}

$dotnetCommand = Get-Command dotnet.exe -ErrorAction SilentlyContinue
$dotnetPath = if ($dotnetCommand) { $dotnetCommand.Source } else { $null }

if (!$dotnetPath) {
    $candidate = "C:\Program Files\dotnet\dotnet.exe"
    if (Test-Path -LiteralPath $candidate) { $dotnetPath = $candidate }
}

if (!$dotnetPath) {
    throw ".NET 8 SDK is required to build ORION."
}

$sdkLines = & $dotnetPath --list-sdks
if ($LASTEXITCODE -ne 0 -or -not ($sdkLines -match '^8\.')) {
    throw ".NET 8 SDK is required to build ORION."
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo "scripts\generate_windows_icon.ps1")
if ($LASTEXITCODE -ne 0) { throw "ORION Windows icon preparation failed." }

if (Test-Path -LiteralPath $Output) {
    Remove-Item -LiteralPath $Output -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $Output | Out-Null

Write-Host "Building native ORION Windows app..." -ForegroundColor Cyan

$args = @(
    "publish",
    $Project,
    "-c", $Configuration,
    "-r", "win-x64",
    "--self-contained", "true",
    "-p:PublishSingleFile=true",
    "-p:PublishTrimmed=false",
    "-p:PublishReadyToRun=false",
    "-o", $Output
)

& $dotnetPath @args
if ($LASTEXITCODE -ne 0) {
    throw "Native ORION Windows UI build failed."
}

$exe = Join-Path $Output "ORION.exe"
if (!(Test-Path -LiteralPath $exe -PathType Leaf)) {
    throw "Build completed without expected executable: $exe"
}

$buildCommit = (& git.exe -C $Repo rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($buildCommit)) {
    throw "Could not resolve ORION build commit."
}

@{
    schema = "orion-v3.build-info.v1"
    commit = $buildCommit
    built_at = [DateTimeOffset]::Now.ToString("O")
    configuration = $Configuration
    shell = "native-wpf-webview2"
} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Output "build-info.json") -Encoding UTF8

Write-Host "ORION_WINDOWS_UI> PASS" -ForegroundColor Green
Write-Host ("BUILD_COMMIT> " + $buildCommit) -ForegroundColor Green
Write-Host ("EXE> " + $exe)
