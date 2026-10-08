# Windows isolation physical qualification — 2026-10-08

Status: EXPERIMENT / NOT TESTED PHYSICALLY. Branch: `spike/windows-isolation-preflight-20261008`. No merge or real Work Hand execution authorized.

## Baseline evidence and test status
Owner's Windows run on experimental branch before test-only corrections: **163 passed, 3 failed, 3 skipped**. Seven preflight cases passed. The three failures were legacy expectations in authorization/policy tests; test-only corrections committed at `ee41cbb3`. Full retest after this commit is **VERIFIED PASS** (details below). Local `tests/test_work_loop_nonce_replay.py` changes were preserved by the owner in a named stash; do not drop/apply automatically. Real execution DISABLED.

## Source review (actual upstream files, current GitHub contents; revisions are blob SHAs, not full pinned repo commits)
- Anthropic SRT: `anthropics/sandbox-runtime/src/sandbox/sandbox-config.ts`, blob `968c82d754f48bc7a6d6dc27f6a628240658b171`. Observed strict config schema for filesystem entries, domain/network rules, and absolute external binary paths. **Config schema alone is not OS enforcement**. Inspect native Windows ACL/WFP implementation, installation privileges, process token, cleanup and STOP before trial.
- Codex: `openai/codex/codex-rs/windows-sandbox-rs/sandbox_smoketests.py`, blob `a1553e5e54ed8772845dbf3e9e9dd6e8339d2993`. Observed a real subprocess smoke harness, with workspace/outside roots, junction and symlink helpers, read-only/workspace-write modes, and local proxy fixtures. Borrow test semantics, not Codex authority or its runtime unqualified.
- ORION existing `src/orion_v3/work_loop/sandbox_srt.py` is **configuration-only**; it does not spawn a sandbox. `windows_isolation_preflight.py` always refuses execution. Neither is proof of Windows confinement.

## Physical gate, in order
1. Verify latest experiment SHA and run `$env:PYTHONPATH=(Join-Path (Get-Location) 'src'); python -m pytest -q` on Windows. Record exact commit and pass/fail/skip evidence.
2. **Read-only inspection first:** identify whether SRT Windows native enforcement is available on the machine, exact binary/version, required privilege/account, installation changes, service/STOP seam, and rollback. No installer or privileged policy mutation automatically.
3. Owner approves a disposable `E:\\` fixture **outside** both TheHands and ORION repos. Create dedicated inside/outside sentinel files, never use real private data or host system paths as attack targets. Capture before/after hashes.
4. Under the actual sandboxed child identity, attempt allowed write inside fixture and denied create/overwrite/delete outside fixture; test absolute/relative escapes, junction/reparse, rename/move, and spawned cmd/PowerShell/Python child. Independently inspect actual filesystem after each attempt. Denied error alone is insufficient.
5. Deny network with a local controlled listener/fixture and verify no connection reaches it. Later explicitly allow only one controlled endpoint; verify no broader egress. Do not treat proxy denial alone as full socket denial.
6. Establish existing ORION STOP source's **real service connection** and cross-process ordering before any Work Loop commit. Prove STOP during child run terminates owned process tree and prevents post-STOP canonical commit. In-process `threading.RLock` is not a cross-process guarantee.
7. Confirm sandbox cleanup, no persistent unintended ACL/WFP grants, no leaked child processes, no canonical Vault mutation, and no TheHands changes. Record version, exact command, result, artifacts, limitations, and owner physical PASS/FAIL.

## Go/no-go
Any unknown isolation mechanism, elevated bypass, failed outside denial, child escape, unproven STOP, or incomplete cleanup => BLOCKED; no Work Hand real execution, no merge. No more synthetic gates unless a physical failure reveals a specific missing contract. Do not modify frozen TheHands. No automatic GitHub Actions without owner approval.

## Physical regression result — VERIFIED 2026-10-08

TheHands published session `c8bbdb2b27f6` on `thehands-results`:
- TheHands source commit `3ac78f9bea0e1bf2ffd9d6b67088a9eac7a13ba7`, Hand tree `2d0c0d6203ddff0b39b2c5c05613101b474646d9`.
- ORION experiment source commit `87abe3ad455ffd97fc4eb7031192d7ed141fc6b6`, detached temporary worktree.
- **166 passed, 3 skipped, 0 failed, 2.62 seconds**.
- Output explicitly confirms `REAL_EXECUTION> DISABLED`, `ORION_MAIN> UNCHANGED`, `THEHANDS_PRODUCT> UNCHANGED`.
- Evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/c8bbdb2b27f6.json

This qualifies the Python regression/preflight behavior **only**, not Windows OS isolation, cross-process STOP or real execution. Do not merge experiment until independent sandbox review and physical proof. Next: inspect Windows SRT native enforcement and deployment/cleanup, then plan owner-approved disposable fixture tests.

## SRT native Windows implementation inspection — 2026-10-08

Source files directly inspected (GitHub upstream blobs):
- `anthropics/sandbox-runtime/README.md` `bd044f68f9240c8c27de1fed4b35eaa5aea411d7`: Windows alpha; dedicated `srt-sandbox` local account; machine-wide WFP fence keyed to sandbox SID; `windows-install` requires elevation; process launch uses `CreateProcessWithLogonW` and a restricted token. Installation is an owner-authorized system change, not an automatic development step.
- `src/sandbox/windows-sandbox-utils.ts` `fe9d63c3ca887cbcca1fc9e0017f4d6ebcfeabbc`: dependency/user/WFP probes, ACL stamp/restore/grant/revoke, sandboxed command wrapper; partial ACL stamp failure explicitly requires restore.
- `src/sandbox/sandbox-manager.ts` `a35d7285626de6aa1d424730812c0bc5bffddc59`: records stamped access set and sandbox SID for reset; WFP verification once per process. Session reset does NOT remove machine-wide WFP fence. Examine crash and interrupted cleanup physically.
- `src/sandbox/sandbox-config.ts` `968c82d754f48bc7a6d6dc27f6a628240658b171`: strict filesystem/network configuration schema.

Next bounded action: **read-only host capability inventory through existing TheHands GitCheck** (OS version, Windows edition, Node/npm, SRT helper presence, relevant non-secret account/service/WFP status), without installing SRT or changing ACLs/WFP. No real sandboxed Work Hand yet. Before staging, ensure commands do not expose private account names, credential material or host paths unnecessarily in published evidence. Owner must explicitly approve any elevated install or security-policy change. This remains a Windows alpha candidate, not a qualified sandbox.
