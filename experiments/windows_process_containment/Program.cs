// ORION Windows process-tree containment experiment.
// This is NOT a security sandbox: no restricted token, ACL scope, or network filter.
// Launch is suspended until the Job Object owns the child; fail closed on errors.
// Compile on Windows: dotnet build (see companion project).
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading;

internal static class Program
{
    private const uint CREATE_SUSPENDED = 0x00000004;
    private const uint CREATE_NO_WINDOW = 0x08000000;
    private const uint JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000;
    private const int JobObjectExtendedLimitInformation = 9;
    private const uint WAIT_OBJECT_0 = 0;
    private const uint WAIT_TIMEOUT = 258;
    [StructLayout(LayoutKind.Sequential)] private struct STARTUPINFO
    {
        public uint cb; public string? lpReserved; public string? lpDesktop; public string? lpTitle;
        public uint dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute;
        public uint dwFlags; public ushort wShowWindow, cbReserved2; public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
    }
    [StructLayout(LayoutKind.Sequential)] private struct PROCESS_INFORMATION
    { public IntPtr hProcess, hThread; public uint dwProcessId, dwThreadId; }
    [StructLayout(LayoutKind.Sequential)] private struct IO_COUNTERS
    { public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount, ReadTransferCount, WriteTransferCount, OtherTransferCount; }
    [StructLayout(LayoutKind.Sequential)] private struct JOBOBJECT_BASIC_LIMIT_INFORMATION
    {
        public long PerProcessUserTimeLimit, PerJobUserTimeLimit; public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize, MaximumWorkingSetSize; public uint ActiveProcessLimit;
        public UIntPtr Affinity; public uint PriorityClass, SchedulingClass;
    }
    [StructLayout(LayoutKind.Sequential)] private struct JOBOBJECT_EXTENDED_LIMIT_INFORMATION
    {
        public JOBOBJECT_BASIC_LIMIT_INFORMATION BasicLimitInformation;
        public IO_COUNTERS IoInfo;
        public UIntPtr ProcessMemoryLimit, JobMemoryLimit, PeakProcessMemoryUsed, PeakJobMemoryUsed;
    }
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)]
    private static extern bool CreateProcessW(string? application, System.Text.StringBuilder command, IntPtr processAttrs, IntPtr threadAttrs, bool inherit, uint flags, IntPtr environment, string? cwd, ref STARTUPINFO startup, out PROCESS_INFORMATION process);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern IntPtr CreateJobObjectW(IntPtr attrs, string? name);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool SetInformationJobObject(IntPtr job, int cls, ref JOBOBJECT_EXTENDED_LIMIT_INFORMATION info, uint size);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool TerminateProcess(IntPtr process, uint code);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool TerminateJobObject(IntPtr job, uint code);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern uint WaitForSingleObject(IntPtr handle, uint ms);
    [DllImport("kernel32.dll", SetLastError=true)] private static extern bool CloseHandle(IntPtr handle);
    private static void Check(bool ok, string name) { if (!ok) throw new Win32Exception(Marshal.GetLastWin32Error(), name); }
    private static int Main()
    {
        if (!OperatingSystem.IsWindows()) { Console.Error.WriteLine("Windows only"); return 2; }
        string root = Path.Combine(Path.GetTempPath(), "orion-suspended-probe-" + Guid.NewGuid().ToString("N"));
        Directory.CreateDirectory(root);
        IntPtr job = IntPtr.Zero; PROCESS_INFORMATION child = default;
        try
        {
            string marker = Path.Combine(root, "marker.txt");
            string script = Path.Combine(root, "child.ps1");
            File.WriteAllText(script, "param([string]$Marker)\nSet-Content -LiteralPath $Marker -Value $PID\nStart-Sleep -Seconds 90\n");
            string ps = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.System), "WindowsPowerShell", "v1.0", "powershell.exe");
            if (!File.Exists(ps)) throw new FileNotFoundException("PowerShell unavailable", ps);
            job = CreateJobObjectW(IntPtr.Zero, null);
            if (job == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateJobObjectW");
            var limits = new JOBOBJECT_EXTENDED_LIMIT_INFORMATION();
            limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
            Check(SetInformationJobObject(job, JobObjectExtendedLimitInformation, ref limits, (uint)Marshal.SizeOf<JOBOBJECT_EXTENDED_LIMIT_INFORMATION>()), "SetInformationJobObject");
            var startup = new STARTUPINFO { cb = (uint)Marshal.SizeOf<STARTUPINFO>() };
            var cmd = new System.Text.StringBuilder("\"" + ps + "\" -NoProfile -NonInteractive -File \"" + script + "\" -Marker \"" + marker + "\"");
            Check(CreateProcessW(ps, cmd, IntPtr.Zero, IntPtr.Zero, false, CREATE_SUSPENDED | CREATE_NO_WINDOW, IntPtr.Zero, root, ref startup, out child), "CreateProcessW");
            Check(AssignProcessToJobObject(job, child.hProcess), "AssignProcessToJobObject");
            if (ResumeThread(child.hThread) == 0xFFFFFFFF) throw new Win32Exception(Marshal.GetLastWin32Error(), "ResumeThread");
            var sw = Stopwatch.StartNew();
            while (!File.Exists(marker) && sw.Elapsed < TimeSpan.FromSeconds(15))
            {
                if (WaitForSingleObject(child.hProcess, 0) == WAIT_OBJECT_0) throw new Exception("Child exited before marker");
                Thread.Sleep(100);
            }
            if (!File.Exists(marker)) throw new TimeoutException("Child marker not created");
            Check(TerminateJobObject(job, 1), "TerminateJobObject");
            if (WaitForSingleObject(child.hProcess, 5000) != WAIT_OBJECT_0) throw new TimeoutException("Child survived STOP");
            Console.WriteLine("{\"status\":\"PASS_PROCESS_TERMINATION_ONLY\",\"suspendedLaunch\":true,\"restrictedToken\":false,\"filesystemIsolation\":false,\"networkIsolation\":false,\"realExecutionAuthorized\":false}");
            return 0;
        }
        catch (Exception e) { Console.Error.WriteLine("FAIL_CLOSED: " + e.Message); return 1; }
        finally
        {
            // Terminate suspended or live child before closing any handles.
            if (child.hProcess != IntPtr.Zero) { TerminateProcess(child.hProcess, 1); CloseHandle(child.hProcess); }
            if (child.hThread != IntPtr.Zero) CloseHandle(child.hThread);
            if (job != IntPtr.Zero) CloseHandle(job);
            try { Directory.Delete(root, true); } catch { }
        }
    }
}
