# Engineering collaboration loop — Step 1 source audit and reuse map

Date: 2026-10-08
Status: **IN PROGRESS — DOCUMENT/INTERFACE AUDIT, NOT FULL FILE-BY-FILE CERTIFICATION**
Inventory: `docs/audits/2026-10-08-tracked-file-inventory.md` (366 ORION V3 tracked blobs, tree not truncated, pinned commit `cc1d4a5`). Separate TheHands `main` tree: 88 tracked blobs, not truncated.

## Correct owner intent

**CURRENT:** reproduce and physically prove the existing owner → ChatGPT architect/coder → DeepSeek independent critic → GitHub staging → TheHands GitCheck → owner approval → Windows execution → evidence → PASS/fix/retest → GitHub continuity loop, as an isolated ORION V3 subsystem. **AFTER PROOF:** connect to existing ORION authority, Vault, Memory and PC/Android UI. This is different from the already-staged autonomous Qwen→Hand Work Loop. See Decision 0018.

## Grounded source map

| Concern | Exact existing sources | Status for collaboration loop | Reuse decision |
|---|---|---|---|
| Operator engineering protocol | `AI_OPERATOR_BRIEF.md`, `docs/ENGINEERING_FREEZE_RULE.md`, `docs/decisions/0017-freeze-rule-module-first.md` | EXISTS as written workflow | Keep; clarify loop ownership in Decision 0018 |
| Human + cloud model collaboration | ChatGPT and DeepSeek are currently external participants; `docs/FUNCTION_INVENTORY_UI_WIRING_2026-10-05.md` lists reviewer/provider concepts | PARTIAL/manual; no proven autonomous ChatGPT/DeepSeek adapter in ORION V3 | First encode review request/response and approval/evidence handoff as data, not a new model framework |
| Git staging + physical operator transport | Separate `Sadusor/TheHands-` `docs/ARCHITECTURE.md`, `hands/powershell-1/command.ps1` | EXISTS physically; exact Git SHA/tree check and owner approval | Reuse unchanged; never import TheHands internals into ORION |
| Evidence retrieval | TheHands `thehands-results` session index + per-session result JSON, exact source commit, output tail | EXISTS physically | Build read-only evidence importer/normalizer in V3; reject stale/mismatched task and source |
| Review and owner decision persistence | Current conversation and GitHub documents, no qualified single typed review handoff contract established | PARTIAL | Proposed small V3 `engineering_loop` contract/checkpoint module, only after reviewing existing project-state primitives |
| ORION project continuity | `src/orion_v3/work_loop/vault.py`, `vault_transaction.py`, `engine.py` | EXISTS for later autonomous Work Loop; integration NOT qualified | Reuse through adapter after collaboration loop proof; don't create another canonical Vault |
| ORION Work Hand | `src/orion_v3/work_loop/executor.py`, `coordinator.py`, `simulated_hand.py` | EXISTS contract, simulated execution only | **Not current target**; do not implement Windows real writer first |
| ORION local models | `src/orion_v3/modules/local_brain.py`, `streaming_local_brain.py`, `brain_pipeline.py` | EXISTS local Qwen text pipeline | Optional later provider slot; not ChatGPT/DeepSeek automation proof |
| Canonical Memory | `src/orion_v3/modules/memory_*.py`, `canonical_memory_*.py` | EXISTS modules, physical evidence documented | Freeze; no second memory |
| Product UI | `src/orion_v3/product_server.py`, `ui/strata/`, `android/.../OrionPcBridge.kt`, `desktop/ORION.UI/` | EXISTS product shell; not engineering-loop integrated | Later, only truthful adapter routes |
| STOP/authorization | `src/orion_v3/work_loop/stop.py`, `authorization.py`, TheHands exact checked tree and STOP | EXISTS but distinct domains | No new STOP; preserve explicit owner gesture for engineering GitCheck |
| Windows sandbox experiments | `experiments/windows_appcontainer/`, `experiments/windows_isolation/` | PARTIAL physical confinement, network not universally qualified | Preserve as deferred work; no broad security PASS |

## Source findings that prevent incorrect implementation

- `WorkLoopCoordinator` constructs `SimulatedWorkHand` and returns dry-run evidence; it is **not** a proven real engineering executor.
- `TheHands` itself is a complete, independent remote application with its own owner approval and exact-SHA execution. It has **no model/reviewer agent code**. We must not rebuild it or treat it as ORION authority.
- TheHands Manual PowerShell scratchpad differs from GitCheck: owner paste+run, **no Git SHA/tree approval or GitHub publication**. Do not silently substitute this for the required auditable GitCheck path.
- `docs/STATUS.md` previously began with 2026-10-05 priority while later roadmap changed priorities. Owner clarification is now prepended to STATUS/ROADMAP/OPERATOR BRIEF.
- TheHands architecture documents `GIT CHECK` as fetch and exact checked tree resolution with **no execution**; `APPROVE & START` binds to checked source/tree and starts detached worktree. Preserve that distinction.
- A GitCheck `PASS` must be evaluated against **which script ran and what it proved**; not equivalent to complete product acceptance.
- Earlier app-container/WFP diagnostics cannot establish universal network isolation.

## Step 1 outstanding work (do not mark PASS)

1. Read and reconcile all remaining Markdown/reference/evidence/checkpoint documents, not only headings.
2. Inspect **every** ORION V3 tracked text source/test/config file, with binary assets catalogued separately. Confirm exact code paths and integration signatures.
3. Read remaining TheHands source/test/config and results documentation sufficiently to pin the evidence schema and check approval identity.
4. Publish precise integration contract and one bounded implementation diff. No new real execution or frozen module edits before this.

