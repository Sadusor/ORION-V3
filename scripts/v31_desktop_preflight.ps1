$ErrorActionPreference = 'Stop'

function Fail([string]$Code, [string]$Detail) {
    Write-Host ($Code + '> FAIL')
    Write-Host ('DETAIL> ' + $Detail)
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'V3_RUN_ID> V3-RUN-003'
Write-Host 'DESKTOP_PREFLIGHT> START'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Donor = Join-Path $RepoRoot 'external\OpenJarvis'
$Frontend = Join-Path $Donor 'frontend'

if (-not (Test-Path $Donor)) {
    Fail 'OPENJARVIS_PIN' 'Pinned OpenJarvis checkout is missing.'
}
$DonorSha = (& git -C $Donor rev-parse HEAD).Trim()
if ($DonorSha -ne '309a4f1044ccfb2032264832a31fef2f1d314586') {
    Fail 'OPENJARVIS_PIN' ('Unexpected donor SHA: ' + $DonorSha)
}
Write-Host 'OPENJARVIS_PIN> PASS'

if (-not (Test-Path (Join-Path $Frontend 'package.json'))) {
    Fail 'DESKTOP_FRONTEND' 'Pinned donor frontend/package.json is missing.'
}
Write-Host 'DESKTOP_FRONTEND> FOUND'

# Determine whether stock OpenJarvis Desktop would auto-boot its own backend.
$InferencePath = Join-Path $env:USERPROFILE '.openjarvis\inference.json'
if (Test-Path $InferencePath) {
    try {
        $cfg = Get-Content -Raw -LiteralPath $InferencePath | ConvertFrom-Json
    } catch {
        Fail 'DESKTOP_INFERENCE_STATE' 'Existing inference.json is invalid JSON.'
    }
    $confirmed = $false
    if ($null -ne $cfg.PSObject.Properties['confirmed']) {
        $confirmed = [bool]$cfg.confirmed
    } else {
        # Pinned donor treats legacy configs without this field as confirmed.
        $confirmed = $true
    }
    $kind = if ($null -ne $cfg.PSObject.Properties['kind']) { [string]$cfg.kind } else { 'unknown' }
    Write-Host ('DESKTOP_INFERENCE_KIND> ' + $kind)
    Write-Host ('DESKTOP_INFERENCE_CONFIRMED> ' + $confirmed)
    if ($confirmed) {
        Write-Host 'DESKTOP_INERT_LAUNCH> BLOCKED'
        Write-Host 'DETAIL> Stock desktop would auto-start its own Jarvis backend from the confirmed source. Do not launch unmodified.'
    } else {
        Write-Host 'DESKTOP_INERT_LAUNCH> SAFE'
    }
} else {
    Write-Host 'DESKTOP_INFERENCE_STATE> ABSENT'
    Write-Host 'DESKTOP_INERT_LAUNCH> SAFE'
}

function Resolve-CommandPath([string]$Name) {
    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $cmd) { return $null }
    return $cmd.Source
}

$nodePath = Resolve-CommandPath 'node'
if (-not $nodePath) { Fail 'NODE' 'Node.js is not installed or not on PATH.' }
$nodeRaw = (& node --version).Trim()
if ($LASTEXITCODE -ne 0 -or $nodeRaw -notmatch '^v(\d+)\.(\d+)\.(\d+)$') {
    Fail 'NODE' ('Could not parse Node version: ' + $nodeRaw)
}
$nodeMajor = [int]$Matches[1]
$nodeMinor = [int]$Matches[2]
if ($nodeMajor -lt 22 -or ($nodeMajor -eq 22 -and $nodeMinor -lt 22)) {
    Fail 'NODE' ('Pinned desktop requires Node >=22.22; found ' + $nodeRaw)
}
Write-Host ('NODE> PASS ' + $nodeRaw)

$npmPath = Resolve-CommandPath 'npm'
if (-not $npmPath) { Fail 'NPM' 'npm is not installed or not on PATH.' }
$npmRaw = (& npm --version).Trim()
if ($LASTEXITCODE -ne 0 -or $npmRaw -notmatch '^(\d+)\.(\d+)\.(\d+)') {
    Fail 'NPM' ('Could not parse npm version: ' + $npmRaw)
}
$npmMajor = [int]$Matches[1]
$npmMinor = [int]$Matches[2]
if ($npmMajor -ne 11 -or $npmMinor -lt 19) {
    Fail 'NPM' ('Pinned desktop requires npm >=11.19 <12; found ' + $npmRaw)
}
Write-Host ('NPM> PASS ' + $npmRaw)

$rustcPath = Resolve-CommandPath 'rustc'
if (-not $rustcPath) { Fail 'RUST' 'rustc is not installed or not on PATH.' }
$rustRaw = (& rustc --version).Trim()
if ($LASTEXITCODE -ne 0) { Fail 'RUST' 'rustc --version failed.' }
Write-Host ('RUST> PASS ' + $rustRaw)

$cargoPath = Resolve-CommandPath 'cargo'
if (-not $cargoPath) { Fail 'CARGO' 'cargo is not installed or not on PATH.' }
$cargoRaw = (& cargo --version).Trim()
if ($LASTEXITCODE -ne 0) { Fail 'CARGO' 'cargo --version failed.' }
Write-Host ('CARGO> PASS ' + $cargoRaw)

Write-Host 'DESKTOP_AUTOSTART_BACKEND> NOT_STARTED'
Write-Host 'OLLAMA> NOT_STARTED'
Write-Host 'MODEL_PULL> NOT_STARTED'
Write-Host 'DESKTOP_PREFLIGHT> PASS'
Write-Host 'STATUS> PASS'
exit 0
