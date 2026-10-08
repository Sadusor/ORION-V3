# Read-only WFP audit readiness diagnostic. No system configuration changes.
$ErrorActionPreference = 'Continue'
Write-Host 'WFP_READINESS> START'
foreach($sub in @('Filtering Platform Packet Drop','Filtering Platform Connection')) {
 Write-Host ('SUBCATEGORY> '+$sub)
 $result = & auditpol.exe /get ("/subcategory:"+$sub) 2>&1
 $result | ForEach-Object { Write-Host ('AUDITPOL> '+$_) }
 Write-Host ('AUDITPOL_EXIT> '+$LASTEXITCODE)
}
try {
 $log = Get-WinEvent -ListLog Security -ErrorAction Stop
 Write-Host ('SECURITY_LOG> ACCESSIBLE ENABLED='+$log.IsEnabled)
} catch { Write-Host ('SECURITY_LOG> INCONCLUSIVE '+$_.Exception.Message) }
try {
 $events = @(Get-WinEvent -FilterHashtable @{LogName='Security';Id=5152,5157;StartTime=(Get-Date).AddHours(-24)} -MaxEvents 5 -ErrorAction Stop)
 Write-Host ('RECENT_WFP_EVENTS> '+$events.Count)
 foreach($e in $events) { Write-Host ('EVENT> '+$e.Id+' '+$e.TimeCreated.ToString('o')) }
} catch { Write-Host ('RECENT_WFP_EVENTS> INCONCLUSIVE '+$_.Exception.Message) }
Write-Host 'AUDIT_POLICY> UNCHANGED'
Write-Host 'NETWORK_QUALIFICATION> INCONCLUSIVE'
Write-Host 'REAL_ORION_EXECUTION> DISABLED'
