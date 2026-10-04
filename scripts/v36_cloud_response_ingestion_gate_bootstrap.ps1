$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'

Write-Host 'V3_RUN_ID> V3-RUN-046'
Write-Host 'MODE> cloud specialist response -> immutable advisory REVIEW; zero model/network/Hand'

& uv run --project $RepoRoot python (Join-Path $RepoRoot 'scripts\v3_authoring_preflight.py')
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v36_cloud_response_ingestion_gate.py'
)
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

Write-Host 'ORION_CLOUD_RESPONSE_INGESTION> PASS'
Write-Host 'STATUS> PASS'
exit 0
