# Memory Indexed Retrieval V2 — Physical PASS and freeze

Date: 2026-10-10
Status: **STANDALONE INDEXED CANDIDATE MODULE PHYSICAL PASS; FROZEN**
ORION source commit physically tested: `2b48a5939ebcd26fde2491a32b80826f21f46bcc`
Frozen branch: `frozen/memory-indexed-retrieval-v2-20261010`
TheHands separate engineering remote source commit: `dbb7df6e572e28a59d747704e5b5ecaea5571c3b`
TheHands session: `7c755b413c59`, physical `PASS`
Output: `ORION_INDEXED_RETRIEVAL_V2> PASS`, `2b48a59`, `ORION_INDEXED_V2_GITCHECK> PASS`.

First attempt session `bc7a05715ca2` FAILED because SQLite connections remained open when Windows temporary directory cleanup attempted deleting derived.sqlite (WinError 32). Fixed by explicitly closing FTS5 SQLite handles via contextlib.closing. The next physical test passed.

Scope qualified: independent experimental FTS5 sidecar test, exact token retrieval, explicit project scope, inactive filtering, project segregation, quoted query safety and rebuild; Windows cleanup succeeds. This is NOT a production hybrid vector integration or end-to-end canonical retrieval test.

All frozen Memory V1/V1.1 paths and actual memories remain untouched. Do not modify this passing V2 module; new capabilities belong in separate modules, and any necessary direct fix requires owner approval per FREEZE RULE.

Benchmark context: separate test rigs showed exact FTS5 index lookup at 1M synthetic records p50 0.0861ms (50/50 scoped exact queries), and a 10-fact semantic embedding test 10/10. These are distinct experiments; no evidence of a 1M semantic index or full hybrid production throughput.

Next: owner-requested ORION V3 roadmap changes. Any future canonical adapter or semantic vector retrieval is a new gated module and must preserve read-only context, provenance/supersession/STOP and authority semantics.
