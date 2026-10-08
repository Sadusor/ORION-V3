# Benchmark A — Neutral model submission protocol v0.1

This is the exact common task for all contenders. Do not include reference implementation code, calibration fixture code, or hidden tests in any contender's context.

Build a standalone Python 3 Task Ledger HTTP server using only the standard library and SQLite. Implement the versioned public HTTP contract in `docs/benchmarks/TASK_LEDGER_HTTP_CONTRACT_V01.md` (provide that contract text to every contender verbatim). Deliver code under `task_ledger/` with a working entrypoint `python -m task_ledger --host 127.0.0.1 --port PORT`, taking a disposable SQLite path from `TASK_LEDGER_DB`. Include >=20 developer-visible automated tests and a concise README.

Required: atomic and durable state transitions, strict input validation, deterministic listing, read-only evidence endpoint, recovery across restart and abrupt process termination. Do not use external databases, package installation, cloud calls, non-loopback listeners, or writes outside the provided disposable workspace.

## Submission artifact
Provide an archive or isolated directory containing only source, tests, and README. Record contender ID, model ID, exact prompt hash, trial seed, elapsed time, number of calls, token counts where available, and human interventions. Do not claim a PASS based on self-tests.

## Equal-treatment rules
- Same frozen spec, tool access, time budget, workspace permissions and evaluator for all contenders.
- Three fresh trials per contender. No reuse of prior solution files, test feedback or reviewer discussion across independent baseline trials.
- Contenders: single cloud; cloud council; Qwen 9B; council+Qwen+ORION. An unavailable model or native execution route is `NOT_RUN`, never a failing model score.
- The benchmark reference source and calibration tests in this repository are NOT to be included in contender prompts or checked out in model-accessible coding workspaces.
- Only independent black-box evaluation counts. Held-out tests remain outside model-accessible repositories and transcripts.
- No direct production ORION/V1 modifications. No automatic retries or unsafe commands.

## Run readiness
Protocol is staged, not yet a completed model submission or scored comparison. Native Work Hand isolation qualification remains a separate gate.
