# Task Ledger SQLite reference — Windows physical PASS

Date: 2026-10-08. PowerShell 1 physical evidence session `992426ad7a7e`; result `PASS`. Tested ORION branch `spike/windows-isolation-preflight-20261008`, HEAD `782e1a7203fa383060a1a4f997c49b8ecc44b360`.

The batch executed both calibration fixtures: deliberately broken service rejected (1/19), in-memory good fixture accepted (19/19); SQLite reopen, atomic concurrency, rollback/integrity, and abrupt child-process-exit recovery all PASS. Then it launched a separate disposable SQLite-backed HTTP reference service: all 19 public HTTP checks PASS. It created a task, transitioned it to RUNNING, killed the server process, restarted against the same database, verified the RUNNING state survived, transitioned to DONE, and verified terminal state could not reopen. Output `LEDGER_REFERENCE> BATCH_ALL_PASS` and `LEDGER_BATCH> PHYSICAL_PASS`.

Limits: reference code is authored by us, not a model submission. No independent held-out test suite has been scored. Public HTTP tests are 19 checks, not the >=20 developer-written tests required of eventual model submissions. The test does not demonstrate recovery from arbitrary power loss, STOP latency, Windows native Work Hand qualification, sandbox network denial, memory promotion, or an end-to-end ORION work loop. Do not conflate isolated SQLite fixture crash tests with the full HTTP reference's mid-write crash behavior.

Next: freeze contract and evaluator access separation, package neutral model task prompts, generate separate model submissions, then score with independent tests under equivalent budgets. Preserve V1 and all frozen ORION modules.
