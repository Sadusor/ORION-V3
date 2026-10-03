$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

Write-Host 'V3_RUN_ID> V3-RUN-019'
Write-Host 'V3_REGRESSION> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) {
    Write-Host 'V3_REGRESSION> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'V3_REGRESSION> PASS'

Write-Host 'ATTEMPT_OWNERSHIP_PROBE> RUN'
& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v34_attempt_ownership_probe.py'
)
if ($LASTEXITCODE -ne 0) {
    Write-Host 'ATTEMPT_OWNERSHIP_PROBE> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'ATTEMPT_OWNERSHIP_PROBE> PASS'
Write-Host 'STATUS> PASS'
exit 0
