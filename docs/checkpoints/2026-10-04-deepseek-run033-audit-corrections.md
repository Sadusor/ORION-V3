# DeepSeek RUN-033 audit — verified corrections and RUN-034 plan

Date: 2026-10-04

## What the external review got right

- Do not abandon OpenHands Agent after RUN-033.
- Prevent Python bytecode-cache pollution instead of treating it as a source edit.
- Capture FileEditor/Terminal observations and stuck diagnostics.
- Compare stuck detection enabled vs disabled.
- Treat donor Finish as an operator-quality signal rather than canonical ORION truth.

## Correction 1 — 119 tests did not prove the candidate verification

The durable RUN-033 log shows:

`119 passed in 11.43s`

under `V3_REGRESSION> RUN`, before the OpenHands benchmark starts.

Those are ORION repository regression tests.

The agent later emitted a Terminal Action containing a sensible Python assertion
command, but RUN-033 did not capture the corresponding Terminal Observation or
exit code.

Therefore:
- Terminal verification was attempted: PROVEN;
- Terminal verification succeeded: NOT YET PROVEN.

Do not classify the coding candidate itself PASS until the observation and
deterministic candidate checks prove it.

## Correction 2 — exact rc/clamp.py harness bug found

RUN-033 contains:

`def git(...): return run(["git", *args], cwd=cwd).stdout.strip()`

and changed-path parsing:

`raw = line[3:].strip()`

For a normal worktree modification, Git porcelain v1 begins the first line as:

` M src/clamp.py`

The generic `.strip()` removes the leading status-space from the complete Git
output, producing:

`M src/clamp.py`

Then `line[3:]` yields:

`rc/clamp.py`

This exactly explains the observed corruption.

This is not an OpenHands/FileEditor path mutation.

Correction:
- never pass porcelain output through the generic stripped `git()` helper;
- use a raw Git-output helper;
- use `git status --porcelain=v1 -z --untracked-files=all`;
- preserve and print the raw NUL-delimited records;
- parse status/path without stripping leading status bytes.

Add a regression for this exact failure.

## Correction 3 — STUCK cause is still unknown

Pinned OpenHands SDK defaults:
- repeating action/observation threshold: 4;
- action/error threshold: 3, with actual stuck only after the threshold is
  exceeded;
- monologue threshold: 3;
- alternating-pattern threshold: 6.

RUN-033 recorded only three ActionEvents:

`file_editor, file_editor, terminal`

Therefore the external review's suggestion that two FileEditor calls themselves
triggered the default repeating action/observation detector is not established.

Possible causes include an unobserved message/error pattern.

RUN-034 must capture the actual event tail and evaluate each stuck-detector
predicate after termination.

## Bytecode policy

Set `PYTHONDONTWRITEBYTECODE=1` before OpenHands creates its Terminal executor so
child Python processes inherit it.

Also run ORION's independent Python candidate check with `-B`.

Do not silently delete bytecode before changed-path inspection: prevention is
preferred because cleanup could hide a real unexpected side effect.

## V3-RUN-034

Purpose:
separate candidate correctness from OpenHands completion/stuck behavior and
identify the exact STUCK predicate.

Same:
- Qwen3.6-35B-A3B;
- compact ORION prompt;
- FileEditor + Terminal + Finish;
- synthetic clamp task;
- exact-SHA disposable worktrees.

Case A:
- `stuck_detection=True`.

Case B:
- `stuck_detection=False`.

Both cases capture:
- full ordered relevant event trace;
- FileEditor action arguments and observations;
- Terminal action command, observation and exit metadata;
- AgentError/ConversationError events;
- final execution status;
- Finish presence;
- stuck detector thresholds;
- exact predicate results over the final event window;
- raw `git status --porcelain=v1 -z` records;
- exact changed paths;
- resulting diff/file bytes;
- deterministic functional check.

Hard failures remain:
- wrong source result;
- wrong path;
- unexpected persistent filesystem mutation;
- candidate Git HEAD change;
- unauthorized tool;
- failed deterministic functional check.

Diagnostic/runtime metrics:
- STUCK with detector ON;
- STUCK with detector OFF;
- Finish present/absent;
- action count and wall time.

If Case B is correct and avoids STUCK, OpenHands remains qualified as a runtime
candidate even if Finish remains advisory.

If Case B is correct but still cannot terminate cleanly, next compare:
- OpenHands Agent machinery;
- OpenHands tools under an ORION-owned step loop;
- OpenJarvis runtime.

Do not run another prompt-dissection campaign.
