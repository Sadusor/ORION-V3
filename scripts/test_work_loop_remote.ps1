# ORION-V3 Work Loop: manual, owner-approved PC regression.
# Intended for existing engineering Remote's PowerShell Hand, NOT ORION runtime.
# No model calls, no real Work Hand, no privileged changes.
param(
    [string]$Python = "python"
)
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repo
try {
    $branch = (& git branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $branch -ne "spike/windows-isolation-preflight-20261008") {
        throw "Wrong ORION branch: $branch"
    }
    Write-Host "ORION_WORK_LOOP_TEST START branch=$branch"
    & $Python -m pytest -q tests/test_work_loop_coordinator.py tests/test_work_loop_model_proposal.py tests/test_work_loop_model_cycle_simulation.py
    $code = $LASTEXITCODE
    if ($code -ne 0) { throw "ORION_WORK_LOOP_TEST FAIL exit=$code" }
    Write-Host "ORION_WORK_LOOP_TEST PASS (offline simulation only; physical qualification NOT RUN)"
}
finally {
    Pop-Location
}
