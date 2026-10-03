$ErrorActionPreference = 'Stop'

function Fail([string]$Code, [string]$Detail) {
    Write-Host ($Code + '> FAIL')
    Write-Host ('DETAIL> ' + $Detail)
    Write-Host 'STATUS> FAIL'
    exit 1
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Sdk = Join-Path $RepoRoot 'external\OpenHands-software-agent-sdk'
$ExpectedSdkSha = '856d99d48e4b11c70c5f1cab21e7830570dbc324'

Write-Host 'V3_RUN_ID> V3-RUN-009'
Write-Host 'ORION_OPENHANDS_ADAPTER_BOOTSTRAP> START'

Write-Host 'V3_REGRESSION> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) {
    Fail 'V3_REGRESSION' 'ORION-V3 regression suite failed.'
}
Write-Host 'V3_REGRESSION> PASS'

& powershell -NoProfile -ExecutionPolicy Bypass -File (
    Join-Path $RepoRoot 'scripts\fetch_openhands_sdk.ps1'
)
if ($LASTEXITCODE -ne 0) {
    Fail 'OPENHANDS_SDK_FETCH' 'Pinned OpenHands SDK fetch failed.'
}

$SdkSha = (& git -C $Sdk rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $SdkSha -ne $ExpectedSdkSha) {
    Fail 'OPENHANDS_SDK_PIN' ('Unexpected SDK SHA: ' + $SdkSha)
}
Write-Host 'OPENHANDS_SDK_PIN> PASS'

& uv sync --project $Sdk --package openhands-tools --locked
if ($LASTEXITCODE -ne 0) {
    Fail 'OPENHANDS_TOOLS_ENV' 'Pinned OpenHands tools environment failed.'
}
Write-Host 'OPENHANDS_TOOLS_ENV> PASS'

Write-Host 'ORION_OPENHANDS_ADAPTER_PHYSICAL> RUN'
& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v31_openhands_adapter_physical.py'
)
if ($LASTEXITCODE -ne 0) {
    Fail 'ORION_OPENHANDS_ADAPTER_PHYSICAL' 'Governed OpenHands adapter probe failed.'
}

Write-Host 'ORION_OPENHANDS_ADAPTER_PHYSICAL> PASS'
Write-Host 'STATUS> PASS'
exit 0
