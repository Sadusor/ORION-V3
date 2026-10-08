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
 static int Main(string[] args) {
  if(!OperatingSystem.IsWindows()||args.Length!=1||!int.TryParse(args[0],out int port)||port<1||port>65535)return 4;
  IntPtr data=Marshal.AllocHGlobal(512);IntPtr sock=new IntPtr(-1);
  try {
   int startup=WSAStartup(0x202,data);
   Console.WriteLine("WSA_STARTUP> "+startup);
   if(startup!=0)return 5;
   sock=socket(2,1,6);
   if(sock==new IntPtr(-1)){Console.WriteLine("SOCKET_ERROR> "+WSAGetLastError());return 6;}
   byte[] address={16,0,(byte)(port>>8),(byte)port,127,0,0,1,0,0,0,0,0,0,0,0};
   int result=connect(sock,address,address.Length);
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
