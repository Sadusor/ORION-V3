# Windows process containment V1 — experiment only
# Disposable child-process tree probe. NOT a sandbox: no restricted token, filesystem or network controls.
# Requires Windows PowerShell 5.1 or PowerShell 7 on Windows.
# Does not modify ORION/TheHands, machine policy, ACLs, or firewall.
param([int]$TimeoutSeconds = 15)
$ErrorActionPreference = 'Stop'
if (-not $IsWindows -and $PSVersionTable.PSEdition -eq 'Core') { throw 'Windows only' }
if ($TimeoutSeconds -lt 3 -or $TimeoutSeconds -gt 60) { throw 'TimeoutSeconds must be 3..60' }
$source = @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class OrionJobProbe {
  [StructLayout(LayoutKind.Sequential)] public struct IO_COUNTERS {
    public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount, ReadTransferCount, WriteTransferCount, OtherTransferCount;
  }
  [StructLayout(LayoutKind.Sequential)] public struct BASIC_LIMIT {
    public long PerProcessUserTimeLimit, PerJobUserTimeLimit;
    public uint LimitFlags;
    public UIntPtr MinimumWorkingSetSize, MaximumWorkingSetSize;
    public uint ActiveProcessLimit;
    public UIntPtr Affinity;
    public uint PriorityClass, SchedulingClass;
  }
  [StructLayout(LayoutKind.Sequential)] public struct EXT_LIMIT {
    public BASIC_LIMIT BasicLimitInformation;
    public IO_COUNTERS IoInfo;
    public UIntPtr ProcessMemoryLimit, JobMemoryLimit, PeakProcessMemoryUsed, PeakJobMemoryUsed;
  }
  [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
  public static extern IntPtr CreateJobObject(IntPtr attrs, string name);
  [DllImport("kernel32.dll", SetLastError=true)]
  [return: MarshalAs(UnmanagedType.Bool)]
  public static extern bool SetInformationJobObject(IntPtr job, int cls, ref EXT_LIMIT info, uint length);
  [DllImport("kernel32.dll", SetLastError=true)]
  [return: MarshalAs(UnmanagedType.Bool)]
  public static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
  [DllImport("kernel32.dll", SetLastError=true)]
  [return: MarshalAs(UnmanagedType.Bool)]
  public static extern bool TerminateJobObject(IntPtr job, uint exitCode);
  [DllImport("kernel32.dll", SetLastError=true)]
  [return: MarshalAs(UnmanagedType.Bool)]
  public static extern bool CloseHandle(IntPtr handle);
}
'@
Add-Type -TypeDefinition $source -ErrorAction Stop
$root = Join-Path ([System.IO.Path]::GetTempPath()) ('orion-job-probe-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $root -Force | Out-Null
$childScript = Join-Path $root 'child.ps1'
$marker = Join-Path $root 'started.txt'
# This child is deliberately benign. It writes only within its own disposable fixture.
@'
param([string]$Marker)
Set-Content -LiteralPath $Marker -Value $PID
Start-Sleep -Seconds 90
'@ | Set-Content -LiteralPath $childScript -Encoding UTF8
$job = [IntPtr]::Zero
$proc = $null
$assigned = $false
$terminated = $false
try {
  $job = [OrionJobProbe]::CreateJobObject([IntPtr]::Zero, $null)
  if ($job -eq [IntPtr]::Zero) { throw ('CreateJobObject Win32=' + [Runtime.InteropServices.Marshal]::GetLastWin32Error()) }
  $limits = New-Object OrionJobProbe+EXT_LIMIT
  $limits.BasicLimitInformation.LimitFlags = 0x2000 # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
  $length = [uint32][Runtime.InteropServices.Marshal]::SizeOf([type][OrionJobProbe+EXT_LIMIT])
  if (-not [OrionJobProbe]::SetInformationJobObject($job, 9, [ref]$limits, $length)) {
    throw ('SetInformationJobObject Win32=' + [Runtime.InteropServices.Marshal]::GetLastWin32Error())
  }
  $exe = (Get-Process -Id $PID).Path
  if (-not $exe) { throw 'Cannot resolve current PowerShell executable' }
  $psi = New-Object System.Diagnostics.ProcessStartInfo
  $psi.FileName = $exe
  $psi.Arguments = '-NoProfile -NonInteractive -File "' + $childScript + '" -Marker "' + $marker + '"'
  $psi.UseShellExecute = $false
  $proc = [System.Diagnostics.Process]::Start($psi)
  if (-not $proc) { throw 'Child launch failed' }
  # IMPORTANT: launch-then-assign has a race. This probe is NOT a security boundary.
  if (-not [OrionJobProbe]::AssignProcessToJobObject($job, $proc.Handle)) {
    throw ('AssignProcessToJobObject Win32=' + [Runtime.InteropServices.Marshal]::GetLastWin32Error())
  }
  $assigned = $true
  $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSeconds)
  while (-not (Test-Path -LiteralPath $marker) -and [DateTime]::UtcNow -lt $deadline) {
    Start-Sleep -Milliseconds 100
  }
  if (-not (Test-Path -LiteralPath $marker)) { throw 'Child marker timeout' }
  if (-not [OrionJobProbe]::TerminateJobObject($job, 1)) {
    throw ('TerminateJobObject Win32=' + [Runtime.InteropServices.Marshal]::GetLastWin32Error())
  }
  $terminated = $proc.WaitForExit(5000)
  if (-not $terminated) { throw 'Job termination did not stop child' }
  [pscustomobject]@{
    probe = 'windows-job-object-v1'
    status = 'PASS_PROCESS_TERMINATION_ONLY'
    childPid = $proc.Id
    jobAssigned = $assigned
    childTerminated = $terminated
    restrictedToken = $false
    filesystemIsolation = $false
    networkIsolation = $false
    secureLaunch = $false
    realExecutionAuthorized = $false
  } | ConvertTo-Json -Compress
}
finally {
  if ($job -ne [IntPtr]::Zero) { [void][OrionJobProbe]::CloseHandle($job) }
  if ($proc) {
    if (-not $proc.HasExited) { try { $proc.Kill() } catch {} }
    $proc.Dispose()
  }
  Remove-Item -LiteralPath $root -Recurse -Force -ErrorAction SilentlyContinue
}
