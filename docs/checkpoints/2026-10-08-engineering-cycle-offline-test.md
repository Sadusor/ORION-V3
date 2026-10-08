# ORION V3 engineering-cycle module — offline test checkpoint

Date: 2026-10-08
Scope: experimental branch only, ORION-owned code only.

Files: `src/orion_v3/work_loop/engineering_cycle.py` (commit 9ef9f2d), `tests/test_engineering_cycle.py` (commit 14e2497).

Evidence: six tests passed in 0.05 seconds using a local reconstruction of the exact visible module behavior and tests in an isolated Linux/Python environment. This is **not** a checkout of the entire ORION repository, **not** Windows physical proof, and **not** a complete ORION regression. The repo's actual test file has not been run by an ORION-native Windows runner yet.

Proven locally: required proposal/review before owner decision, stale digest rejection, invalid transition rejection, no direct execution method on the cycle. Not proven: authenticated owner identity, proposal/review integrity across persistence, Qwen adapter, provider provenance, restart recovery, authority/Vault integration, physical isolation, STOP, or end-to-end execution.

Important: `owner_decide` currently records a caller-supplied decision; it does **not** authenticate the owner and must never be treated as an ORION Authorization or permission to execute. The approval marker is a workflow record only. Do not wire it directly to a Work Hand.

Next bounded work: add explicit provider-neutral proposal/review envelope with role/provenance and deterministic tests, then bind owner decision through existing ORION authorization rather than inventing new approval authority. No execution enabled. Separate TheHands project is not part of this module.
