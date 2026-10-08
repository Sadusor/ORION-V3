# ORION V3 WFP diagnostic plan — no system policy changes
# Existing native child and AppContainer launch stay unchanged.
# Never classify a timeout alone as PASS.
param([int]$LookbackMinutes=10)
$ErrorActionPreference='Stop'
if($LookbackMinutes -lt 1 -or $LookbackMinutes -gt 60){throw 'Invalid lookback'}
$since=(Get-Date).AddMinutes(-$LookbackMinutes)
Write-Host 'WFP_AUDIT_DIAGNOSTIC> START'
try {
 $events=Get-WinEvent -FilterHashtable @{LogName='Security';Id=5152,5157;StartTime=$since} -ErrorAction Stop
 foreach($e in $events) {
  $xml=[xml]$e.ToXml()
  $data=@{}
  foreach($d in $xml.Event.EventData.Data){if($d.Name){$data[$d.Name]=$d.'#text'}}
  [pscustomobject]@{EventId=$e.Id;Time=$e.TimeCreated.ToString('o');Fields=$data} | ConvertTo-Json -Depth 5 -Compress
 }
 Write-Host 'WFP_AUDIT_DIAGNOSTIC> EVENTS_RETRIEVED_REVIEW_SID_PORT_AND_FILTER'
} catch {
 Write-Host ('WFP_AUDIT_DIAGNOSTIC> INCONCLUSIVE '+$_.Exception.Message)
}
Write-Host 'WFP_AUDIT_POLICY> UNCHANGED'
Write-Host 'NETWORK_QUALIFICATION> NOT_YET_PASS'
Write-Host 'REAL_ORION_EXECUTION> DISABLED'
