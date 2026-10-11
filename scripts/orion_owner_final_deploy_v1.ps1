param([Parameter(Mandatory=$true)][string]$QualifiedCheckout,[Parameter(Mandatory=$true)][string]$ExpectedCommit)
$ErrorActionPreference='Stop'
$state=Join-Path $env:LOCALAPPDATA 'ORION-V3'
$report=Join-Path $state 'final-owner-deployment.json'
$steps=[ordered]@{pc_backup='NOT_RUN';pc_update='NOT_RUN';android_update='NOT_RUN';orion2_removal='NOT_RUN';archive_network='NOT_ACTIVATED';result='IN_PROGRESS'}
function Persist {
  $steps | ConvertTo-Json | Set-Content -LiteralPath $report -Encoding UTF8
}
New-Item -ItemType Directory -Force -Path $state | Out-Null
Persist
try {
  $qualified=(& git -C $QualifiedCheckout rev-parse HEAD).Trim()
  if($LASTEXITCODE -ne 0 -or $qualified -ne $ExpectedCommit){throw 'Qualified source SHA mismatch'}
  $source=Join-Path $state 'chat_history.sqlite3'
  if(!(Test-Path -LiteralPath $source -PathType Leaf)){throw 'Production PC chat SQLite not found'}
  $backupDir=Join-Path $state 'history-archive-backups'
  & python (Join-Path $QualifiedCheckout 'tests/history_archive_backup_rehearsal_v1.py') --source $source --destination-root $backupDir
  if($LASTEXITCODE -ne 0){throw 'PC SQLite online backup and restore rehearsal failed'}
  $steps.pc_backup='PASS';Persist
  Write-Host 'PC_CONVERSATION_BACKUP> PASS'
  $ui=@(Get-CimInstance Win32_Process -Filter "Name='ORION.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.ExecutablePath -match '[\\/]dist[\\/]windows[\\/]ORION\.exe$' })
  if($ui.Count -ne 1){throw 'Expected exactly one running production ORION.exe; refusing guessed PC update'}
  $liveExe=$ui[0].ExecutablePath
  $prod=Split-Path (Split-Path (Split-Path $liveExe -Parent) -Parent) -Parent
  if(!(Test-Path -LiteralPath (Join-Path $prod '.git'))){throw 'Production ORION executable does not belong to a Git checkout'}
  if((Resolve-Path $prod).Path -ieq (Resolve-Path $QualifiedCheckout).Path){throw 'Qualification and production trees overlap'}
  $dirty=@(& git -C $prod status --porcelain)
  if($LASTEXITCODE -ne 0 -or $dirty.Count){throw 'Production source dirty; stopping to preserve uncommitted files'}
  $previous=(& git -C $prod rev-parse HEAD).Trim()
  & git -C $prod fetch origin main --quiet
  if($LASTEXITCODE -ne 0){throw 'Production Git fetch failed'}
  $target=(& git -C $prod rev-parse origin/main).Trim()
  if($target -ne $ExpectedCommit){throw 'Production target differs from qualified commit'}
  & git -C $prod merge-base --is-ancestor $previous $target
  if($LASTEXITCODE -ne 0){throw 'Production Git history diverged'}
  & git -C $prod merge --ff-only origin/main
  if($LASTEXITCODE -ne 0){throw 'Production Git fast-forward failed'}
  if($previous -eq $ExpectedCommit){
    $steps.pc_update='ALREADY_CURRENT';Persist
    Write-Host 'ORION_PC_UPDATE> ALREADY_CURRENT'
  } else {
    $updater=Join-Path $prod 'scripts\apply_orion_update.ps1'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $updater -ExpectedCommit $ExpectedCommit -PreviousCommit $previous
    if($LASTEXITCODE -ne 0){throw 'PC updater failed to launch'}
    $statusPath=Join-Path $state 'update-status.json'
    $deadline=(Get-Date).AddMinutes(18)
    $passed=$false
    while((Get-Date) -lt $deadline){
      Start-Sleep -Seconds 2
      if(Test-Path $statusPath){
        try {
          $st=Get-Content $statusPath -Raw | ConvertFrom-Json
          if($st.commit -eq $ExpectedCommit -and $st.state -eq 'pass'){$passed=$true;break}
          if($st.commit -eq $ExpectedCommit -and $st.state -eq 'failed'){throw ('PC update failed: '+$st.message)}
        } catch {if($_.Exception.Message -like 'PC update failed:*'){throw}}
      }
    }
    if(!$passed){throw 'PC update did not report PASS within 18 minutes'}
    $steps.pc_update='PASS';Persist
    Write-Host 'ORION_PC_UPDATE> PASS'
  }
  $sdk=if($env:ANDROID_SDK_ROOT){$env:ANDROID_SDK_ROOT}elseif(Test-Path 'E:\Android\Sdk'){'E:\Android\Sdk'}else{Join-Path $env:LOCALAPPDATA 'Android\Sdk'}
  $adb=Join-Path $sdk 'platform-tools\adb.exe'
  if(!(Test-Path $adb)){throw 'ADB missing; PC updated but Android not updated'}
  $devices=@(& $adb devices | Where-Object {$_ -match '^\S+\s+device$'})
  if($devices.Count -ne 1){throw 'Exactly one connected authorized phone required'}
  $serial=($devices[0] -split '\s+')[0]
  $apk=Join-Path $prod 'dist\ORION-V3-debug.apk'
  if(!(Test-Path $apk)){throw 'PC updater did not produce Android APK'}
  $aapt=Get-ChildItem (Join-Path $sdk 'build-tools') -Filter 'aapt.exe' -Recurse -File | Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
  $signer=Get-ChildItem (Join-Path $sdk 'build-tools') -Filter 'apksigner.bat' -Recurse -File | Sort-Object FullName -Descending | Select-Object -First 1 -ExpandProperty FullName
  if(!$aapt -or !$signer){throw 'Android package verification tools unavailable'}
  $badge=(& $aapt dump badging $apk | Select-String '^package:').ToString()
  if($LASTEXITCODE -ne 0 -or $badge -notmatch "name='com\.sadusor\.orionv3'"){throw 'Android APK identity wrong'}
  $apkCert=@(& $signer verify --print-certs $apk | Select-String 'Signer #1 certificate SHA-256 digest:')
  if($LASTEXITCODE -ne 0 -or $apkCert.Count -ne 1){throw 'Candidate signing certificate unavailable'}
  $remote=@(& $adb -s $serial shell pm path com.sadusor.orionv3 | Where-Object {$_ -match '^package:'} | Select-Object -First 1)
  if(!$remote){throw 'Installed ORION not found: refusing replace'}
  $temporary=Join-Path $env:TEMP ('orion-installed-'+[guid]::NewGuid().ToString('N')+'.apk')
  try{
    & $adb -s $serial pull (($remote[0] -replace '^package:','').Trim()) $temporary | Out-Null
    if($LASTEXITCODE -ne 0){throw 'Installed APK cannot be verified'}
    $oldCert=@(& $signer verify --print-certs $temporary | Select-String 'Signer #1 certificate SHA-256 digest:')
    if($LASTEXITCODE -ne 0 -or $oldCert.Count -ne 1 -or $apkCert[0].ToString() -ne $oldCert[0].ToString()){throw 'Signing certificate mismatch; Android not modified'}
  } finally {Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue}
  & $adb -s $serial install -r $apk
  if($LASTEXITCODE -ne 0){throw 'Android in-place install failed'}
  $installed=@(& $adb -s $serial shell pm path com.sadusor.orionv3)
  if($LASTEXITCODE -ne 0 -or !($installed -match '^package:')){throw 'ORION missing after install'}
  $steps.android_update='PASS';Persist
  Write-Host 'ORION_ANDROID_IN_PLACE_UPDATE> PASS'
  $orion2=@(& $adb -s $serial shell pm list packages com.sadusor.orionv3.archivequal)
  if($orion2 -match '^package:com\.sadusor\.orionv3\.archivequal$'){
    & $adb -s $serial uninstall com.sadusor.orionv3.archivequal
    if($LASTEXITCODE -ne 0){throw 'ORION2 uninstall failed'}
    $steps.orion2_removal='PASS';Persist
    Write-Host 'ORION2_REMOVAL> PASS'
  }else{$steps.orion2_removal='ALREADY_ABSENT';Persist;Write-Host 'ORION2_REMOVAL> ALREADY_ABSENT'}
  $steps.result='PASS_WITH_ARCHIVE_NETWORK_NOT_ACTIVATED';Persist
  Write-Host "FINAL_OWNER_DEPLOYMENT> PASS"
  Write-Host "FINAL_DEPLOYMENT_REPORT> $report"
}catch{
  $steps.result='BLOCKED: '+$_.Exception.Message;Persist
  Write-Host ('FINAL_OWNER_DEPLOYMENT> BLOCKED '+$_.Exception.Message)
  throw
}
