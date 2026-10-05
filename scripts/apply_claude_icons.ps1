param()

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$IconRoot = Join-Path $Repo "ui\strata\icons"
$Renderer = Join-Path $IconRoot "make_icons.py"
$ToolRoot = Join-Path $env:LOCALAPPDATA "ORION-V3\icon-renderer"
$Venv = Join-Path $ToolRoot "venv"
$Py = Join-Path $Venv "Scripts\python.exe"

function Resolve-SystemPython {
    foreach ($name in @("python.exe", "py.exe")) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
    }
    throw "Python 3.11+ not found."
}

if (!(Test-Path -LiteralPath $Renderer -PathType Leaf)) {
    throw "Claude ORION icon renderer missing: $Renderer"
}

New-Item -ItemType Directory -Force -Path $ToolRoot | Out-Null

if (!(Test-Path -LiteralPath $Py -PathType Leaf)) {
    $systemPython = Resolve-SystemPython
    Write-Host "Creating local ORION icon renderer environment..." -ForegroundColor Cyan
    & $systemPython -m venv $Venv
    if ($LASTEXITCODE -ne 0) { throw "Could not create ORION icon renderer venv." }
}

Write-Host "Ensuring Pillow + NumPy for Claude icon renderer..." -ForegroundColor Cyan
$previousErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Py -m pip install --disable-pip-version-check --quiet pillow numpy 2>&1 | Out-Host
$pipExit = $LASTEXITCODE
$ErrorActionPreference = $previousErrorPreference
if ($pipExit -ne 0) {
    throw "Could not install icon renderer dependencies."
}

$previousErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Py -c "import PIL, numpy; print('ORION_ICON_DEPS> PASS')" 2>&1 | Out-Host
$verifyExit = $LASTEXITCODE
$ErrorActionPreference = $previousErrorPreference
if ($verifyExit -ne 0) {
    throw "ORION icon renderer dependency verification failed."
}

Write-Host "Rendering Claude ORION icon pack..." -ForegroundColor Cyan
$previousErrorPreference = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $Py $Renderer $IconRoot 2>&1 | Out-Host
$renderExit = $LASTEXITCODE
$ErrorActionPreference = $previousErrorPreference
if ($renderExit -ne 0) {
    throw "Claude ORION icon rendering failed."
}

$required = @(
    (Join-Path $IconRoot "orion-icon-1024.png"),
    (Join-Path $IconRoot "orion-icon-rounded-1024.png"),
    (Join-Path $IconRoot "orion-mark-transparent-1024.png"),
    (Join-Path $IconRoot "sizes\favicon.ico"),
    (Join-Path $IconRoot "sizes\apple-touch-icon.png"),
    (Join-Path $IconRoot "sizes\orion-icon-48.png"),
    (Join-Path $IconRoot "sizes\orion-icon-72.png"),
    (Join-Path $IconRoot "sizes\orion-icon-96.png"),
    (Join-Path $IconRoot "sizes\orion-icon-144.png"),
    (Join-Path $IconRoot "sizes\orion-icon-192.png"),
    (Join-Path $IconRoot "sizes\orion-icon-maskable-512.png")
)
foreach ($path in $required) {
    if (!(Test-Path -LiteralPath $path -PathType Leaf)) {
        throw "Required ORION icon missing after render: $path"
    }
}

# STRATA uses stable top-level names for browser metadata.
Copy-Item -LiteralPath (Join-Path $IconRoot "sizes\favicon.ico") -Destination (Join-Path $IconRoot "favicon.ico") -Force
Copy-Item -LiteralPath (Join-Path $IconRoot "sizes\apple-touch-icon.png") -Destination (Join-Path $IconRoot "apple-touch-icon.png") -Force

# Android launcher density map from Claude's generated pack.
$androidRes = Join-Path $Repo "android\app\src\main\res"
$map = @(
    @{ Dir = "mipmap-mdpi"; Size = 48 },
    @{ Dir = "mipmap-hdpi"; Size = 72 },
    @{ Dir = "mipmap-xhdpi"; Size = 96 },
    @{ Dir = "mipmap-xxhdpi"; Size = 144 },
    @{ Dir = "mipmap-xxxhdpi"; Size = 192 }
)

foreach ($item in $map) {
    $dest = Join-Path $androidRes $item.Dir
    New-Item -ItemType Directory -Force -Path $dest | Out-Null
    $src = Join-Path $IconRoot ("sizes\orion-icon-" + $item.Size + ".png")
    Copy-Item -LiteralPath $src -Destination (Join-Path $dest "ic_launcher.png") -Force
    Copy-Item -LiteralPath $src -Destination (Join-Path $dest "ic_launcher_round.png") -Force
}

Write-Host "ORION_ICON_PACK> PASS" -ForegroundColor Green
Write-Host "WEB_ICON> ui\strata\icons\favicon.ico"
Write-Host "ANDROID_ICON> mipmap 48/72/96/144/192"
Write-Host "MASTER_ICON> ui\strata\icons\orion-icon-1024.png"
Write-Host "MARK> ui\strata\icons\orion-mark-transparent-1024.png"
