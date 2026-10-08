# Windows isolation donor decision — 2026-10-08

Status: EXPERIMENT / FAIL CLOSED. Real ORION Work Hand execution disabled. TheHands product frozen.

## Evidence
- SRT v0.0.79 official windows-install completed (dedicated sandbox account, 4 WFP filters).
- TheHands confinement session eac5face9d24 FAIL: WFP verification fails before child launch with CreateProcessWithLogonW(srt-sandbox) access denied (0x80070005).
- TheHands session 304ff4807efb PASS for managed token inspection; absence of S-1-5-5 in enumerated groups is NOT proof of native logon-token deficiency.
- TheHands session 99efd275a802 PASS for filtered whoami inspection; filtered output inconclusive.
- Owner reproduced identical SRT WFP verify error in ordinary interactive PowerShell. This rules out a TheHands-only failure, not the exact Windows account-rights cause.
- DeepSeek review recommends restricted token + Job Object with filesystem ACLs and network enforcement; recommendation is a hypothesis until physical proof.

## Source-grounded donor notes
- Codex `codex-rs/windows-sandbox-rs/src/unified_exec/backends/legacy.rs`: explicitly rejects additional deny-read paths in legacy restricted-token mode. Cannot treat this backend as a complete ORION read-denial substrate.
- Codex `codex-rs/windows-sandbox-rs/src/bin/command_runner/win.rs`: has dedicated command-runner and Job Object patterns.
- Codex `codex-rs/windows-sandbox-rs/src/token.rs`: token group and logon SID helpers.
- nanosandbox (Erio-Harrison/nanosandbox): candidate restricted-token / Job Object reference; verify source, license and guarantees before reuse.
- OpenHands/OpenJarvis/cua: useful execution-tool donors, not accepted Windows OS containment without evidence.

## Chosen modular sequence
1. PROCESS CONTAINMENT: isolated experimental launcher with restricted token and Job Object; disposable fixture only, no production integration. Verify kill-on-close and descendants; no privilege increase.
2. FILESYSTEM: kernel-enforced allowed read/write workspace and denied outside read/write; test reparse points, rename and children; no ACL edits to product repos.
3. NETWORK: enforce outbound denial for all descendants, not only proxy-level policy. Test local controlled listener and direct sockets.
4. STOP / COMMIT: connect existing ORION authority to cross-process STOP; deny post-STOP commit.
5. FULL PHYSICAL GATE: latency/CPU/RAM, rollback, cleanup, and evidence. Only then consider freeze/merge.

**Security note:** restricted token + Job Object alone are NOT a sandbox and MUST NOT enable real Work Hand execution. No stage may claim confinement until outside-read/write and egress denial are independently verified.

## Safety
No changes to TheHands product, Windows account rights, WFP, service settings or ORION canonical memory. No privileged repair without separate approval. Preserve owner stash. Keep module replaceable.