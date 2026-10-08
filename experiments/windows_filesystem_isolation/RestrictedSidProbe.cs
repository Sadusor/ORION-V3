// Windows restricted SID token constructor / inspection, experimental only.
// This is a prerequisite test, NOT filesystem confinement proof.
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Security.Principal;
internal static class Program {
 const uint TOKEN_DUPLICATE=2, TOKEN_QUERY=8, TOKEN_ASSIGN_PRIMARY=1, TOKEN_ADJUST_DEFAULT=0x80, TOKEN_ADJUST_SESSIONID=0x100;
 const uint DISABLE_MAX_PRIVILEGE=1;
 const int TokenRestrictedSids=11;
 [StructLayout(LayoutKind.Sequential)] struct SID_AND_ATTRIBUTES { public IntPtr Sid; public uint Attributes; }
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool OpenProcessToken(IntPtr process,uint access,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool CreateRestrictedToken(IntPtr existing,uint flags,uint disableCount,IntPtr disabled,uint deleteCount,IntPtr deleted,uint restrictCount,IntPtr restricting,out IntPtr token);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool GetTokenInformation(IntPtr token,int cls,IntPtr buffer,uint size,out uint needed);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr handle);
 static void Ensure(bool success,string operation) { if(!success) throw new Win32Exception(Marshal.GetLastWin32Error(),operation); }
 static int Main() {
 if(!OperatingSystem.IsWindows()) return 2;
 IntPtr source=IntPtr.Zero,restricted=IntPtr.Zero,sidBuffer=IntPtr.Zero,sidEntry=IntPtr.Zero,info=IntPtr.Zero;
 try {
 // Restricted Code is a well-known SID. This does not create an account or alter ACLs.
 var sid=new SecurityIdentifier(WellKnownSidType.RestrictedCodeSid,null);
 var sidBytes=new byte[sid.BinaryLength];sid.GetBinaryForm(sidBytes,0);
 sidBuffer=Marshal.AllocHGlobal(sidBytes.Length);Marshal.Copy(sidBytes,0,sidBuffer,sidBytes.Length);
 sidEntry=Marshal.AllocHGlobal(Marshal.SizeOf<SID_AND_ATTRIBUTES>());
 Marshal.StructureToPtr(new SID_AND_ATTRIBUTES{Sid=sidBuffer,Attributes=0},sidEntry,false);
 Ensure(OpenProcessToken(Process.GetCurrentProcess().Handle,TOKEN_DUPLICATE|TOKEN_QUERY|TOKEN_ASSIGN_PRIMARY|TOKEN_ADJUST_DEFAULT|TOKEN_ADJUST_SESSIONID,out source),"OpenProcessToken");
 Ensure(CreateRestrictedToken(source,DISABLE_MAX_PRIVILEGE,0,IntPtr.Zero,0,IntPtr.Zero,1,sidEntry,out restricted),"CreateRestrictedToken");
 GetTokenInformation(restricted,TokenRestrictedSids,IntPtr.Zero,0,out uint needed);
 if(needed<sizeof(uint))throw new Exception("TokenRestrictedSids length invalid");
 info=Marshal.AllocHGlobal((int)needed);
 Ensure(GetTokenInformation(restricted,TokenRestrictedSids,info,needed,out _),"GetTokenInformation(TokenRestrictedSids)");
 uint count=(uint)Marshal.ReadInt32(info);
 if(count!=1)throw new Exception("Expected exactly one restricting SID; observed "+count);
 IntPtr first=IntPtr.Add(info,IntPtr.Size==8?8:4);
 var entry=Marshal.PtrToStructure<SID_AND_ATTRIBUTES>(first);
 var actual=new SecurityIdentifier(entry.Sid).Value;
 if(!string.Equals(actual,sid.Value,StringComparison.OrdinalIgnoreCase))throw new Exception("Restricted SID mismatch");
 Console.WriteLine("RESTRICTING_SID> "+actual);
 Console.WriteLine("TOKEN_RESTRICTED_SIDS> 1");
 Console.WriteLine("RESULT> PASS_TOKEN_CONSTRUCTION_ONLY");
 Console.WriteLine("FILESYSTEM_ISOLATION> UNTESTED");
 Console.WriteLine("NETWORK_ISOLATION> UNTESTED");
 Console.WriteLine("REAL_EXECUTION> DISABLED");
 return 0;
 }catch(Exception e){Console.Error.WriteLine("FAIL_CLOSED> "+e.Message);return 1;}
 finally{if(info!=IntPtr.Zero)Marshal.FreeHGlobal(info);if(restricted!=IntPtr.Zero)CloseHandle(restricted);if(source!=IntPtr.Zero)CloseHandle(source);if(sidEntry!=IntPtr.Zero)Marshal.FreeHGlobal(sidEntry);if(sidBuffer!=IntPtr.Zero)Marshal.FreeHGlobal(sidBuffer);}
 }
}
