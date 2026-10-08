# Windows isolation physical qualification — 2026-10-08

Status: EXPERIMENT / NOT TESTED PHYSICALLY. Branch: `spike/windows-isolation-preflight-20261008`. No merge or real Work Hand execution authorized.

## Baseline evidence and test status
Owner's Windows run on experimental branch before test-only corrections: **163 passed, 3 failed, 3 skipped**. Seven preflight cases passed. The three failures were legacy expectations in authorization/policy tests; test-only corrections committed at `ee41cbb3`. Full retest after this commit is **PENDING**, not PASS. Local `tests/test_work_loop_nonce_replay.py` changes were preserved by the owner in a named stash; do not drop/apply automatically. Real execution DISABLED.

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
