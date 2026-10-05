param()

$ErrorActionPreference = "Stop"

$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$IconPng = Join-Path $Repo "ui\strata\icons\orion-icon-1024.png"
$AssetDir = Join-Path $Repo "desktop\ORION.UI\Assets"
$IconIco = Join-Path $AssetDir "orion.ico"
$VenvPython = Join-Path $env:LOCALAPPDATA "ORION-V3\icon-renderer\venv\Scripts\python.exe"

if (!(Test-Path -LiteralPath $IconPng -PathType Leaf)) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo "scripts\apply_claude_icons.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Could not generate ORION source icon assets." }
}

if (!(Test-Path -LiteralPath $VenvPython -PathType Leaf)) {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $Repo "scripts\apply_claude_icons.ps1")
    if ($LASTEXITCODE -ne 0) { throw "Could not prepare ORION icon renderer." }
}

New-Item -ItemType Directory -Force -Path $AssetDir | Out-Null

$code = @'
from PIL import Image
import sys
src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGBA")
im.save(dst, format="ICO", sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])
print("ORION_WINDOWS_ICON> PASS")
'@

$old = $ErrorActionPreference
$ErrorActionPreference = "Continue"
$code | & $VenvPython - $IconPng $IconIco 2>&1 | Out-Host
$exit = $LASTEXITCODE
$ErrorActionPreference = $old

if ($exit -ne 0 -or !(Test-Path -LiteralPath $IconIco -PathType Leaf)) {
    throw "ORION Windows icon generation failed."
}

Write-Host ("ICON> " + $IconIco) -ForegroundColor Green
