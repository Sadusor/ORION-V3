# Disposable vault interruption / STOP qualification — no canonical ORION writes
# This tests a *fixture state machine*, not the existing ORION commit coordinator.
$ErrorActionPreference='Stop'
$root=Join-Path $env:TEMP ('orion-vault-crash-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
function Assert($ok,$label){if(-not $ok){throw ('FAIL '+$label)};Write-Host ($label+'> PASS')}
function State($dir,$value){Set-Content -LiteralPath (Join-Path $dir 'state.txt') -Value $value -NoNewline}
function ReadState($dir){Get-Content -LiteralPath (Join-Path $dir 'state.txt') -Raw}
try{
 Write-Host 'VAULT_CRASH_FIXTURE> START'
 Write-Host 'REAL_ORION_EXECUTION> DISABLED'
 $canonical=Join-Path $root 'canonical.bin'
 [IO.File]::WriteAllBytes($canonical,[byte[]](1,2,3,4,5,6,7,8))
 $baseline=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([IO.File]::ReadAllBytes($canonical)))
 foreach($scenario in @('STOP_BEFORE_COMMIT','CRASH_AFTER_ARTIFACT','RESTART_NO_AUTORETRY','REPEATED_STOP')){
  $dir=Join-Path $root $scenario;New-Item -ItemType Directory -Path $dir|Out-Null
  State $dir 'PENDING'
  [IO.File]::WriteAllBytes((Join-Path $dir 'artifact.bin'),[byte[]](9,8,7,6))
  switch($scenario){
   'STOP_BEFORE_COMMIT' {State $dir 'STOPPED'}
   'CRASH_AFTER_ARTIFACT' {State $dir 'INTERRUPTED'}
   'RESTART_NO_AUTORETRY' {State $dir 'INTERRUPTED'}
   'REPEATED_STOP' {State $dir 'STOPPED';State $dir 'STOPPED'}
  }
  Assert ((ReadState $dir) -ne 'PASS') ($scenario+'_NO_FALSE_PASS')
  Assert ((ReadState $dir) -in @('STOPPED','INTERRUPTED')) ($scenario+'_TERMINAL')
  $now=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([IO.File]::ReadAllBytes($canonical)))
  Assert ($now -eq $baseline) ($scenario+'_CANONICAL_UNCHANGED')
 }
 Write-Host 'FIXTURE_STOP_CRASH_SUITE> PASS'
 Write-Host 'ORION_REAL_VAULT_COMMIT_GUARD> NOT_TESTED'
 Write-Host 'ORION_STOP_SERVICE_INTEGRATION> NOT_TESTED'
 Write-Host 'NETWORK_ISOLATION> UNVERIFIED'
 Write-Host 'COMBINED_QUALIFICATION> INCOMPLETE'
}finally{
 Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop
 Write-Host 'FIXTURE_CLEANUP> PASS'
}
