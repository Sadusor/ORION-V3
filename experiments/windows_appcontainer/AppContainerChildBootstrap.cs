// ORION V3 experimental AppContainer native child launch gate. No ORION/Hands execution.
using System;using System.ComponentModel;using System.Diagnostics;using System.Runtime.InteropServices;using System.Security.Principal;
internal static class Program{
 const uint SUSPENDED=4,EXTENDED=0x80000,KILL_ON_CLOSE=0x2000;
 const int ATTR_SECURITY_CAPABILITIES=0x00020009;
 [StructLayout(LayoutKind.Sequential)]struct SecurityCapabilities{public IntPtr Sid,Capabilities;public uint Count,Reserved;}
 [StructLayout(LayoutKind.Sequential,CharSet=CharSet.Unicode)]struct StartupInfo{public uint cb;public IntPtr reserved,desktop,title;public uint x,y,xSize,ySize,xChars,yChars,fill,flags;public ushort show,cbReserved;public IntPtr reserved2,input,output,error;}
 [StructLayout(LayoutKind.Sequential)]struct StartupInfoEx{public StartupInfo Startup;public IntPtr Attributes;}
 [StructLayout(LayoutKind.Sequential)]struct ProcessInfo{public IntPtr Process,Thread;public uint Pid,Tid;}
 [StructLayout(LayoutKind.Sequential)]struct IoCounters{public ulong a,b,c,d,e,f;}
 [StructLayout(LayoutKind.Sequential)]struct BasicLimits{public long a,b;public uint Flags;public UIntPtr c,d;public uint e;public UIntPtr f;public uint g,h;}
 [StructLayout(LayoutKind.Sequential)]struct ExtendedLimits{public BasicLimits Basic;public IoCounters Io;public UIntPtr a,b,c,d;}
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)]static extern int CreateAppContainerProfile(string name,string display,string description,IntPtr caps,uint count,out IntPtr sid);
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)]static extern int DeleteAppContainerProfile(string name);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool InitializeProcThreadAttributeList(IntPtr list,int count,int flags,ref IntPtr size);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool UpdateProcThreadAttribute(IntPtr list,uint flags,IntPtr attribute,IntPtr value,IntPtr size,IntPtr previous,IntPtr returned);
 [DllImport("kernel32.dll")]static extern void DeleteProcThreadAttributeList(IntPtr list);
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode,SetLastError=true)]static extern bool CreateProcessW(string application,string command,IntPtr pa,IntPtr ta,bool inherit,uint flags,IntPtr env,string cwd,ref StartupInfoEx startup,out ProcessInfo process);
 [DllImport("kernel32.dll",SetLastError=true)]static extern IntPtr CreateJobObjectW(IntPtr attrs,string? name);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool SetInformationJobObject(IntPtr job,int cls,ref ExtendedLimits info,uint size);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll",SetLastError=true)]static extern uint ResumeThread(IntPtr thread);
 [DllImport("kernel32.dll",SetLastError=true)]static extern uint WaitForSingleObject(IntPtr handle,uint timeout);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool GetExitCodeProcess(IntPtr handle,out uint code);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool TerminateProcess(IntPtr handle,uint code);
 [DllImport("kernel32.dll",SetLastError=true)]static extern bool CloseHandle(IntPtr handle);
 [DllImport("kernel32.dll")]static extern IntPtr LocalFree(IntPtr ptr);
 static void Check(bool ok,string name){if(!ok)throw new Win32Exception(Marshal.GetLastWin32Error(),name);}
 static string Hex(int n)=>"0x"+unchecked((uint)n).ToString("X8");
 static int Main(){
  if(!OperatingSystem.IsWindows())return 2;
  string name="ORION.V3.Child."+Guid.NewGuid().ToString("N");IntPtr sid=IntPtr.Zero,list=IntPtr.Zero,cap=IntPtr.Zero,job=IntPtr.Zero;ProcessInfo child=default;bool profile=false,initialized=false;int status=1;
  try{
   int hr=CreateAppContainerProfile(name,"ORION disposable child","No production execution",IntPtr.Zero,0,out sid);
   Console.WriteLine("PROFILE_HRESULT> "+Hex(hr));if(hr<0||sid==IntPtr.Zero)throw new Exception("CREATE_PROFILE_FAILED");
   profile=true;Console.WriteLine("PROFILE_SID> "+new SecurityIdentifier(sid).Value);
   IntPtr size=IntPtr.Zero;InitializeProcThreadAttributeList(IntPtr.Zero,1,0,ref size);
   if(size==IntPtr.Zero)throw new Exception("ATTRIBUTE_SIZE_FAILED");
   list=Marshal.AllocHGlobal(size);Check(InitializeProcThreadAttributeList(list,1,0,ref size),"InitializeProcThreadAttributeList");initialized=true;
   cap=Marshal.AllocHGlobal(Marshal.SizeOf<SecurityCapabilities>());Marshal.StructureToPtr(new SecurityCapabilities{Sid=sid},cap,false);
   Check(UpdateProcThreadAttribute(list,0,new IntPtr(ATTR_SECURITY_CAPABILITIES),cap,new IntPtr(Marshal.SizeOf<SecurityCapabilities>()),IntPtr.Zero,IntPtr.Zero),"UpdateProcThreadAttribute");
   job=CreateJobObjectW(IntPtr.Zero,null);if(job==IntPtr.Zero)throw new Win32Exception(Marshal.GetLastWin32Error(),"CreateJobObject");
   var limits=new ExtendedLimits();limits.Basic.Flags=KILL_ON_CLOSE;
   Check(SetInformationJobObject(job,9,ref limits,(uint)Marshal.SizeOf<ExtendedLimits>()),"SetInformationJobObject");
   string exe=System.IO.Path.Combine(Environment.SystemDirectory,"cmd.exe");
   var startup=new StartupInfoEx{Startup=new StartupInfo{cb=(uint)Marshal.SizeOf<StartupInfoEx>()},Attributes=list};
   Check(CreateProcessW(exe,"\""+exe+"\" /d /c exit 0",IntPtr.Zero,IntPtr.Zero,false,SUSPENDED|EXTENDED,IntPtr.Zero,Environment.SystemDirectory,ref startup,out child),"CreateProcessW_AppContainer");
   Console.WriteLine("CHILD_CREATED> PASS PID="+child.Pid);
   Check(AssignProcessToJobObject(job,child.Process),"AssignProcessToJobObject");
   Console.WriteLine("JOB_ASSIGN> PASS");
   if(ResumeThread(child.Thread)==uint.MaxValue)throw new Win32Exception(Marshal.GetLastWin32Error(),"ResumeThread");
   uint wait=WaitForSingleObject(child.Process,10000);if(wait!=0)throw new Exception("CHILD_WAIT_FAILED_OR_TIMEOUT "+wait);
   Check(GetExitCodeProcess(child.Process,out uint exit),"GetExitCodeProcess");
   Console.WriteLine("CHILD_EXIT> "+Hex(unchecked((int)exit)));
   if(exit!=0)throw new Exception("CHILD_BOOTSTRAP_FAILED");
   Console.WriteLine("APPCONTAINER_CHILD_BOOTSTRAP> PASS");
   status=0;
  }catch(Exception ex){Console.WriteLine("APPCONTAINER_CHILD_BOOTSTRAP> FAIL "+ex.Message);}
  finally{
   if(child.Process!=IntPtr.Zero){TerminateProcess(child.Process,1);CloseHandle(child.Process);}
   if(child.Thread!=IntPtr.Zero)CloseHandle(child.Thread);
   if(job!=IntPtr.Zero)CloseHandle(job);
   if(initialized)DeleteProcThreadAttributeList(list);
   if(list!=IntPtr.Zero)Marshal.FreeHGlobal(list);
   if(cap!=IntPtr.Zero)Marshal.FreeHGlobal(cap);
   if(sid!=IntPtr.Zero)LocalFree(sid);
   if(profile){int hr=DeleteAppContainerProfile(name);Console.WriteLine("PROFILE_DELETE_HRESULT> "+Hex(hr));if(hr<0)status=7;}
   Console.WriteLine("FILESYSTEM_NETWORK_DESCENDANTS> UNTESTED");
   Console.WriteLine("REAL_ORION_EXECUTION> DISABLED");
  }
  return status;
 }
}
