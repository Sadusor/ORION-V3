$ErrorActionPreference='Stop'
Write-Host 'ORION_MODULE_INVENTORY> START'
$root='E:\ORION-V3'
$paths=@('E:\ORION-V3','E:\ORION-V3\ORION-V3','E:\Orion-V3')
foreach($p in $paths){if(Test-Path (Join-Path $p '.git')){$root=$p;break}}
if(!(Test-Path (Join-Path $root '.git'))){Write-Host 'ORION_MODULE_INVENTORY> NO_LOCAL_CHECKOUT';Write-Host 'REAL_EXECUTION> DISABLED';exit 0}
Write-Host ('REPOSITORY> '+$root)
$files=@(& git -C $root ls-files)
if($LASTEXITCODE -ne 0){throw 'GIT_LIST_FAILED'}
$patterns=@('work.loop','work_loop','vault','stop','verif','hand','appcontainer','model','qwen','authority')
foreach($pattern in $patterns){
 Write-Host ('MODULE_GROUP> '+$pattern)
 $files | Where-Object {$_ -match $pattern} | Select-Object -First 35 | ForEach-Object {Write-Host ('PATH> '+$_)}
}
Write-Host 'ORION_MODULE_INVENTORY> PASS_READ_ONLY'
Write-Host 'REMOTE_V1> UNCHANGED'
Write-Host 'REAL_EXECUTION> DISABLED'
