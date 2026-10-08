# Experimental Windows physical qualification: disposable AppContainer filesystem and native Winsock.
# NOT the full eight-gate qualification. Does not touch Remote V1 or production execution.
$ErrorActionPreference = 'Stop'
$sha = '7436d086e1af6f8c32a9f2e48e95806e196e88ce'
$base = "https://raw.githubusercontent.com/Sadusor/ORION-V3/$sha/experiments/windows_appcontainer/"
$root = Join-Path $env:TEMP ('orion-physical-gate-' + [guid]::NewGuid().ToString('N'))
$report = [ordered]@{source_commit=$sha; gate='partial_windows_physical'; status='FAIL'; checks=@(); production_execution=$false}
New-Item -ItemType Directory -Path $root -Force | Out-Null
function Fetch([string]$name,[string]$folder,[string]$target) {
 $dest=Join-Path $root $folder
 New-Item -ItemType Directory -Path $dest -Force | Out-Null
 Invoke-WebRequest -Uri ($base+$name) -OutFile (Join-Path $dest $target) -UseBasicParsing -TimeoutSec 45
}
function RunStep([string]$label,[string]$exe,[string[]]$arguments) {
 Write-Host "STEP> $label"
 & $exe @arguments
 if($LASTEXITCODE -ne 0){throw "$label failed exit=$LASTEXITCODE"}
}
try {
 if(-not [Environment]::OSVersion.Platform.ToString().Contains('Win32')) {throw 'WINDOWS_REQUIRED'}
 $dotnet=Get-Command dotnet -ErrorAction Stop
 Fetch 'AppContainerLifecycleProbe.csproj' 'fs' 'Probe.csproj'
 Fetch 'AppContainerWorkspaceWriteProbe.cs' 'fs' 'Program.cs'
 Fetch 'AppContainerLifecycleProbe.csproj' 'net' 'Probe.csproj'
 Fetch 'AppContainerNativeNetworkHarness.cs' 'net' 'Program.cs'
 Fetch 'NativeWinsockChild.csproj' 'child' 'NativeWinsockChild.csproj'
 Fetch 'NativeWinsockChild.cs' 'child' 'Program.cs'
 RunStep 'BUILD_FILESYSTEM_HARNESS' $dotnet.Source @('build',(Join-Path $root 'fs/Probe.csproj'),'-c','Release','-o',(Join-Path $root 'fs-out'),'-v','quiet')
 RunStep 'BUILD_NATIVE_CHILD' $dotnet.Source @('publish',(Join-Path $root 'child/NativeWinsockChild.csproj'),'-c','Release','-o',(Join-Path $root 'child-out'),'-v','quiet')
 RunStep 'BUILD_NETWORK_HARNESS' $dotnet.Source @('build',(Join-Path $root 'net/Probe.csproj'),'-c','Release','-o',(Join-Path $root 'net-out'),'-v','quiet')
 Copy-Item (Join-Path $root 'child-out/NativeWinsockChild.exe') (Join-Path $root 'net-out/NativeWinsockChild.exe') -Force
 foreach($item in @(@('FILESYSTEM',(Join-Path $root 'fs-out/Probe.dll'))),@('NETWORK',(Join-Path $root 'net-out/Probe.dll')))) {
  $label=$item[0];$dll=$item[1]
  $output= & $dotnet.Source $dll 2>&1
  $exit=$LASTEXITCODE
  $output | ForEach-Object {Write-Host "$label> $_"}
  $report.checks += @{name=$label;exit=$exit;output=@($output | ForEach-Object {"$_"})}
  if($exit -ne 0){throw "$label failed exit=$exit"}
  if($label -eq 'FILESYSTEM' -and -not (($output -join "`n") -match 'APPCONTAINER_FILESYSTEM> PASS_DISPOSABLE_FIXTURE_ONLY')){throw 'FILESYSTEM_MARKER_MISSING'}
  if($label -eq 'NETWORK' -and -not (($output -join "`n") -match 'NETWORK_GATE> PASS_NATIVE_WSAEACCES_CHILD_EXIT_0')){throw 'NETWORK_DENIAL_NOT_PROVEN'}
  if(-not (($output -join "`n") -match 'PROFILE_DELETE_HRESULT> 0x00000000')){throw "PROFILE_CLEANUP_NOT_PROVEN_$label"}
 }
 $report.status='PASS_PARTIAL'
 Write-Host 'PARTIAL_WINDOWS_PHYSICAL> PASS'
 Write-Host 'DESCENDANT_STOP_AND_FULL_CRASH> NOT_QUALIFIED'
} catch {
 $report.error="$($_.Exception.Message)"
 Write-Host "PARTIAL_WINDOWS_PHYSICAL> FAIL $($report.error)"
 throw
} finally {
 Write-Host ('MACHINE_EVIDENCE_JSON> '+($report | ConvertTo-Json -Depth 8 -Compress))
 try{Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction Stop;Write-Host 'BUILD_FIXTURE_CLEANUP> PASS'}
 catch{Write-Host "BUILD_FIXTURE_CLEANUP> FAIL $($_.Exception.Message)";throw}
 Write-Host 'REAL_ORION_EXECUTION> DISABLED'
}
