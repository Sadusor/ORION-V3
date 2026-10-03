# V3-RUN-034 — candidate succeeded; unproven PATCH replay boundary failed

Date: 2026-10-04

Status: **PROCESS FAIL, BUT CODING CANDIDATE PHYSICALLY PROVEN CORRECT BEFORE PACKAGE REPLAY**

Remote source SHA:
`96ac368f9511c8fa41e298cc8ddb6ff05645e9c2`

Session:
`22ff0ef24bb9`

Exact V3 SHA:
`590e0069adf76e4d99286f74ef49b1980018a4b9`

## What RUN-034 physically proved

Case B ran with OpenHands stuck detection disabled.

Observed Terminal action executed the clamp verification.

Observed Terminal observation:
- output contained `All tests passed.`;
- `exit_code = 0`;
- `is_error = false`.

Observed final agent MessageEvent:
Qwen explicitly stated that the bug was fixed and correctly described the change
from:

`min(low, max(high, value))`

to:

`max(low, min(high, value))`.

Pinned OpenHands source proves that a normal content response is itself a valid
completion path:
`_handle_content_response(...)` emits the message and sets
`ConversationExecutionStatus.FINISHED`.

Therefore FinishTool is optional for this runtime path. It remains a metric, not
a qualification requirement.

## Why the benchmark reached the WorkPackage executor

RUN-034 calls `execute_verified_patch()` only after selecting a case with
`deterministic_ok=True`.

That requires, before WorkPackage execution:
- resulting `src/clamp.py` text equals the expected fix;
- changed paths equal exactly `src/clamp.py`;
- candidate Git HEAD remains at the exact base SHA;
- ORION's independent functional check passes.

The durable traceback occurred inside the WorkPackage executor verifier, after
those candidate checks.

Therefore the candidate itself was correct.

## Actual failure

The WorkPackage used a PATCH artifact generated from the candidate Git diff.

The executor mechanically replayed that PATCH in a second exact-SHA worktree,
then the raw-byte `file_sha256` verifier failed.

This exact combination was **not** physically proven by RUN-020.

Audit of V3-RUN-020 physical probe:
- FILE artifact exercised;
- PATCH artifact not exercised;
- no `git apply` path exercised.

So RUN-034 uncovered an untested ORION-core boundary:

`Windows candidate worktree -> textual Git PATCH artifact -> git apply in second
worktree -> raw working-tree file SHA verifier`.

Likely cause to characterize later:
Git/Windows working-tree newline/filter behavior causing raw-byte divergence even
when Git diff semantics and source text are correct.

Do not weaken the verifier without a dedicated deterministic gate.

## Cleanup defect

RUN-034 also failed temporary-directory cleanup because the harness did not close
`OrionStateStore` after the verifier exception.

Windows held `core.db` open, causing `WinError 32`.

This is a RUN-034 harness cleanup bug. Add `store.close()` in `finally`.

## Architectural decision

For OpenHands runtime qualification, use an exact FILE REPLACE WorkPackage from
the candidate bytes.

This:
- preserves exact candidate bytes;
- stays within an already-supported WorkPackage artifact kind;
- avoids conflating Agent quality with the newly-discovered PATCH replay
  portability issue.

Track PATCH replay as a separate ORION core gate before production use of PATCH
artifacts.

## Next gate — V3-RUN-035

Single compact OpenHands coding case:
- Qwen3.6;
- FileEditor + Terminal + optional Finish;
- `stuck_detection=False`;
- require final OpenHands execution status FINISHED;
- require Terminal observation exit code 0;
- require exact candidate path and functional result;
- capture exact candidate bytes;
- freeze `src/clamp.py` as FILE REPLACE using those exact bytes;
- verifier SHA binds to exact candidate bytes;
- execute through WorkPackage executor;
- require deterministic verifier PASS;
- close state store in `finally`.

A PASS qualifies compact OpenHands Agent as one candidate runtime for the ORION
Operator Benchmark.

It does not make OpenHands an ORION authority component.
