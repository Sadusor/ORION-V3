$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$OpenJarvis = Join-Path $RepoRoot 'external\OpenJarvis'
$ExpectedOpenJarvis = '309a4f1044ccfb2032264832a31fef2f1d314586'

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'

Write-Host 'V3_RUN_ID> V3-RUN-049R'
Write-Host 'MODE> real 9B proposal -> ORION lease -> proven OpenJarvis read-only Hand -> evidence -> verifier'

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

if (-not (Get-Command cargo -ErrorAction SilentlyContinue)) {
    Write-Host 'OPENJARVIS_RUST_PREREQ> FAIL cargo missing'
    Write-Host 'STATUS> FAIL'
    exit 1
}

$env:CARGO_NET_RETRY = '5'
$SyncPassed = $false
for ($Attempt = 1; $Attempt -le 3; $Attempt++) {
    Write-Host ('OPENJARVIS_ENV> SYNC ATTEMPT ' + $Attempt + '/3')
    & uv sync --project $OpenJarvis --group desktop-native
    if ($LASTEXITCODE -eq 0) {
        $SyncPassed = $true
        break
    }
    if ($Attempt -lt 3) {
        Write-Host 'OPENJARVIS_ENV> transient native build/download failure; retrying'
        Start-Sleep -Seconds 5
    }
}
if (-not $SyncPassed) {
    Write-Host 'OPENJARVIS_ENV> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'OPENJARVIS_ENV> PASS'

& uv run --project $OpenJarvis python -c "import openjarvis_rust; print('OPENJARVIS_RUST_IMPORT> PASS')"
if ($LASTEXITCODE -ne 0) {
    Write-Host 'OPENJARVIS_RUST_IMPORT> FAIL'
    Write-Host 'STATUS> FAIL'
    exit 1
}

& uv run --project $OpenJarvis python (
    Join-Path $RepoRoot 'scripts\v36_routine_hand_execution_gate.py'
)
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

Write-Host 'ORION_ROUTINE_HAND_EXECUTION> PASS'
Write-Host 'STATUS> PASS'
exit 0
