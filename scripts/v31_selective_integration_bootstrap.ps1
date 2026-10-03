$ErrorActionPreference = 'Stop'

function Fail([string]$Code, [string]$Detail) {
    Write-Host ($Code + '> FAIL')
    Write-Host ('DETAIL> ' + $Detail)
    Write-Host 'STATUS> FAIL'
    exit 1
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Donor = Join-Path $RepoRoot 'external\OpenJarvis'
$ExpectedDonorSha = '309a4f1044ccfb2032264832a31fef2f1d314586'

Write-Host 'V3_RUN_ID> V3-RUN-007'
Write-Host 'SELECTIVE_OPENJARVIS_BOOTSTRAP> START'

if (-not (Test-Path $Donor)) {
    Fail 'OPENJARVIS_PIN' 'Pinned OpenJarvis donor checkout is missing.'
}
$DonorSha = (& git -C $Donor rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $DonorSha -ne $ExpectedDonorSha) {
    Fail 'OPENJARVIS_PIN' ('Unexpected donor SHA: ' + $DonorSha)
}
Write-Host 'OPENJARVIS_PIN> PASS'

Write-Host 'V3_REGRESSION> RUN'
& uv run --project $RepoRoot --extra dev pytest (Join-Path $RepoRoot 'tests') -q
if ($LASTEXITCODE -ne 0) {
    Fail 'V3_REGRESSION' 'ORION-V3 regression suite failed.'
}
Write-Host 'V3_REGRESSION> PASS'

function Test-Ollama {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2
        return $response.StatusCode -eq 200
    } catch {
        return $false
    }
}

$StartedOllama = $false
if (-not (Test-Ollama)) {
    $Ollama = Get-Command 'ollama.exe' -ErrorAction SilentlyContinue
    if ($null -eq $Ollama) {
        $Ollama = Get-Command 'ollama' -ErrorAction SilentlyContinue
    }
    if ($null -eq $Ollama) {
        Fail 'OLLAMA' 'Ollama is offline and ollama executable was not found on PATH.'
    }

    Write-Host 'OLLAMA> STARTING_FOR_BOUNDED_ROUTER_TEST'
    Start-Process -FilePath $Ollama.Source -ArgumentList @('serve') -WindowStyle Hidden | Out-Null
    $StartedOllama = $true

    $deadline = (Get-Date).AddSeconds(25)
    while ((Get-Date) -lt $deadline -and -not (Test-Ollama)) {
        Start-Sleep -Milliseconds 500
    }
}

if (-not (Test-Ollama)) {
    Fail 'OLLAMA' 'Ollama did not become reachable.'
}
Write-Host ('OLLAMA> PASS' + $(if ($StartedOllama) { ' AUTO_STARTED' } else { ' ALREADY_RUNNING' }))

Write-Host 'SELECTIVE_OPENJARVIS_PROBE> RUN'
& uv run --project $Donor python (
    Join-Path $RepoRoot 'scripts\v31_openjarvis_selective_integration.py'
)
if ($LASTEXITCODE -ne 0) {
    Fail 'SELECTIVE_OPENJARVIS_PROBE' 'Workflow/router qualification probe failed.'
}

Write-Host 'SELECTIVE_OPENJARVIS_PROBE> PASS'
Write-Host 'STATUS> PASS'
exit 0
