$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
Write-Host 'V3_RUN_ID> V3-RUN-014'
Write-Host 'V3_REGRESSION> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }
Write-Host 'V3_REGRESSION> PASS'
$Donor = Join-Path $RepoRoot 'external\OpenJarvis'
& uv run --project $Donor python (Join-Path $RepoRoot 'scripts\v32_qwen_structured_canonicalization_benchmark.py')
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }
Write-Host 'STATUS> PASS'
exit 0
