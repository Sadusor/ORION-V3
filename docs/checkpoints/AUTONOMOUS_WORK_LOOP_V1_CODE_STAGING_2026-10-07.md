# Autonomous Work Loop V1 — Code Staging Checkpoint

Date: 2026-10-07  
Status: **GITHUB-CODED / NOT GIT-CHECKED / NOT PHYSICALLY QUALIFIED**

## Owner direction

Work in modules where boundaries are real. Combine tiny helpers when splitting them would be over-engineering. Stage as much safe code as practical so the next session can begin with pull + GIT CHECK and then physical qualification.

## What was staged

New isolated package:

`src/orion_v3/work_loop/`

Modules:
- `contracts.py` — Proposal, EvidenceRecord, WorkState, GREEN/YELLOW/RED vocabulary and deterministic proposal hash.
- `paths.py` — fail-closed workspace/path/frozen overlap preflight. This is defense-in-depth, **not OS sandboxing**.
- `policy.py` — deterministic bounded GREEN/YELLOW/RED classification.
- `authorization.py` — exact-proposal expiring HMAC authorization token; RED cannot be authorized.
- `verifier.py` — evidence binding/type/revision checks; GIT CHECK PASS cannot satisfy execution evidence.
- `vault.py` — minimal project Vault (`STATE.md`, append-only `JOURNAL.md`, `repo/`) with no overwrite-on-initialize.
- `engine.py` — pure state-transition seam; no embedded model and no embedded Hand.
- `sandbox_srt.py` — configuration-only adapter for the Anthropic SRT physical spike. It does not install SRT, change ACLs/WFP, or spawn a process.
- `__init__.py` — narrow public exports.

New tests:
- `tests/test_work_loop_contracts.py`
- `tests/test_work_loop_policy.py`
- `tests/test_work_loop_authorization.py`
- `tests/test_work_loop_verifier.py`
- `tests/test_work_loop_vault.py`
- `tests/test_work_loop_engine.py`
- `tests/test_work_loop_sandbox_srt.py`

## Donor code/patterns embodied

- OpenMuse: exact proposal hash, stale/changed action invalidation concept, bounded authorization.
- OpenJarvis: resolved-path allowed-root and protected-path concepts, made fail-closed for ORION.
- CLI-Anything: typed deterministic operation/receipt discipline.
- TheHands: remains intended execution/evidence substrate; **not modified**.
- Anthropic Sandbox Runtime: wrapped only as a config plan pending physical Windows qualification.
- Codex Windows sandbox: smoke-test ideas reserved for physical confinement attack suite.

## Deliberately NOT coded tonight

- no SRT installation;
- no Windows ACL/WFP mutation;
- no autonomous subprocess execution;
- no TheHands core modification;
- no Memory V1/V1.1 modification;
- no Qwen call;
- no Work Chat/UI;
- no Council/Skills framework;
- no replacement STOP;
- no claim that the sandbox works on the ORION PC.

This is intentional. The first dangerous boundary is execution confinement, so it remains physically gated.

## Claim discipline

A GitHub commit means **CODED**, not PASS.

Next evidence types remain distinct:
1. **GIT CHECK PASS** — repository/code gate only.
2. **TEST PASS** — Python qualification tests execute successfully.
3. **SANDBOX PHYSICAL PASS** — Windows confinement attacks execute successfully.
4. **LOOP EXECUTION PASS** — real bounded loop executes through TheHands and authenticated evidence.
5. **AUTONOMOUS WORK LOOP V1 PASS** — only after the full milestone qualification.

Never substitute one for another.

## Next-session order

1. Pull latest ORION-V3 through the normal TheHands/GIT CHECK workflow.
2. Run GIT CHECK once for the staged batch.
3. If GIT CHECK passes, run the new Python test suite physically.
4. Audit exact current TheHands dispatcher/cwd/path/process/evidence seams before writing an adapter.
5. Physically qualify Anthropic SRT in a disposable E: workspace using the attack suite in the donor audit.
6. Only after sandbox PASS, add the smallest TheHands execution adapter.
7. Then run deliberate FAIL -> restart -> repair -> PASS continuity qualification.

## Frozen boundaries

Memory V1/V1.1 remain frozen. Proven TheHands core remains untouched. Existing ORION STOP remains authoritative. This staging does not reopen any frozen component.
