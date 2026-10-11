# ORION V3 HistoryArchive Stage C3 — Isolated Ingress Qualification
Date: 2026-10-11
Status: CODED / NOT YET TESTED / NOT LIVE

## New module
`src/orion_v3/modules/history_archive_ingress_v1.py`: isolated ingress facade wrapping previously qualified Stage B archive-first sync and Stage C1/C2 replay/delete components.
- Normal remote sync requires verified paired-device authentication; local_trusted is deliberately limited to ordinary sync and NEVER owner deletion.
- Owner delete requires a verified paired owner token even on loopback.
- Tombstone replay guard runs before archive append or live sync.
- A shared per-instance lock serializes sync and delete for the disposable single-instance qualification.
- `deleted` client metadata does not authorize owner deletion.

## Tests
`tests/test_history_archive_ingress_v1.py` adds six integration tests, alongside the 25 previously passing Stage A/B/C1/C2 tests, targeting 31 tests total.

## Release holds (do not activate)
This layer is NOT installed on `product_server.py`; no authenticated HTTP route has been added. A production integration must use the existing `AUTH.valid` / `_require_owner_token` contracts without accepting `owner_authorized` or `local_trusted` from the request JSON. It also needs cross-process serialization, startup recovery of partial deletions, repaired PC/Android tombstone exchange, true project provenance and pre-truncation message capture.
The current client 'Delete' is still a flag, not a verified owner-delete HTTP call. When enabled, archive-first sync refuses flagged rows instead of deleting them.
Frozen live ChatHistoryStore, Stage A/B/C1/C2, canonical memory, MyGitea2, STOP and TheHands application remain unchanged. Experimental archive activation remains OFF.

## Qualification
Run prior 25 unit tests plus the 6 Stage C3 tests, plus Python compile, on the Windows ORION isolated checkout under TheHands PowerShell 1. Record exact GitHub evidence before claiming PASS.
