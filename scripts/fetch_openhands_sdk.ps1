$ErrorActionPreference = 'Stop'

$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Repo = 'https://github.com/Sadusor/software-agent-sdk.git'
$Destination = Join-Path $Root 'external\OpenHands-software-agent-sdk'
$ExpectedSha = '856d99d48e4b11c70c5f1cab21e7830570dbc324'

if (-not (Test-Path $Destination)) {
    Write-Host 'OPENHANDS_SDK_FETCH> CLONE'
    & git clone --no-checkout $Repo $Destination
    if ($LASTEXITCODE -ne 0) { throw 'OpenHands software-agent-sdk clone failed.' }
}

& git -C $Destination fetch origin $ExpectedSha --depth 1
if ($LASTEXITCODE -ne 0) { throw 'OpenHands software-agent-sdk fetch failed.' }

& git -C $Destination checkout --detach $ExpectedSha
if ($LASTEXITCODE -ne 0) { throw 'OpenHands software-agent-sdk checkout failed.' }

$ActualSha = (& git -C $Destination rev-parse HEAD).Trim()
if ($ActualSha -ne $ExpectedSha) {
    throw "OpenHands SDK SHA mismatch: $ActualSha != $ExpectedSha"
}

$Dirty = @(& git -C $Destination status --porcelain=v1 --untracked-files=no)
if ($Dirty.Count -gt 0) {
    throw ('OpenHands SDK tracked checkout is dirty: ' + ($Dirty -join ' | '))
}

Write-Host ('OPENHANDS_SDK_PIN> PASS ' + $ActualSha)
