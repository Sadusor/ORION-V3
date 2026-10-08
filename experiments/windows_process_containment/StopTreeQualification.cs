// Disposable Windows STOP process-tree qualification. No ORION or TheHands processes touched.
using System;
using System.IO;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.ComponentModel;
using System.Threading;
using System.Text;
class Program {
 const uint SUSPENDED=4, NO_WINDOW=0x08000000, KILL_ON_CLOSE=0x2000;
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)] struct Startup {public uint cb;public IntPtr a,b,c;public uint x,y,w,h,cw,ch,fill,flags;public ushort show,reserved;public IntPtr d,e,f,g;}
 [StructLayout(LayoutKind.Sequential)] struct PI {public IntPtr process,thread;public uint pid,tid;}
 [StructLayout(LayoutKind.Sequential)] struct Io {public ulong a,b,c,d,e,f;}
 [StructLayout(LayoutKind.Sequential)] struct Basic {public long a,b;public uint flags;public UIntPtr c,d;public uint e;public UIntPtr f;public uint g,h;}
 [StructLayout(LayoutKind.Sequential)] struct Limits {public Basic basic;public Io io;public UIntPtr a,b,c,d;}
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern bool CreateProcessW(string app,StringBuilder cmd,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref Startup si,out PI pi);
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr CreateJobObjectW(IntPtr a,string? name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int cls,ref Limits lim,uint size);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateJobObject(IntPtr job,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle,uint ms);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr h);
 static void Require(bool ok,string why){if(!ok)throw new Exception(why+" WIN32="+Marshal.GetLastWin32Error());}
 static bool Alive(int pid){try{using var p=Process.GetProcessById(pid);return !p.HasExited;}catch(ArgumentException){return false;}}
 static void WaitFile(string path,int seconds){var sw=Stopwatch.StartNew();while(!File.Exists(path)&&sw.Elapsed<TimeSpan.FromSeconds(seconds))Thread.Sleep(50);Require(File.Exists(path),"MARKER_TIMEOUT_"+Path.GetFileName(path));}
 static int Main(){
  if(!OperatingSystem.IsWindows())return 2;
  string root=Path.Combine(Path.GetTempPath(),"orion-stop-tree-"+Guid.NewGuid().ToString("N"));
  Directory.CreateDirectory(root);
  IntPtr job=IntPtr.Zero;PI parent=default;
  try {
   string ps=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),"WindowsPowerShell","v1.0","powershell.exe");
   string script=Path.Combine(root,"tree.ps1");
   File.WriteAllText(script,@"param([string]$Root,[int]$Depth,[string]$Name)
$ErrorActionPreference='Stop'
Set-Content -LiteralPath (Join-Path $Root ($Name+'.pid')) -Value $PID
if($Depth -gt 0){
 $exe=(Get-Process -Id $PID).Path
 $next=$Name+'x'
 $args='-NoProfile -NonInteractive -ExecutionPolicy Bypass -File ""'+$PSCommandPath+'"" -Root ""'+$Root+'"" -Depth '+($Depth-1)+' -Name '+$next
 Start-Process -FilePath $exe -ArgumentList $args -WindowStyle Hidden
}
Start-Sleep -Seconds 90
");
   job=CreateJobObjectW(IntPtr.Zero,null);Require(job!=IntPtr.Zero,"JOB_CREATE");
   var lim=new Limits();lim.basic.flags=KILL_ON_CLOSE;
   Require(SetInformationJobObject(job,9,ref lim,(uint)Marshal.SizeOf<Limits>()),"JOB_LIMIT");
   var si=new Startup{cb=(uint)Marshal.SizeOf<Startup>()};
   var cmd=new StringBuilder("\""+ps+"\" -NoProfile -NonInteractive -ExecutionPolicy Bypass -File \""+script+"\" -Root \""+root+"\" -Depth 2 -Name p");
   Require(CreateProcessW(ps,cmd,IntPtr.Zero,IntPtr.Zero,false,SUSPENDED|NO_WINDOW,IntPtr.Zero,root,ref si,out parent),"CREATE_SUSPENDED");
   Require(AssignProcessToJobObject(job,parent.process),"ASSIGN_BEFORE_RESUME");
   Require(ResumeThread(parent.thread)!=uint.MaxValue,"RESUME");
   foreach(var n in new[]{"p","px","pxx"})WaitFile(Path.Combine(root,n+".pid"),12);
   int[] pids=Array.ConvertAll(new[]{"p","px","pxx"},n=>int.Parse(File.ReadAllText(Path.Combine(root,n+".pid")).Trim()));
   Require(pids.Distinct().Count()==3,"DUPLICATE_PIDS");
   foreach(int pid in pids)Require(Alive(pid),"PROCESS_EXITED_BEFORE_STOP_"+pid);
   Console.WriteLine("PROCESS_TREE_READY> PASS COUNT=3");
   Require(TerminateJobObject(job,77),"TERMINATE_JOB");
   Require(WaitForSingleObject(parent.process,5000)==0,"PARENT_SURVIVED");
   var sw=Stopwatch.StartNew();
   while(pids.Any(Alive)&&sw.Elapsed<TimeSpan.FromSeconds(5))Thread.Sleep(50);
   foreach(int pid in pids)Require(!Alive(pid),"ORPHAN_PID_"+pid);
   Console.WriteLine("STOP_DESCENDANTS> PASS COUNT=3");
   Console.WriteLine("STOP_NO_ORPHANS> PASS");
   Console.WriteLine("STOP_REPEATED> NOT_TESTED");
   Console.WriteLine("ORION_STOP_SERVICE_INTEGRATION> NOT_TESTED");
   Console.WriteLine("REAL_ORION_EXECUTION> DISABLED");
   return 0;
  }catch(Exception e){Console.WriteLine("STOP_DESCENDANTS> FAIL "+e.Message);return 1;}
  finally{
   if(job!=IntPtr.Zero)CloseHandle(job);
   if(parent.thread!=IntPtr.Zero)CloseHandle(parent.thread);
   if(parent.process!=IntPtr.Zero)CloseHandle(parent.process);
   try{Directory.Delete(root,true);}catch{}
  }
 }
}
