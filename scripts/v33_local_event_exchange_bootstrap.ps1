$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

Write-Host 'V3_RUN_ID> V3-RUN-016'
Write-Host 'V3_REGRESSION> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) {
    Write-Host 'V3_REGRESSION> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'V3_REGRESSION> PASS'

Write-Host 'LOCAL_EVENT_EXCHANGE_PROBE> RUN'
& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v33_local_event_exchange_probe.py'
)
if ($LASTEXITCODE -ne 0) {
    Write-Host 'LOCAL_EVENT_EXCHANGE_PROBE> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'LOCAL_EVENT_EXCHANGE_PROBE> PASS'
Write-Host 'STATUS> PASS'
exit 0
