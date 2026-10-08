// Native Winsock connection probe; launched only as an AppContainer child by the existing isolated harness.
// No HTTP, DNS, shell, file writes or ORION execution. Exit 0 only for WSAEACCES (10013).
using System;
using System.Net;
using System.Net.Sockets;
using System.Runtime.InteropServices;
internal static class Program {
 [DllImport("ws2_32.dll",SetLastError=true)] static extern int WSAStartup(ushort version, IntPtr data);
 [DllImport("ws2_32.dll",SetLastError=true)] static extern int WSACleanup();
 [DllImport("ws2_32.dll",SetLastError=true)] static extern IntPtr socket(int af,int type,int protocol);
 [DllImport("ws2_32.dll",SetLastError=true)] static extern int connect(IntPtr s, byte[] address,int length);
 [DllImport("ws2_32.dll",SetLastError=true)] static extern int closesocket(IntPtr s);
 [DllImport("ws2_32.dll")] static extern int WSAGetLastError();
 [DllImport("ws2_32.dll")] static extern int ioctlsocket(IntPtr s,int cmd,ref uint argp);
 [DllImport("ws2_32.dll")] static extern int select(int nfds,IntPtr readfds,IntPtr writefds,IntPtr exceptfds,IntPtr timeout);
 [DllImport("ws2_32.dll")] static extern int getsockopt(IntPtr s,int level,int optname,out int optval,ref int optlen);
 static int Main(string[] args) {
  if(!OperatingSystem.IsWindows()||args.Length!=1||!int.TryParse(args[0],out int port)||port<1||port>65535)return 4;
  IntPtr data=Marshal.AllocHGlobal(512);IntPtr sock=new IntPtr(-1);
  try {
   int startup=WSAStartup(0x202,data);
   Console.WriteLine("WSA_STARTUP> "+startup);
   if(startup!=0)return 5;
   sock=socket(2,1,6);
   if(sock==new IntPtr(-1)){Console.WriteLine("SOCKET_ERROR> "+WSAGetLastError());return 6;}
   byte[] address={2,0,(byte)(port>>8),(byte)port,127,0,0,1,0,0,0,0,0,0,0,0};
   uint nonblocking=1;
   if(ioctlsocket(sock,unchecked((int)0x8004667e),ref nonblocking)!=0){Console.WriteLine("NONBLOCKING_SETUP_ERROR> "+WSAGetLastError());return 7;}
   int result=connect(sock,address,address.Length);
   if(result!=0 && WSAGetLastError()==10035){
    IntPtr writeSet=Marshal.AllocHGlobal(16),errorSet=Marshal.AllocHGlobal(16),deadline=Marshal.AllocHGlobal(8);
    try{
     Marshal.WriteInt32(writeSet,1);Marshal.WriteIntPtr(writeSet,8,sock);
     Marshal.WriteInt32(errorSet,1);Marshal.WriteIntPtr(errorSet,8,sock);
     Marshal.WriteInt32(deadline,0);Marshal.WriteInt32(deadline,4,1500000);
     int ready=select(0,IntPtr.Zero,writeSet,errorSet,deadline);
     if(ready==0){Console.WriteLine("NETWORK_ISOLATION> INCONCLUSIVE_TIMEOUT");return 12;}
     if(ready<0){Console.WriteLine("SELECT_ERROR> "+WSAGetLastError());return 13;}
     int length=4;
     if(getsockopt(sock,0xffff,0x1007,out int soError,ref length)!=0){Console.WriteLine("SO_ERROR_QUERY_FAILED> "+WSAGetLastError());return 14;}
     Console.WriteLine("SO_ERROR> "+soError);
     if(soError==0){Console.WriteLine("NETWORK_ISOLATION> FAIL_CONNECTED");return 10;}
     if(soError==10013){Console.WriteLine("NETWORK_ISOLATION> PASS_ACCESS_DENIED");return 0;}
     Console.WriteLine("NETWORK_ISOLATION> INCONCLUSIVE_SOCKET_ERROR_"+soError);return 11;
    }finally{Marshal.FreeHGlobal(writeSet);Marshal.FreeHGlobal(errorSet);Marshal.FreeHGlobal(deadline);}
   }
   int error=result==0?0:WSAGetLastError();
   Console.WriteLine("CONNECT_RESULT> "+result);
   Console.WriteLine("WSA_CONNECT_ERROR> "+error);
   if(result==0){Console.WriteLine("NETWORK_ISOLATION> FAIL_CONNECTED");return 10;}
   if(error==10013){Console.WriteLine("NETWORK_ISOLATION> PASS_ACCESS_DENIED");return 0;}
   Console.WriteLine("NETWORK_ISOLATION> INCONCLUSIVE");return 11;
  } finally {
   if(sock!=new IntPtr(-1))closesocket(sock);
   WSACleanup();Marshal.FreeHGlobal(data);
  }
 }
}
