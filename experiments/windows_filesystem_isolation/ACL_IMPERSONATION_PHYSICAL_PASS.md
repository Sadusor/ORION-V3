# Physical ACL impersonation qualification — 2026-10-08

Evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/c5d73bf8fea2.json

Source GitCheck: ae8401ec9c36b3eb94b6e928cfb424c9bdbb5995
Result: PASS, disposable fixture, .NET 8 build 0 warnings/errors.

- Inside read TRUE; inside write TRUE.
- Outside read FALSE (UnauthorizedAccessException).
- Outside write FALSE (UnauthorizedAccessException).
- Outside file unchanged TRUE.

Scope: WindowsIdentity.RunImpersonated under CreateRestrictedToken with RestrictedCode SID (S-1-5-12), with explicit ACL grant on the inside fixture. This demonstrates an OS-enforced dual access check for these file operations only.

Not proven: separately launched child/grandchild, directory traversal/junction, process bootstrap under restricting SID, network egress, cross-process STOP/commit ordering. Real ORION execution remains DISABLED.

Next qualification: use the existing suspended-launch + Job Object infrastructure to run the exact same allowed/denied file probes in a separate child. If system DLL/bootstrap access fails, report BOOTSTRAP_BLOCKED and investigate without broadening host ACLs.
