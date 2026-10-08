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


## Verified STOP/Vault evidence — 2026-10-08

GitCheck session `e3296ce50195`, TheHands source `32e5930`: six real-Vault experimental tests passed, including 12 concurrent cross-process trials (10 rejected, 2 committed before STOP). Controlled parent STOP then child commit rejected; commit-first and STOP-first tests passed; one injected pending-write interruption recovered without duplicate journal entries. Experimental prototype commit `e1730d7` uses the existing Vault SQLite lock and a separate monotonic STOP_AUTHORITY SQLite file.

**Scope limitation:** these tests do not establish AppContainer filesystem/network isolation, Job Object descendant termination, production STOP integration, or comprehensive crash safety. The 8-point combined Windows acceptance contract above remains NOT RUN. No production execution authorization is implied.

## Fail-closed authority qualification — 2026-10-08

TheHands GitCheck session `03bb1e6561a0`, source `7093975`: 9/9 experimental STOP/Vault tests PASS. Includes missing STOP authority, corrupt SQLite STOP authority, monotonic STOP persistence, real Vault STOP guard, cross-process parent STOP/child commit, 12 concurrent STOP/commit iterations (10 rejected; 2 committed before STOP), and pending transaction recovery. This validates the tested prototype behaviors only; AppContainer and full eight-check combined qualification remain NOT RUN. Production execution remains DISABLED.

## Physical evidence 2026-10-08 — session af7a5f6970d7

FILESYSTEM PASS: approved workspace read/write allowed, outside read/write denied, outside fixture unchanged, disposable AppContainer profile cleanup succeeded. NETWORK INCONCLUSIVE: live host listener reachable by host, AppContainer native Winsock child timed out (`NETWORK_ISOLATION> INCONCLUSIVE_TIMEOUT`, child exit 12). A timeout is NOT a network-denial PASS. Do not relax acceptance criterion or enable execution. Investigate native socket error reporting and Windows filtering diagnostics in a dedicated diagnostic module before re-running combined gate. Remote V1 unchanged.