## Proposed first module after audit

An isolated `src/orion_v3/engineering_loop/` **read-only evidence + checkpoint adapter**, not a new Hand or agent. Inputs: approved task identity, expected exact Git source/Hand tree, reviewer decision and observed TheHands result. Outputs: a truthful normalized cycle record and next action (PASS→freeze or FAIL→repair), without changing TheHands or granting execution. Verify against real session `088f1873516b` plus a known FAIL result. Owner approval remains in TheHands until explicitly integrated.

This is a **design recommendation pending exact source and schema audit**, not implemented code or qualified behavior.

## Repository-wide text review completed — 2026-10-08

At pinned ORION V3 tree `38a41ba68690b9834540abba699ed922d6466cec`, fetched and reviewed the **full returned blob contents** of all **321 files** matching source/document/config extensions (`.md .py .ps1 .json .js .kt .cs .xml .yml .yaml .toml .html .css .kts`). This included **all Markdown documents**, Android, desktop, product server, memory modules/tests, Work Loop, Windows experiments, UI, scripts and tests. Separately fetched/reviewed **73** TheHands source/document/config files from its `main` tree (88 total tracked blobs). Remaining binary assets and uncommon extensions were inventoried, not interpreted as executable text. These are source-content inspections, **not runtime test execution or proof of correctness**.

### Precise TheHands code and evidence contract (verified from source)

- `server/thehands_server.py:541` `HandsRuntime.git_check(hand_id)` records `source_commit`, `tree_sha`, `checked_at`, label and working directory. **No execution**.
- `server/thehands_server.py:574` `approve_and_run` re-fetches and checks the current Hand tree, then calls `approve` and `run`. `run` (line 596) verifies the approved Hand tree and starts a detached Git worktree.
- `server/session_supervisor.py:71` `start_powershell_file` starts the approved PowerShell file. `stop` (line 183) targets its session.
- `server/thehands_server.py:679` `_finalize` maps completed exit 0 to `PASS`, stopped to `STOPPED`, otherwise `FAIL`. **This is a process exit verdict, not a claim that the intended ORION feature was independently qualified.**
- `_publish_evidence` (line 772) writes `thehands.github-evidence.v1` to `thehands-results:docs/thehands/session-results/<session_id>.json`, plus `thehands.session-index.v1` at `docs/thehands/session-index.json`. Index fields: `session_id, hand_id, result, source_commit, hand_tree_sha, recorded_at`. Detail includes `evidence_id, source_system, hand_id, result, source_commit, hand_tree_sha, started_at, finished_at, recorded_at, working_directory, output_tail, provenance`.
- **Important identity distinction:** `source_commit` in TheHands evidence is **TheHands GitCheck repository revision**, not necessarily the **ORION V3 revision tested by the PowerShell script**. For ORION module acceptance, the script must also emit a verifiable ORION revision/test target and assertions, or the engineering-loop adapter must mark the ORION target identity **UNVERIFIED**.
- TheHands `Manual PowerShell` uses owner paste/run and lacks the checked source/tree and GitHub evidence semantics of normal GitCheck. It is not a substitute for acceptance evidence.

### Findings for next implementation

1. **Existing and reusable:** GitCheck identity/approval, exact detached execution, session supervisor, STOP, evidence publication, immutable result files, canonical ORION memory and UI, ORION Work Loop contracts.
2. **Missing for this owner workflow:** a V3-owned typed engineering-cycle record linking **task + ORION target revision + proposed diff + DeepSeek review + owner approval + TheHands session + independently evaluated acceptance evidence + next repair/freeze action**.
3. **Missing:** proven automated provider transport for ChatGPT and DeepSeek in this loop. Initial protocol can preserve manual review while remaining provider-neutral.
4. **Do not conflate:** `WorkLoopCoordinator` simulated autonomous Qwen execution with the collaboration loop; `git_check` script PASS with verified functional PASS; TheHands source commit with ORION target commit.
5. **No code or physical tests run** during this repository content audit; actual module implementation and physical acceptance remain pending.

### Step 1 verdict

**Repository text/source/document review: COMPLETE for tracked recognized text formats at pinned tree; binary/unrecognized formats: INVENTORIED; runtime verification: NOT RUN.** Documentation priority reconciliation and interface mapping: COMPLETE for the immediate engineering-loop scope. Future source changes require a delta audit; this result does not freeze code or qualify a new product module.

## Step 2 isolated module staged — physical test pending

New files: `src/orion_v3/engineering_loop/__init__.py`, `evidence.py`, `tests/test_engineering_loop_evidence.py`. These normalize exact TheHands published session identity and require an **HMAC-authenticated verifier receipt** bound to ORION revision + session before granting product PASS. The `verifier_key` is an external authority-owned secret; models and scripts must not control it. The module does **not** implement or run the verifier, automate ChatGPT/DeepSeek, write Vault, grant approval or execute Hands. No production wiring.

Pinned source revision: `2e6cfae8259215a1d8366e121fb47e6e1cfd2668`. TheHands designated GitCheck command staged on main `0d9562f09fa7ce9bdfb1a6efd6c90e3a8c098124` to run isolated pytest in disposable detached worktree and print actual ORION revision. **STAGED, NOT PHYSICALLY PASSED.** The owner must run GitHub Check → Approve & Start before qualifying this module. Review the contract and tests after physical results; do not freeze until PASS.
