# Task Ledger batch calibration — Windows physical PASS

Date: 2026-10-08. Evidence: PowerShell 1 session `5b808d553abe`; result `PASS`; ORION tested HEAD `50abeb8b26f3341c8513a01187f3fe2de7fe7b47`.

Observed physical run: defective HTTP fixture rejected (1/19 checks passed, 18/19 correctly failed); known-good in-memory HTTP fixture accepted (19/19). Disposable SQLite tests all PASS: reopen persistence, atomic concurrent transition, rollback and integrity, and recovery after separate child process exits abruptly while a transaction is open. Final output: `LEDGER_BATCH> ALL_6_CALIBRATION_GATES_PASS` and `LEDGER_BATCH> PHYSICAL_PASS`.

Prior FAIL session `61a76c1a0cf3`: six gates completed but Windows temporary-directory cleanup failed with `WinError 32` because Python's SQLite context manager committed/rolled back without closing the database handle. Fixed via explicit connection closure at commit `50abeb8`; rerun PASS.

Limitations: these are evaluator calibration fixtures and standalone SQLite mechanism tests, not a complete durable HTTP Task Ledger implementation, hidden benchmark, real cloud/Qwen coding score, native ORION Hand, or end-to-end recovery. Do not promote this result to those claims. Keep hidden evaluator out of model-accessible workspace and retain frozen V1 untouched.

Next: freeze public contract; implement independently scored disposable Task Ledger submission and isolated persistence/restart/crash testing, then compare model configurations under equal conditions.
