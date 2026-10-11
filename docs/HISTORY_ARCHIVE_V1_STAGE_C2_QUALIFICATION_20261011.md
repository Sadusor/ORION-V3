# ORION V3 — Stage C2 Delete Coordinator Qualification
Date: 2026-10-11
Status: CODED / NOT TESTED / NOT LIVE

## Scope and design
- Additive isolated module: `src/orion_v3/modules/history_archive_delete_coordinator_v1.py`.
- Additive tests: `tests/test_history_archive_delete_coordinator_v1.py` (6).
- Frozen Stage A archive, Stage B sync adapter, Stage C1 tombstone ledger, original ChatHistoryStore all unchanged.
- Delete coordinator requires caller assertion `owner_authorized=True`; this is NOT HTTP authentication and MUST NOT be mapped to request JSON. Any future HTTP route must verify authenticated owner via existing authorization boundary.
- Before an irreversible write, confirm project scope against BOTH live and archive records.
- Durable tombstone first, then delete archive messages, then delete live SQLite records; retry after interruption finishes deletion.
- `guarded_sync` blocks stale replay when the caller routes all syncs through it with serialization.

## Known limits and remaining blockers
- **Not crash-atomic across three SQLite files.** Tombstone-first with retry provides fail-closed behavior ONLY if every sync path checks ledger. No live sync path is wired yet.
- Separate coordinator instances/processes are not jointly serialized. Production requires shared ingress gate and startup recovery/reconciliation.
- Authentic owner event, project identity, PC and Android tombstone protocol, and capture before client 8000-character truncation remain unresolved.
- Never enable experimental archive or delete operation in production based only on this module's tests.
- The archived delete method preserves minimal tombstones; this is the previously approved replay-protection exception to erasing message content.

## Physical qualification
PowerShell 1 should run all preceding suites (19 tests) plus 6 new C2 tests (25 total) and Python compile in known isolated checkout. Only TheHands physical PASS is evidence for Stage C2 qualification.
