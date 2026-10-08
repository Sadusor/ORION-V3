Restricted child loader diagnosis — 2026-10-08

Evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/d6a8de102ced.json

The .NET launcher compiled cleanly. Native executable read under the restricted token: ALLOW. kernel32.dll, kernelbase.dll, ntdll.dll reads under the same restricted token: DENY (UnauthorizedAccessException 0x80070005). Child exit: 0xC0000142.

Conclusion: the current S-1-5-12 restricted SID configuration is incompatible with observed Windows DLL access. Do not grant S-1-5-12 on system DLLs. Child isolation remains BLOCKED; network, descendants, junctions and cross-process STOP untested. Real execution disabled.

Next: evaluate an OS-supported isolation identity or AppContainer with explicit capability and workspace ACLs, in an independent disposable experiment; preserve existing Job Object and authority boundary.
