# Benchmark A public evaluator — physical calibration PASS

Date: 2026-10-08. Evidence: PowerShell 1 session `8789ca05e44a`, published result PASS, tested ORION revision `7967ac81d80bb84b0d1ec9af96282a5b9f6f6ec7`.

Observed: deliberately defective HTTP fixture scored 1/19 (health only) and was correctly rejected. Known-good in-memory fixture scored 19/19 and was correctly accepted. Both ran through loopback HTTP on Windows.

This establishes public evaluator discrimination against these two fixtures only. It does **not** establish general evaluator correctness, disk persistence, abrupt termination recovery, hidden-test validity, native Hand qualification, cloud-model coding performance, or full work-loop performance.

Next: add independent durable SQLite fixture and restart/crash tests, verify against known-good and defective durable fixtures; freeze benchmark protocol before scored runs. Keep hidden evaluator out of model-accessible workspace. No frozen ORION/V1 changes; PowerShell 1 is transport provenance only.
