// ORION experimental restricted-token capability probe. NOT filesystem/network isolation.
// No elevated privileges, account changes, ACL changes, WFP changes or real Hands execution.
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
internal static class Program {
 const uint TOKEN_DUPLICATE=0x0002, TOKEN_ASSIGN_PRIMARY=0x0001, TOKEN_QUERY=0x0008, TOKEN_ADJUST_DEFAULT=0x0080, TOKEN_ADJUST_SESSIONID=0x0100;
 const uint DISABLE_MAX_PRIVILEGE=0x1, CREATE_SUSPENDED=0x4, CREATE_NO_WINDOW=0x08000000;
 const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE=0x2000;
 [StructLayout(LayoutKind.Sequential)] struct STARTUPINFO {
 public uint cb; public string? lpReserved,lpDesktop,lpTitle; public uint dwX,dwY,dwXSize,dwYSize,dwXCountChars,dwYCountChars,dwFillAttribute,dwFlags; public ushort wShowWindow,cbReserved2; public IntPtr lpReserved2,hStdInput,hStdOutput,hStdError;
 }
 [StructLayout(LayoutKind.Sequential)] struct PROCESS_INFORMATION { public IntPtr hProcess,hThread; public uint dwProcessId,dwThreadId; }
 [StructLayout(LayoutKind.Sequential)] struct IO_COUNTERS { public ulong a,b,c,d,e,f; }
 [StructLayout(LayoutKind.Sequential)] struct BASIC { public long a,b; public uint flags; public UIntPtr c,d; public uint e; public UIntPtr f; public uint g,h; }
 [StructLayout(LayoutKind.Sequential)] struct EXT { public BASIC basic; public IO_COUNTERS io; public UIntPtr a,b,c,d; }
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool OpenProcessToken(IntPtr process,uint access,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool CreateRestrictedToken(IntPtr existing,uint flags,uint disableCount,IntPtr disabled,uint deleteCount,IntPtr deleted,uint restrictCount,IntPtr restricted,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true,CharSet=CharSet.Unicode)] static extern bool CreateProcessAsUserW(IntPtr token,string? app,StringBuilder command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string? cwd,ref STARTUPINFO si,out PROCESS_INFORMATION pi);
 [DllImport("kernel32.dll",SetLastError=true)] static extern IntPtr CreateJobObjectW(IntPtr attrs,string? name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int cls,ref EXT info,uint size);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateJobObject(IntPtr job,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle,uint ms);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
 static void Ensure(bool success,string step) { if(!success) throw new Win32Exception(Marshal.GetLastWin32Error(),step); }
 static int Main() {
 if(!OperatingSystem.IsWindows()) return 2;
 IntPtr source=IntPtr.Zero,restricted=IntPtr.Zero,job=IntPtr.Zero; PROCESS_INFORMATION child=default;
 string root=System.IO.Path.Combine(System.IO.Path.GetTempPath(),"orion-token-probe-"+Guid.NewGuid().ToString("N"));
 try {
 System.IO.Directory.CreateDirectory(root);
 string marker=System.IO.Path.Combine(root,"child-token.txt");
 string script=System.IO.Path.Combine(root,"child.ps1");
 System.IO.File.WriteAllText(script,"param([string]$Marker)\nwhoami /priv | Out-File -LiteralPath $Marker -Encoding utf8\nStart-Sleep -Seconds 90\n");
 Ensure(OpenProcessToken(Process.GetCurrentProcess().Handle,TOKEN_DUPLICATE|TOKEN_ASSIGN_PRIMARY|TOKEN_QUERY|TOKEN_ADJUST_DEFAULT|TOKEN_ADJUST_SESSIONID,out source),"OpenProcessToken");
 Ensure(CreateRestrictedToken(source,DISABLE_MAX_PRIVILEGE,0,IntPtr.Zero,0,IntPtr.Zero,0,IntPtr.Zero,out restricted),"CreateRestrictedToken");
 job=CreateJobObjectW(IntPtr.Zero,null); if(job==IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(),"CreateJobObjectW");
 var limits=new EXT(); limits.basic.flags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
 Ensure(SetInformationJobObject(job,9,ref limits,(uint)Marshal.SizeOf<EXT>()),"SetInformationJobObject");
 string ps=System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System),"WindowsPowerShell","v1.0","powershell.exe");
 var command=new StringBuilder("\""+ps+"\" -NoProfile -NonInteractive -File \""+script+"\" -Marker \""+marker+"\"");
 var si=new STARTUPINFO{cb=(uint)Marshal.SizeOf<STARTUPINFO>()};
 Ensure(CreateProcessAsUserW(restricted,ps,command,IntPtr.Zero,IntPtr.Zero,false,CREATE_SUSPENDED|CREATE_NO_WINDOW,IntPtr.Zero,root,ref si,out child),"CreateProcessAsUserW");
 Ensure(AssignProcessToJobObject(job,child.hProcess),"AssignProcessToJobObject");
 if(ResumeThread(child.hThread)==uint.MaxValue) throw new Win32Exception(Marshal.GetLastWin32Error(),"ResumeThread");
 var sw=Stopwatch.StartNew(); while(!System.IO.File.Exists(marker)&&sw.ElapsedMilliseconds<15000) {
 if(WaitForSingleObject(child.hProcess,0)==0) throw new Exception("Child exited before writing token evidence");
 System.Threading.Thread.Sleep(100);
 }
 if(!System.IO.File.Exists(marker)) throw new Exception("Token evidence timeout");
 var evidence=System.IO.File.ReadAllText(marker);
 if(!evidence.Contains("SeChangeNotifyPrivilege",StringComparison.OrdinalIgnoreCase)) Console.Error.WriteLine("NOTE: localized whoami output; privilege inspection requires review");
 Ensure(TerminateJobObject(job,1),"TerminateJobObject");
 if(WaitForSingleObject(child.hProcess,5000)!=0) throw new Exception("Child survived STOP");
 Console.WriteLine("TOKEN_PROBE> PASS_LAUNCH_AND_JOB_ONLY");
 Console.WriteLine("CHILD_PRIVILEGES_BEGIN\n"+evidence+"\nCHILD_PRIVILEGES_END");
 Console.WriteLine("FILESYSTEM_ISOLATION> FALSE\nNETWORK_ISOLATION> FALSE\nREAL_EXECUTION> DISABLED");
 return 0;
 } catch(Exception ex) { Console.Error.WriteLine("TOKEN_PROBE> BLOCKED "+ex.Message); return 1; }
 finally {
 if(child.hProcess!=IntPtr.Zero){TerminateProcess(child.hProcess,1);CloseHandle(child.hProcess);}
 if(child.hThread!=IntPtr.Zero)CloseHandle(child.hThread);
 if(job!=IntPtr.Zero)CloseHandle(job);
 if(restricted!=IntPtr.Zero)CloseHandle(restricted);
 if(source!=IntPtr.Zero)CloseHandle(source);
 try{System.IO.Directory.Delete(root,true);}catch{}
 }
 }
}
