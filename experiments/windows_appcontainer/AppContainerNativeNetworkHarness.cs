// ORION V3 experimental AppContainer native child launch gate. No ORION/Hands execution.
using System;using System.IO;using System.Net;using System.Net.Sockets;using System.Threading.Tasks;using System.Security.AccessControl;using System.ComponentModel;using System.Diagnostics;using System.Runtime.InteropServices;using System.Security.Principal;
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
 static string Q(string path)=>((char)34)+path+((char)34);
 static int Main(){
  if(!OperatingSystem.IsWindows())return 2;
  string name="ORION.V3.Child."+Guid.NewGuid().ToString("N");IntPtr sid=IntPtr.Zero,list=IntPtr.Zero,cap=IntPtr.Zero,job=IntPtr.Zero;ProcessInfo child=default;bool profile=false,initialized=false;int status=1;string root=Path.Combine(Path.GetTempPath(),"orion-acl-gate-"+Guid.NewGuid().ToString("N"));
  try{
   int hr=CreateAppContainerProfile(name,"ORION disposable child","No production execution",IntPtr.Zero,0,out sid);
   Console.WriteLine("PROFILE_HRESULT> "+Hex(hr));if(hr<0||sid==IntPtr.Zero)throw new Exception("CREATE_PROFILE_FAILED");
   profile=true;var appSid=new SecurityIdentifier(sid);Console.WriteLine("PROFILE_SID> "+appSid.Value);
   Directory.CreateDirectory(root);
   string inside=Path.Combine(root,"inside"),outside=Path.Combine(root,"outside");
   Directory.CreateDirectory(inside);Directory.CreateDirectory(outside);
   string allowed=Path.Combine(inside,"allowed.txt"),denied=Path.Combine(outside,"denied.txt");
   string nonce=Guid.NewGuid().ToString("N");File.WriteAllText(allowed,nonce);File.WriteAllText(denied,nonce);
   // Explicit ACE on approved workspace only; outside receives no AppContainer grant.
   var acl=new DirectoryInfo(inside).GetAccessControl();
   acl.AddAccessRule(new FileSystemAccessRule(appSid,FileSystemRights.Modify|FileSystemRights.Synchronize,InheritanceFlags.ContainerInherit|InheritanceFlags.ObjectInherit,PropagationFlags.None,AccessControlType.Allow));
   new DirectoryInfo(inside).SetAccessControl(acl);
   // Existing file must also receive explicit ACE (created before directory ACE).
   var fileAcl=new FileInfo(allowed).GetAccessControl();
   fileAcl.AddAccessRule(new FileSystemAccessRule(appSid,FileSystemRights.Read,AccessControlType.Allow));
   new FileInfo(allowed).SetAccessControl(fileAcl);
   string output=Path.Combine(inside,"read_result.txt"),leak=Path.Combine(inside,"leak.txt");
   string approvedWrite=Path.Combine(inside,"approved_write.txt");
   string outsideWrite=Path.Combine(outside,"unauthorized.txt");
   using var listener=new TcpListener(IPAddress.Loopback,0);listener.Start();
   int port=((IPEndPoint)listener.LocalEndpoint).Port;
   using(var control=new TcpClient()){control.Connect(IPAddress.Loopback,port);using var accepted=listener.AcceptTcpClient();}
   Console.WriteLine("NETWORK_HOST_CONTROL> PASS PORT="+port);

   // Windows cmd builtins only; paths are disposable GUID-based paths under TEMP.
   string exe=Path.GetFullPath(Path.Combine(AppContext.BaseDirectory,"NativeWinsockChild.exe"));
   if(!File.Exists(exe))throw new Exception("NATIVE_CHILD_NOT_PUBLISHED");
   // Grant execute on disposable published binary only; never alter system paths.
   var exeAcl=new FileInfo(exe).GetAccessControl();
   exeAcl.AddAccessRule(new FileSystemAccessRule(appSid,FileSystemRights.ReadAndExecute,AccessControlType.Allow));
   new FileInfo(exe).SetAccessControl(exeAcl);
   Console.WriteLine("FIXTURE> DISPOSABLE_WORKSPACE_READY");
   IntPtr size=IntPtr.Zero;InitializeProcThreadAttributeList(IntPtr.Zero,1,0,ref size);
   if(size==IntPtr.Zero)throw new Exception("ATTRIBUTE_SIZE_FAILED");
   list=Marshal.AllocHGlobal(size);Check(InitializeProcThreadAttributeList(list,1,0,ref size),"InitializeProcThreadAttributeList");initialized=true;
   cap=Marshal.AllocHGlobal(Marshal.SizeOf<SecurityCapabilities>());Marshal.StructureToPtr(new SecurityCapabilities{Sid=sid},cap,false);
   Check(UpdateProcThreadAttribute(list,0,new IntPtr(ATTR_SECURITY_CAPABILITIES),cap,new IntPtr(Marshal.SizeOf<SecurityCapabilities>()),IntPtr.Zero,IntPtr.Zero),"UpdateProcThreadAttribute");
   job=CreateJobObjectW(IntPtr.Zero,null);if(job==IntPtr.Zero)throw new Win32Exception(Marshal.GetLastWin32Error(),"CreateJobObject");
   var limits=new ExtendedLimits();limits.Basic.Flags=KILL_ON_CLOSE;
   Check(SetInformationJobObject(job,9,ref limits,(uint)Marshal.SizeOf<ExtendedLimits>()),"SetInformationJobObject");

   var startup=new StartupInfoEx{Startup=new StartupInfo{cb=(uint)Marshal.SizeOf<StartupInfoEx>()},Attributes=list};
   Check(CreateProcessW(exe,"\""+exe+"\" "+port,IntPtr.Zero,IntPtr.Zero,false,SUSPENDED|EXTENDED,IntPtr.Zero,inside,ref startup,out child),"CreateProcessW_AppContainer");
   Console.WriteLine("CHILD_CREATED> PASS PID="+child.Pid);
   Check(AssignProcessToJobObject(job,child.Process),"AssignProcessToJobObject");
   Console.WriteLine("JOB_ASSIGN> PASS");
   if(ResumeThread(child.Thread)==uint.MaxValue)throw new Win32Exception(Marshal.GetLastWin32Error(),"ResumeThread");
   uint wait=WaitForSingleObject(child.Process,10000);if(wait!=0)throw new Exception("CHILD_WAIT_FAILED_OR_TIMEOUT "+wait);
   Check(GetExitCodeProcess(child.Process,out uint exit),"GetExitCodeProcess");
   Console.WriteLine("CHILD_EXIT> "+Hex(unchecked((int)exit)));
   if(exit!=0)throw new Exception("NATIVE_NETWORK_CHILD_EXIT_"+exit);
   Console.WriteLine("APPCONTAINER_CHILD_BOOTSTRAP> PASS");
   bool acceptedNetwork=listener.Pending();
   Console.WriteLine("NETWORK_LISTENER_PENDING> "+acceptedNetwork);
   if(acceptedNetwork)throw new Exception("NETWORK_EGRESS_ALLOWED");
   Console.WriteLine("NETWORK_GATE> PASS_NATIVE_WSAEACCES_CHILD_EXIT_0");
   Console.WriteLine("COMBINED_QUALIFICATION> INCOMPLETE_STOP_COMMIT_PENDING");
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
   try{Directory.Delete(root,true);}catch(Exception ex){Console.WriteLine("FIXTURE_CLEANUP> FAILED "+ex.GetType().Name);if(status==0)status=8;}
   Console.WriteLine("NETWORK_JUNCTION_HARDLINK_DESCENDANTS> UNTESTED");
   Console.WriteLine("REAL_ORION_EXECUTION> DISABLED");
  }
  return status;
 }
}
