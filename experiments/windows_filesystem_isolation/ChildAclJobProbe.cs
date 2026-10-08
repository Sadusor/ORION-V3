// ORION experimental restricted-token capability probe. NOT filesystem/network isolation.
// No elevated privileges, account changes, ACL changes, WFP changes or real Hands execution.
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.IO;
using System.Security.AccessControl;
using System.Security.Principal;
internal static class Program {
 const uint TOKEN_DUPLICATE=0x0002, TOKEN_ASSIGN_PRIMARY=0x0001, TOKEN_QUERY=0x0008, TOKEN_ADJUST_DEFAULT=0x0080, TOKEN_ADJUST_SESSIONID=0x0100;
 const uint DISABLE_MAX_PRIVILEGE=0x1, CREATE_SUSPENDED=0x4, CREATE_NO_WINDOW=0x08000000;
 const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE=0x2000;
 [StructLayout(LayoutKind.Sequential)] struct SID_AND_ATTRIBUTES { public IntPtr Sid; public uint Attributes; }
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
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool GetExitCodeProcess(IntPtr process,out uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateProcess(IntPtr process,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool TerminateJobObject(IntPtr job,uint code);
 [DllImport("kernel32.dll",SetLastError=true)] static extern uint WaitForSingleObject(IntPtr handle,uint ms);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
 static void Ensure(bool success,string step) { if(!success) throw new Win32Exception(Marshal.GetLastWin32Error(),step); }
 static int Main() {
 if(!OperatingSystem.IsWindows()) return 2;
 IntPtr source=IntPtr.Zero,restricted=IntPtr.Zero,job=IntPtr.Zero,sidMemory=IntPtr.Zero,sidEntry=IntPtr.Zero; PROCESS_INFORMATION child=default;
 string root=System.IO.Path.Combine(System.IO.Path.GetTempPath(),"orion-token-probe-"+Guid.NewGuid().ToString("N"));
 try {
 System.IO.Directory.CreateDirectory(root);
 string inside=Path.Combine(root,"inside"),outside=Path.Combine(root,"outside");
 Directory.CreateDirectory(inside);Directory.CreateDirectory(outside);
 string allowed=Path.Combine(inside,"allowed.txt"),forbidden=Path.Combine(outside,"forbidden.txt"),result=Path.Combine(inside,"result.txt");
 string nonce=Guid.NewGuid().ToString("N");File.WriteAllText(allowed,nonce);File.WriteAllText(forbidden,nonce);
 var sid=new SecurityIdentifier(WellKnownSidType.RestrictedCodeSid,null);
 byte[] bytes=new byte[sid.BinaryLength];sid.GetBinaryForm(bytes,0);
 sidMemory=Marshal.AllocHGlobal(bytes.Length);Marshal.Copy(bytes,0,sidMemory,bytes.Length);
 sidEntry=Marshal.AllocHGlobal(Marshal.SizeOf<SID_AND_ATTRIBUTES>());
 Marshal.StructureToPtr(new SID_AND_ATTRIBUTES{Sid=sidMemory,Attributes=0},sidEntry,false);
 foreach(var file in new[]{allowed,result}) {
  if(file==result)File.WriteAllText(file,"pending");
  var acl=new FileInfo(file).GetAccessControl();
  acl.AddAccessRule(new FileSystemAccessRule(sid,FileSystemRights.Read|FileSystemRights.Write,AccessControlType.Allow));
  new FileInfo(file).SetAccessControl(acl);
 }
 string script=Path.Combine(inside,"native_child.exe");
 string nativeSource=Path.Combine(root,"native_child.c");
 File.WriteAllText(nativeSource,@"#include <windows.h>
int main(int argc,char**argv){
 if(argc!=4)return 10;
 const char* paths[2]={argv[1],argv[2]};
 char results[5]={'D','D','D','D',0};
 for(int i=0;i<2;i++){
 HANDLE h=CreateFileA(paths[i],GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
 if(h!=INVALID_HANDLE_VALUE){results[i*2]='A';CloseHandle(h);}
 h=CreateFileA(paths[i],FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,NULL,OPEN_EXISTING,FILE_ATTRIBUTE_NORMAL,NULL);
 if(h!=INVALID_HANDLE_VALUE){results[i*2+1]='A';CloseHandle(h);}
 }
 HANDLE o=CreateFileA(argv[3],GENERIC_WRITE,FILE_SHARE_READ,NULL,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,NULL);
 if(o==INVALID_HANDLE_VALUE)return 11;
 DWORD n=0;BOOL ok=WriteFile(o,results,4,&n,NULL);CloseHandle(o);
 if(!ok||n!=4)return 12;
 Sleep(90000);return 0;
 }");
 string vs=Environment.GetEnvironmentVariable("ORION_VS_INSTALL")??"";
 if(string.IsNullOrWhiteSpace(vs))throw new Exception("ORION_VS_INSTALL missing");
 string vcvars=Path.Combine(vs,"VC","Auxiliary","Build","vcvars64.bat");
 string compileBat=Path.Combine(root,"compile-native.cmd");
 File.WriteAllText(compileBat,"@echo off\r\ncall \""+vcvars+"\" >nul\r\nif errorlevel 1 exit /b 10\r\ncl /nologo /W4 /WX /MT /Fe:\""+script+"\" \""+nativeSource+"\"\r\nexit /b %errorlevel%\r\n");
 var build=new ProcessStartInfo("cmd.exe"){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};
 build.ArgumentList.Add("/d");build.ArgumentList.Add("/c");build.ArgumentList.Add(compileBat);
 using(var compiler=Process.Start(build)??throw new Exception("MSVC failed to start")){
 string output=compiler.StandardOutput.ReadToEnd()+compiler.StandardError.ReadToEnd();
 compiler.WaitForExit();if(compiler.ExitCode!=0)throw new Exception("MSVC_BUILD_FAILED "+output);
 }
 var scriptAcl=new FileInfo(script).GetAccessControl();
 scriptAcl.AddAccessRule(new FileSystemAccessRule(sid,FileSystemRights.ReadAndExecute,AccessControlType.Allow));
 new FileInfo(script).SetAccessControl(scriptAcl);
 Ensure(OpenProcessToken(Process.GetCurrentProcess().Handle,TOKEN_DUPLICATE|TOKEN_ASSIGN_PRIMARY|TOKEN_QUERY|TOKEN_ADJUST_DEFAULT|TOKEN_ADJUST_SESSIONID,out source),"OpenProcessToken");
 Ensure(CreateRestrictedToken(source,DISABLE_MAX_PRIVILEGE,0,IntPtr.Zero,0,IntPtr.Zero,1,sidEntry,out restricted),"CreateRestrictedToken");
 job=CreateJobObjectW(IntPtr.Zero,null); if(job==IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(),"CreateJobObjectW");
 var limits=new EXT(); limits.basic.flags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
 Ensure(SetInformationJobObject(job,9,ref limits,(uint)Marshal.SizeOf<EXT>()),"SetInformationJobObject");
 string ps=script;
 Console.WriteLine("DIAGNOSTIC> native executable prepared");
 foreach(string path in new[]{script,Path.Combine(Environment.SystemDirectory,"kernel32.dll"),Path.Combine(Environment.SystemDirectory,"kernelbase.dll"),Path.Combine(Environment.SystemDirectory,"ntdll.dll")}){
  try {
   bool readable=false;string error="";
   WindowsIdentity.RunImpersonated(new Microsoft.Win32.SafeHandles.SafeAccessTokenHandle(restricted),()=>{
    try{using var stream=new FileStream(path,FileMode.Open,FileAccess.Read,FileShare.ReadWrite|FileShare.Delete);readable=stream.ReadByte()>=0;}
    catch(Exception ex){error=ex.GetType().Name+":"+ex.HResult.ToString("X8");}
   });
   Console.WriteLine("RESTRICTED_READ> "+Path.GetFileName(path)+" "+(readable?"ALLOW":"DENY")+" "+error);
  }catch(Exception ex){Console.WriteLine("RESTRICTED_READ> "+Path.GetFileName(path)+" DIAGNOSTIC_ERROR "+ex.GetType().Name);}
 }

 var command=new StringBuilder("\""+ps+"\" \""+allowed+"\" \""+forbidden+"\" \""+result+"\"");
 var si=new STARTUPINFO{cb=(uint)Marshal.SizeOf<STARTUPINFO>()};
 Ensure(CreateProcessAsUserW(restricted,ps,command,IntPtr.Zero,IntPtr.Zero,false,CREATE_SUSPENDED|CREATE_NO_WINDOW,IntPtr.Zero,root,ref si,out child),"CreateProcessAsUserW");
 Ensure(AssignProcessToJobObject(job,child.hProcess),"AssignProcessToJobObject");
 if(ResumeThread(child.hThread)==uint.MaxValue) throw new Win32Exception(Marshal.GetLastWin32Error(),"ResumeThread");
 var sw=Stopwatch.StartNew();
 while(File.ReadAllText(result)=="pending" && sw.ElapsedMilliseconds<15000) {
  if(WaitForSingleObject(child.hProcess,0)==0){Ensure(GetExitCodeProcess(child.hProcess,out uint code),"GetExitCodeProcess");throw new Exception("CHILD_BOOTSTRAP_BLOCKED: exit=0x"+code.ToString("X8"));}
  System.Threading.Thread.Sleep(100);
 }
 string evidence=File.ReadAllText(result);
 if(evidence=="pending")throw new Exception("CHILD_BOOTSTRAP_BLOCKED: timeout");
 bool valid=evidence=="AADD" && File.ReadAllText(forbidden)==nonce;
 Console.WriteLine("CHILD_ACL_RESULT> "+evidence+" (A=allowed,D=denied; read/write inside then outside)");
 Console.WriteLine("OUTSIDE_UNCHANGED> "+(File.ReadAllText(forbidden)==nonce));
 if(!valid)throw new Exception("CHILD_ACL_GATE_FAIL");
 Ensure(TerminateJobObject(job,1),"TerminateJobObject");
 if(WaitForSingleObject(child.hProcess,5000)!=0) throw new Exception("Child survived STOP");
 Console.WriteLine("CHILD_ACL_JOB> PASS_CHILD_BOUNDARY_ONLY");

 Console.WriteLine("JUNCTION_AND_DESCENDANTS> UNTESTED\nNETWORK_ISOLATION> UNTESTED\nREAL_EXECUTION> DISABLED");
 return 0;
 } catch(Exception ex) { Console.Error.WriteLine("TOKEN_PROBE> BLOCKED "+ex.Message); return 1; }
 finally {
 if(child.hProcess!=IntPtr.Zero){TerminateProcess(child.hProcess,1);CloseHandle(child.hProcess);}
 if(child.hThread!=IntPtr.Zero)CloseHandle(child.hThread);
 if(job!=IntPtr.Zero)CloseHandle(job);
 if(restricted!=IntPtr.Zero)CloseHandle(restricted);
 if(source!=IntPtr.Zero)CloseHandle(source);
 if(sidEntry!=IntPtr.Zero)Marshal.FreeHGlobal(sidEntry);
 if(sidMemory!=IntPtr.Zero)Marshal.FreeHGlobal(sidMemory);
 try{System.IO.Directory.Delete(root,true);}catch{}
 }
 }
}
