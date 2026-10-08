# Combined Windows qualification — acceptance contract

Status: NOT RUN. Production execution DISABLED.

Prior physical evidence: profile lifecycle d271141f4509; child launch d036d15f7af0; basic filesystem allow/deny 170ac85ebbdc.

One GitCheck, only when all checks implemented:
1. Approved workspace write: child creates nonce file; host compares exact bytes.
2. Protected read/write: capture OS error codes and verify outside files unchanged.
3. Network: live IPv4 listener, host control connection succeeds, child Winsock connection denied with recorded WSA error. Connection refused or DNS failure is INCONCLUSIVE.
4. Descendant STOP: spawn three disposable children, record PIDs, verify job membership, close final Job Object handle, confirm all exited.
5. STOP vs commit: exercise existing ORION vault guard with simulated receipt. STOP must reject commit and leave canonical state unchanged. No duplicate guard.
6. Crash vs commit: interrupt after artifact write and before verification; mark INTERRUPTED, no PASS, no auto-retry or canonical mutation.
7. Cleanup: remove temporary fixtures and profile, fail on cleanup error.
8. Machine-readable evidence: source commit, per-check observations, OS codes, PIDs and timeouts. Overall PASS requires all P0 checks.

No elevation, permanent firewall rules, Windows DLL ACL edits, production Hands execution, or changes to Remote V1. Do not claim full qualification from the existing three partial passes.

Herald overview experiment is opt-in and read-only; not connected to UI or canonical memory.
