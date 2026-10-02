$ErrorActionPreference = 'Stop'

$Repo = 'https://github.com/Sadusor/OpenJarvis.git'
$ExpectedSha = '309a4f1044ccfb2032264832a31fef2f1d314586'
$Root = Split-Path -Parent $PSScriptRoot
$Destination = Join-Path $Root 'external\OpenJarvis'

if (Test-Path $Destination) {
    throw "Refusing to overwrite existing donor working tree: $Destination"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
git clone --no-checkout $Repo $Destination
if ($LASTEXITCODE -ne 0) { throw 'OpenJarvis clone failed.' }

git -C $Destination checkout --detach $ExpectedSha
if ($LASTEXITCODE -ne 0) { throw 'Pinned OpenJarvis checkout failed.' }

$ActualSha = (git -C $Destination rev-parse HEAD).Trim()
if ($ActualSha -ne $ExpectedSha) {
    throw "OpenJarvis SHA mismatch: $ActualSha != $ExpectedSha"
}

Write-Host "Pinned OpenJarvis donor ready at $Destination"
Write-Host "SHA: $ActualSha"
Write-Host 'No installer or donor code has been executed by this script.'