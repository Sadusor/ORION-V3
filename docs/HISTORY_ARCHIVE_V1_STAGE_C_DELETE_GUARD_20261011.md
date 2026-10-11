# HistoryArchive V1 — Stage C1 isolated replay guard
Date: 2026-10-11
Status: CODED, UNVERIFIED, NOT LIVE

## Scope
New replaceable module `src/orion_v3/modules/history_archive_delete_guard_v1.py` contains `OwnerDeleteLedgerV1`, storing permanent owner-delete tombstones in a separate SQLite ledger and refusing incoming stale conversation/message replays. Test module `tests/test_history_archive_delete_guard_v1.py` has 8 isolated cases.

## Security caveats / hold points
- The `owner_authorized=True` argument is **not** an authentication system. It is only an internal assertion for unit tests. A real server route must first verify the authenticated owner, bind the identity to the project/conversation, authorize deletion, and prevent client-controlled use of this flag.
- This does not yet delete live or archived messages. Tombstones must be coordinated with actual deletion and failure recovery without creating a falsely successful delete.
- The guard currently **rejects the whole sync batch** on a replay, not an interactive client synchronization protocol. PC/Android client repair and tombstone propagation are still needed.
- Fail-closed on the guard's own SQLite errors; persistent tombstone DB backup/recovery is essential.
- Nothing is wired into `product_server.py`; `ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL` remains off; no deployed feature is claimed.
- Frozen Stage A/B modules, chat-history, canonical memory, STOP, TheHands product and Gitea remain untouched.

## Qualification
Run isolated test `python -m unittest -v tests.test_history_archive_delete_guard_v1` and `python -m py_compile src/orion_v3/modules/history_archive_delete_guard_v1.py` through TheHands PowerShell 1. Keep prior Stage A/B regression suite included. Physical PASS must be read from results branch before freezing this new module.
