$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$OpenJarvis = Join-Path $RepoRoot 'external\OpenJarvis'
$OpenHands = Join-Path $RepoRoot 'external\OpenHands-software-agent-sdk'
$ExpectedOpenJarvis = '309a4f1044ccfb2032264832a31fef2f1d314586'

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:ORION_BENCHMARK_MODEL = 'ollama_chat/qwen3.6:35b-a3b'

Write-Host 'V3_RUN_ID> V3-RUN-036R'

& uv run --project $RepoRoot python (Join-Path $RepoRoot 'scripts\v3_authoring_preflight.py')
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

& (Join-Path $RepoRoot 'scripts\fetch_openhands_sdk.ps1')
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

if (-not (Test-Path $OpenJarvis)) {
    & (Join-Path $RepoRoot 'scripts\fetch_openjarvis.ps1')
    if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }
}
$ActualOpenJarvis = (& git -C $OpenJarvis rev-parse HEAD).Trim()
if ($ActualOpenJarvis -ne $ExpectedOpenJarvis) { Write-Host 'STATUS> FAIL'; exit 1 }

& uv run --project $OpenHands --package openhands-tools python (
    Join-Path $RepoRoot 'scripts\v35_operator_mixed_tool_smoke_r2.py'
)
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

Write-Host 'ORION_OPERATOR_MIXED_TOOL_SMOKE_R2> PASS'
Write-Host 'STATUS> PASS'
exit 0
