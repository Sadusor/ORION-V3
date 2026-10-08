// Experimental Windows restricted-SID filesystem check, disposable files only.
// This probe deliberately uses managed WindowsIdentity.RunImpersonated to exercise OS ACL checks
// with a restricted token. It is not a child-process escape or complete sandbox proof.
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.AccessControl;
using System.Security.Principal;
internal static class Program {
 const uint ACCESS=0x18B, DISABLE_MAX_PRIVILEGE=1;
 [StructLayout(LayoutKind.Sequential)] struct SID_AND_ATTRIBUTES { public IntPtr Sid; public uint Attributes; }
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool OpenProcessToken(IntPtr p,uint a,out IntPtr t);
 [DllImport("advapi32.dll",SetLastError=true)] static extern bool CreateRestrictedToken(IntPtr t,uint flags,uint d,IntPtr ds,uint del,IntPtr deleted,uint n,IntPtr sids,out IntPtr output);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool CloseHandle(IntPtr h);
 static void Require(bool ok,string step) {if(!ok)throw new Win32Exception(Marshal.GetLastWin32Error(),step);}
 static int Main() {
 if(!OperatingSystem.IsWindows())return 2;
 string root=Path.Combine(Path.GetTempPath(),"orion-fs-sid-"+Guid.NewGuid().ToString("N"));
 IntPtr source=IntPtr.Zero,token=IntPtr.Zero,sidPtr=IntPtr.Zero,entryPtr=IntPtr.Zero;
 try {
 string inside=Path.Combine(root,"inside"),outside=Path.Combine(root,"outside");
 Directory.CreateDirectory(inside);Directory.CreateDirectory(outside);
 string permitted=Path.Combine(inside,"permitted.txt"),forbidden=Path.Combine(outside,"forbidden.txt");
 string nonce=Guid.NewGuid().ToString("N");
 File.WriteAllText(permitted,nonce);File.WriteAllText(forbidden,nonce);
 var restrictingSid=new SecurityIdentifier(WellKnownSidType.RestrictedCodeSid,null);
 var sidBytes=new byte[restrictingSid.BinaryLength];restrictingSid.GetBinaryForm(sidBytes,0);
 sidPtr=Marshal.AllocHGlobal(sidBytes.Length);Marshal.Copy(sidBytes,0,sidPtr,sidBytes.Length);
 entryPtr=Marshal.AllocHGlobal(Marshal.SizeOf<SID_AND_ATTRIBUTES>());
 Marshal.StructureToPtr(new SID_AND_ATTRIBUTES{Sid=sidPtr,Attributes=0},entryPtr,false);
 // Only the fresh fixture gets an ACL change. No parent directory or user profile changes.
 var acl=new FileInfo(permitted).GetAccessControl();
 acl.AddAccessRule(new FileSystemAccessRule(restrictingSid,FileSystemRights.Read|FileSystemRights.Write,AccessControlType.Allow));
 new FileInfo(permitted).SetAccessControl(acl);
 Require(OpenProcessToken(Process.GetCurrentProcess().Handle,ACCESS,out source),"OpenProcessToken");
 Require(CreateRestrictedToken(source,DISABLE_MAX_PRIVILEGE,0,IntPtr.Zero,0,IntPtr.Zero,1,entryPtr,out token),"CreateRestrictedToken");
 bool insideRead=false,insideWrite=false,outsideRead=false,outsideWrite=false;
 using(var identity=new WindowsIdentity(token)){
 WindowsIdentity.RunImpersonated(identity.AccessToken,()=>{
 try{insideRead=File.ReadAllText(permitted)==nonce;}catch(Exception e){Console.WriteLine("INSIDE_READ_ERROR> "+e.GetType().Name);}
 try{File.AppendAllText(permitted,"x");insideWrite=true;}catch(Exception e){Console.WriteLine("INSIDE_WRITE_ERROR> "+e.GetType().Name);}
 try{outsideRead=File.ReadAllText(forbidden)==nonce;}catch(Exception e){Console.WriteLine("OUTSIDE_READ_DENIED> "+e.GetType().Name);}
 try{File.AppendAllText(forbidden,"x");outsideWrite=true;}catch(Exception e){Console.WriteLine("OUTSIDE_WRITE_DENIED> "+e.GetType().Name);}
 });
 }
 bool outsideUnchanged=File.ReadAllText(forbidden)==nonce;
 Console.WriteLine($"INSIDE_READ> {insideRead}; INSIDE_WRITE> {insideWrite}; OUTSIDE_READ> {outsideRead}; OUTSIDE_WRITE> {outsideWrite}; OUTSIDE_UNCHANGED> {outsideUnchanged}");
 bool pass=insideRead&&insideWrite&&!outsideRead&&!outsideWrite&&outsideUnchanged;
 Console.WriteLine(pass?"RESULT> PASS_DISPOSABLE_ACL_IMPERSONATION_ONLY":"RESULT> FAIL_FILESYSTEM_BOUNDARY");
 Console.WriteLine("CHILD_PROCESS_ISOLATION> UNTESTED\nNETWORK_ISOLATION> UNTESTED\nREAL_EXECUTION> DISABLED");
 return pass?0:1;
 }catch(Exception e){Console.Error.WriteLine("BLOCKED> "+e);return 2;}
 finally {
 if(token!=IntPtr.Zero)CloseHandle(token);if(source!=IntPtr.Zero)CloseHandle(source);
 if(entryPtr!=IntPtr.Zero)Marshal.FreeHGlobal(entryPtr);if(sidPtr!=IntPtr.Zero)Marshal.FreeHGlobal(sidPtr);
 try{Directory.Delete(root,true);}catch{}
 }
 }
}
