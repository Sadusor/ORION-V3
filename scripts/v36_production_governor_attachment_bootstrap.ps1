$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'

Write-Host 'V3_RUN_ID> V3-RUN-045'
Write-Host 'MODEL> qwen35-9b-orion:latest'
Write-Host 'THINKING> ON'
Write-Host 'NUM_CTX> 4096'
Write-Host 'MODE> production governor -> ORION control plane; no direct Hand/provider execution'

& uv run --project $RepoRoot python (Join-Path $RepoRoot 'scripts\v3_authoring_preflight.py')
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v36_production_governor_attachment.py'
)
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

Write-Host 'ORION_PRODUCTION_GOVERNOR_ATTACHMENT> PASS'
Write-Host 'STATUS> PASS'
exit 0
