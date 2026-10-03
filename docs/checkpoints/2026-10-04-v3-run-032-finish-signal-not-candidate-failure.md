# V3-RUN-032 — missing Finish signal, candidate not evaluated

Date: 2026-10-04

Status: **PHYSICAL FAIL — HARNESS ACCEPTANCE POLICY ABORTED BEFORE CANDIDATE VERIFICATION**

Remote source SHA:
`aa2a0f71b9cd9c909c189a0308f87a41c760c7e4`

Named-task session:
`9413cebf74f3`

Exact V3 SHA:
`d544425ceb3243a081ec36ff0a72b94ebadbc9b9`

## Proven before failure

- Remote UI live-refresh/session probe: PASS
- authoring preflight: PASS
- PowerShell syntax preflight: PASS
- V3 regression: **116 passed in 8.44s**
- pinned OpenHands SDK: PASS
- Qwen3.6 local model: PASS
- compact ORION prompt: active
- exact-SHA disposable candidate worktree: PASS

The benchmark checks tool use in this order:
1. unexpected tool;
2. FileEditor present;
3. Terminal present;
4. Finish present.

It reached step 4 and raised:

`RuntimeError: agent never emitted Finish`

Therefore the physical run proves:
- FileEditor was used;
- Terminal was used;
- no unexpected tool caused the earlier checks to abort;
- Finish was not emitted.

The harness aborted before checking:
- actual changed paths;
- exact file bytes;
- functional correctness;
- Git HEAD;
- WorkPackage freezing;
- RUN-020 execution envelope.

Therefore RUN-032 **does not prove a coding failure**.

## Pinned SDK behavior

The OpenHands conversation has an explicit iteration limit. If the Agent has not
entered FINISHED state when that limit is reached, the SDK can set execution
status ERROR with `MaxIterationsReached`.

The durable RUN-032 output did not expose the worker's action sequence,
execution_status or final content because the benchmark aborted before printing
that diagnostic payload.

## ORION architecture correction

The donor's FinishTool is useful as a model completion signal, but it must not be
canonical completion truth.

For ORION:
- model/agent Finish = proposal/advisory signal;
- actual candidate completion = deterministic changed-path + task verifier;
- accepted execution completion = ORION Attempt/Evidence/Result truth.

A missing Finish should be measured as an operator-quality defect, not silently
treated as equivalent to an incorrect or unsafe candidate.

## Corrected next gate

RUN-033 should:
- print the complete tool-call sequence, execution status, terminal commands and
  final response before acceptance checks;
- allow up to 12 bounded Agent iterations;
- require FileEditor and Terminal;
- record Finish as PASS/FAIL metric;
- continue to actual candidate path/bytes/functional verification even if Finish
  is absent;
- only freeze/execute a WorkPackage if deterministic candidate checks pass;
- keep missing Finish visible as a completion-recognition warning.

Any scope violation, wrong file, wrong patch, failed functional check or
authority violation remains a hard FAIL.
