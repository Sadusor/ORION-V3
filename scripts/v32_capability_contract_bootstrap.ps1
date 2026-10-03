$ErrorActionPreference = 'Stop'

function Fail([string]$Code, [string]$Detail) {
    Write-Host ($Code + '> FAIL')
    Write-Host ('DETAIL> ' + $Detail)
    Write-Host 'STATUS> FAIL'
    exit 1
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

Write-Host 'V3_RUN_ID> V3-RUN-010'
Write-Host 'SEMANTIC_CAPABILITY_BOOTSTRAP> START'

Write-Host 'V3_REGRESSION> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) {
    Fail 'V3_REGRESSION' 'ORION-V3 regression suite failed.'
}
Write-Host 'V3_REGRESSION> PASS'

Write-Host 'SEMANTIC_CAPABILITY_PROBE> RUN'
& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v32_capability_contract_probe.py'
)
if ($LASTEXITCODE -ne 0) {
    Fail 'SEMANTIC_CAPABILITY_PROBE' 'Semantic capability contract probe failed.'
}

Write-Host 'SEMANTIC_CAPABILITY_PROBE> PASS'
Write-Host 'V3_RUN_009> INTENTIONALLY_NOT_EXECUTED'
Write-Host 'STATUS> PASS'
exit 0
