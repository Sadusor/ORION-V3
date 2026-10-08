// ORION V3 disposable AppContainer API qualification. No child execution or production integration.
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Security.Principal;
internal static class Program {
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)] static extern int CreateAppContainerProfile(string name,string display,string description,IntPtr capabilities,uint count,out IntPtr sid);
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)] static extern int DeleteAppContainerProfile(string name);
 [DllImport("userenv.dll",CharSet=CharSet.Unicode)] static extern int DeriveAppContainerSidFromAppContainerName(string name,out IntPtr sid);
 [DllImport("advapi32.dll",SetLastError=true)] static extern IntPtr GetSidSubAuthorityCount(IntPtr sid);
 [DllImport("kernel32.dll")] static extern IntPtr LocalFree(IntPtr hMem);
 static string Hex(int code)=>"0x"+unchecked((uint)code).ToString("X8");
 static int Main(){
  if(!OperatingSystem.IsWindows()){Console.WriteLine("GATE> WINDOWS_REQUIRED");return 2;}
  string name="ORION.V3.Disposable."+Guid.NewGuid().ToString("N");
  IntPtr sid=IntPtr.Zero,derived=IntPtr.Zero;
  bool created=false;
  try{
   int hr=CreateAppContainerProfile(name,"ORION V3 disposable qualification","API lifecycle only; no child launch",IntPtr.Zero,0,out sid);
   Console.WriteLine("CREATE_PROFILE_HRESULT> "+Hex(hr));
   if(hr<0||sid==IntPtr.Zero){Console.WriteLine("GATE_CREATE> FAIL");return 3;}
   created=true;
   Console.WriteLine("PROFILE_SID> "+new SecurityIdentifier(sid).Value);
   hr=DeriveAppContainerSidFromAppContainerName(name,out derived);
   Console.WriteLine("DERIVE_SID_HRESULT> "+Hex(hr));
   if(hr<0||derived==IntPtr.Zero){Console.WriteLine("GATE_DERIVE> FAIL");return 4;}
   bool equal=new SecurityIdentifier(sid).Value==new SecurityIdentifier(derived).Value;
   Console.WriteLine("GATE_DERIVE> "+(equal?"PASS":"FAIL"));
   return equal?0:5;
  }catch(Exception ex){Console.WriteLine("GATE_EXCEPTION> "+ex.GetType().Name+" "+ex.Message);return 6;}
  finally{
   if(sid!=IntPtr.Zero)LocalFree(sid);
   if(derived!=IntPtr.Zero)LocalFree(derived);
   if(created){
    int hr=DeleteAppContainerProfile(name);
    Console.WriteLine("DELETE_PROFILE_HRESULT> "+Hex(hr));
    Console.WriteLine("CLEANUP> "+(hr>=0?"PASS":"FAIL_PROFILE_REMAINS"));
   }
   Console.WriteLine("CHILD_LAUNCH> UNTESTED");
   Console.WriteLine("FILESYSTEM_NETWORK_STOP> UNTESTED");
   Console.WriteLine("REAL_EXECUTION> DISABLED");
  }
 }
}
