$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'

Write-Host 'V3_RUN_ID> V3-RUN-047'
Write-Host 'MODE> one live Groq GPT-OSS 120B advisory round-trip through ORION'
Write-Host 'NETWORK> one bounded provider request; no tools; no Hands; no fallback'

& uv run --project $RepoRoot python (Join-Path $RepoRoot 'scripts\v3_authoring_preflight.py')
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

if ([string]::IsNullOrWhiteSpace($env:GROQ_API_KEY)) {
    Write-Host 'GROQ_CREDENTIAL> BLOCKED missing GROQ_API_KEY'
    Write-Host 'STATUS> FAIL'
    exit 1
}
Write-Host 'GROQ_CREDENTIAL> PRESENT'

& uv run --project $RepoRoot python (
    Join-Path $RepoRoot 'scripts\v36_live_cloud_roundtrip_gate.py'
)
if ($LASTEXITCODE -ne 0) { Write-Host 'STATUS> FAIL'; exit 1 }

Write-Host 'ORION_LIVE_CLOUD_ROUNDTRIP> PASS'
Write-Host 'STATUS> PASS'
exit 0
