$ErrorActionPreference = 'Stop'

function Fail([string]$Code, [string]$Detail) {
    Write-Host ($Code + '> FAIL')
    Write-Host ('DETAIL> ' + $Detail)
    Write-Host 'STATUS> FAIL'
    exit 1
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$Donor = Join-Path $RepoRoot 'external\OpenJarvis'

Write-Host 'ORION_V3_V31_BOOTSTRAP> START'
Write-Host 'V3_RUN_ID> V3-RUN-001'

$Origin = (& git -C $RepoRoot remote get-url origin).Trim()
if ($LASTEXITCODE -ne 0 -or $Origin -notmatch 'Sadusor/ORION-V3') {
    Fail 'V3_ORIGIN' ('Unexpected origin: ' + $Origin)
}
Write-Host 'V3_ORIGIN> PASS'

$Branch = (& git -C $RepoRoot branch --show-current).Trim()
if ($Branch -ne 'agent/v3.1-filesystem-hand') {
    Fail 'V3_BRANCH' ('Unexpected branch: ' + $Branch)
}
Write-Host 'V3_BRANCH> PASS'

$Dirty = @(& git -C $RepoRoot status --porcelain=v1 --untracked-files=no)
if ($LASTEXITCODE -ne 0 -or $Dirty.Count -gt 0) {
    Fail 'V3_CLEAN' ('Tracked changes present: ' + ($Dirty -join ' | '))
}
Write-Host 'V3_CLEAN> PASS'

if (-not (Test-Path $Donor)) {
    Fail 'OPENJARVIS_PIN' 'Pinned donor checkout is missing.'
}
$DonorSha = (& git -C $Donor rev-parse HEAD).Trim()
if ($DonorSha -ne '309a4f1044ccfb2032264832a31fef2f1d314586') {
    Fail 'OPENJARVIS_PIN' ('Unexpected donor SHA: ' + $DonorSha)
}
Write-Host 'OPENJARVIS_PIN> PASS'

Write-Host 'V31_TESTS> RUN'
& uv run --project $RepoRoot --extra dev pytest -q
if ($LASTEXITCODE -ne 0) {
    Fail 'V31_TESTS' 'ORION-V3 test suite failed.'
}
Write-Host 'V31_TESTS> PASS'

Write-Host 'V31_REAL_FILESYSTEM_SEARCH> RUN'
& uv run --project $Donor python (Join-Path $RepoRoot 'scripts\v31_filesystem_search_physical.py')
if ($LASTEXITCODE -ne 0) {
    Fail 'V31_REAL_FILESYSTEM_SEARCH' 'Physical filesystem.search integration failed.'
}
Write-Host 'V31_REAL_FILESYSTEM_SEARCH> PASS'

Write-Host 'STATUS> PASS'
exit 0
