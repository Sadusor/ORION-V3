$ErrorActionPreference = 'Stop'
Write-Host 'ORION_GITEA_READONLY_V1_GITCHECK> START'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Push-Location $repo
try {
  $env:PYTHONPATH = Join-Path $repo 'src'
  & py -3.11 -m unittest discover -s tests -p test_gitea_readonly_v1.py -v
  if ($LASTEXITCODE -ne 0) { throw 'Gitea V1 isolated contract tests failed' }
  Write-Host 'ORION_GITEA_READONLY_V1_GITCHECK> PASS'
  git rev-parse --short HEAD
} finally {
  Pop-Location
}
