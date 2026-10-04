$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$OpenJarvis = Join-Path $RepoRoot 'external\OpenJarvis'
$ExpectedOpenJarvis = '309a4f1044ccfb2032264832a31fef2f1d314586'

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'

Write-Host 'V3_RUN_ID> V3-RUN-053'
Write-Host 'MODE> waiting_owner -> exact owner scope amendment -> bounded 9B resume -> real Hand -> cumulative completion'

& uv run --project $RepoRoot python (Join-Path $RepoRoot 'scripts\v3_authoring_preflight.py')
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

if (-not (Test-Path $OpenJarvis)) {
    & (Join-Path $RepoRoot 'scripts\fetch_openjarvis.ps1')
    if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }
}
$ActualOpenJarvis = (& git -C $OpenJarvis rev-parse HEAD).Trim()
if ($ActualOpenJarvis -ne $ExpectedOpenJarvis) {
    Write-Host "OPENJARVIS_PIN> FAIL expected=$ExpectedOpenJarvis actual=$ActualOpenJarvis"
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'OPENJARVIS_PIN> PASS'

& uv run --project $OpenJarvis python -c "import openjarvis_rust; print('OPENJARVIS_RUST_IMPORT> PASS')"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'OPENJARVIS_RUST_IMPORT> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}

& uv run --project $OpenJarvis python (
    Join-Path $RepoRoot 'scripts\v36_owner_scope_resume_gate.py'
)
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

Write-Host 'ORION_OWNER_RESUME> PASS'
Write-Host 'STATUS> PASS'
exit 0
