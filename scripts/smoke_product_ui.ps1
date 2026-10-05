param(
    [int]$Port = 8890
)

$ErrorActionPreference = "Stop"
$Repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

$health = Invoke-RestMethod -Uri ("http://127.0.0.1:" + $Port + "/api/health") -TimeoutSec 3
if (!$health.ok) { throw "ORION_PC_HEALTH> FAIL" }
Write-Host ("ORION_PC_HEALTH> PASS | " + $health.running_commit) -ForegroundColor Green

$status = Invoke-RestMethod -Uri ("http://127.0.0.1:" + $Port + "/api/status") -TimeoutSec 3
if ($status.schema -ne "orion-v3.product-status/1") {
    throw "ORION_PC_LOCAL_AUTH> FAIL | localhost status contract missing"
}
Write-Host "ORION_PC_LOCAL_AUTH> PASS" -ForegroundColor Green

$head = (& git.exe -C $Repo rev-parse HEAD).Trim()
if ([string]$health.running_commit -ne $head) {
    throw ("ORION_PC_BUILD_MATCH> FAIL | runtime " + $health.running_commit + " != repo " + $head)
}
Write-Host ("ORION_PC_BUILD_MATCH> PASS | " + $head) -ForegroundColor Green

$html = (Invoke-WebRequest -UseBasicParsing -Uri ("http://127.0.0.1:" + $Port + "/v3/") -TimeoutSec 3).Content
if ($html -notmatch "Ask ORION") {
    throw "ORION_PC_STRATA> FAIL | Ask ORION composer missing"
}
if ($html -notmatch "ORION_PC_PAIR_CODE") {
    throw "ORION_PC_PAIRING_SURFACE> FAIL | local pairing code was not injected"
}
Write-Host "ORION_PC_STRATA> PASS" -ForegroundColor Green
Write-Host "ORION_PC_PAIRING_SURFACE> PASS" -ForegroundColor Green

Write-Host "ORION_PC_SMOKE> PASS" -ForegroundColor Green
