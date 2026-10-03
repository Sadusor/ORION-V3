$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'

Write-Host 'V3_RUN_ID> V3-RUN-020'

Write-Host 'AUTHORING_PREFLIGHT> RUN'
& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v3_authoring_preflight.py'
)
if ($LASTEXITCODE -ne 0) {
    Write-Host 'AUTHORING_PREFLIGHT> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'AUTHORING_PREFLIGHT> PASS'

Write-Host 'V3_REGRESSION> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) {
    Write-Host 'V3_REGRESSION> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'V3_REGRESSION> PASS'

Write-Host 'WORKPACKAGE_EXECUTION_ENVELOPE_PROBE> RUN'
& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v34_workpackage_execution_envelope_probe.py'
)
if ($LASTEXITCODE -ne 0) {
    Write-Host 'WORKPACKAGE_EXECUTION_ENVELOPE_PROBE> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}

Write-Host 'WORKPACKAGE_EXECUTION_ENVELOPE_PROBE> PASS'
Write-Host 'STATUS> PASS'
exit 0
