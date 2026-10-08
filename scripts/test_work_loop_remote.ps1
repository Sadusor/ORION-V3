# ORION Work Loop bounded PC test, no real executor
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $root
$prior = $env:PYTHONPATH
try {
    if ((& git branch --show-current).Trim() -ne "spike/windows-isolation-preflight-20261008") { throw "Unexpected branch" }
    $env:PYTHONPATH = Join-Path $root "src"
    & python -m pytest -q tests/test_work_loop_coordinator.py tests/test_work_loop_model_proposal.py tests/test_work_loop_model_cycle_simulation.py tests/test_work_loop_local_proposer.py
    if ($LASTEXITCODE -ne 0) { throw "ORION_WORK_LOOP_TEST FAIL" }
    Write-Host "ORION_WORK_LOOP_TEST PASS - mock Qwen only; real Qwen and Windows isolation NOT RUN"
} finally {
    $env:PYTHONPATH = $prior
    Pop-Location
}
