# ORION V3 — 2026-10-08 Isolation Gate Handoff

Status: GITHUB DOCUMENTED / PHYSICAL ISOLATION NOT TESTED
Reported physical evidence (owner): TheHands session 38412799d65a, ORION 55be8d8, GitCheck e1f707b; 137 passed, 3 skipped, 0 failed. Dry-run; real execution disabled. This report must be reconciled against the published TheHands results branch before labeling independently verified.

## Current boundaries
- Read observation, Vault transactions/recovery, V2 identity, STOP coordination/source injection, Work Loop/Vault coordination, authorization mutation/expiry: reported regression coverage.
- NOT PROVEN: live ORION STOP-service connection; cross-process STOP/commit ordering; Windows OS filesystem/network containment; real execution.
- TheHands product remains frozen. TheHands targeted STOP is not ORION's canonical STOP.

## Isolation donor disposition
- Anthropic sandbox-runtime: previously documented source-file audit, Windows alpha; candidate for physical falsification, not adopted.
- Codex windows-sandbox-rs: documented smoke-test cases and token/ACL implementation leads; runtime unqualified.
- DeepSeek Harness Windows ACL: prior physical partial write-boundary result; no read/network isolation.
- OpenJarvis mount_security.py: documented path allowlist implementation; NOT OS isolation; default-empty roots caveat.
- agent-win-sandbox: reference only, not hard confinement.
These dispositions are based on existing donor audit docs; no new external donor checkout or code-level Windows implementation review is claimed in this checkpoint.

## Next bounded implementation
1. Read current ORION STOP coordinator/source adapter, Vault commit guard, work-loop tests and TheHands GitCheck hand manifest. Identify the actual existing ORION STOP-service API; do not add a second STOP owner.
2. Add a separate Windows isolation probe adapter, initially non-executing. It accepts only a disposable E: workspace and emits an immutable probe manifest. No arbitrary command execution.
3. Physical Windows gate: under candidate OS sandbox identity prove inside-write allowed, outside-create/overwrite/delete denied, junction/reparse escapes denied, child processes confined, outbound network denied, and STOP interrupts the process tree before commit. Use only synthetic files and harmless test destinations.
4. Cross-process gate: arrange STOP request during a held commit boundary; verify no commit after authoritative STOP, including restart/recovery. No auto-replay.
5. Record source SHA, sandbox backend/revision, OS build, identity, policy, process tree, every probe result, timestamps and evidence pack hash.
6. Batch new adapter tests + existing regressions into ONE GitCheck. Keep real execution disabled even after probe until owner-reviewed proof.

## Fail closed
If the authoritative STOP service cannot be reached or the sandbox cannot prove OS denials, return BLOCKED; never fall back to ordinary PowerShell execution. Job Objects alone are insufficient. ACL-only write restriction is insufficient for read/network containment. STOP cannot undo effects already committed.

## Documentation reconciliation
docs/STATUS.md remains historical and docs/ROADMAP.md still describes the earlier 57-pass stage. This handoff is a non-destructive supplemental record; update canonical files after confirming the source/evidence and code seam.
