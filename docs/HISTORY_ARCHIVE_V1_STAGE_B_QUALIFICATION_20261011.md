# HistoryArchive V1 — Stage B experimental sync qualification
Date: 2026-10-11
Status: GITHUB-CODED / UNVERIFIED, OFF BY DEFAULT

## Proven baseline
Stage A physical PASS: 6/6 unittest on Windows, session `38db8c366592`, ORION commit `f5329013ce6cd06d8e9ef118bcf56e4cb60776bb`. Frozen archive module remains unchanged.

## Added integration seam
- `src/orion_v3/modules/history_archive_sync_v1.py` contains `archive_first_sync`, which takes the raw sync body, validates projects and deletion state, archives raw text, then invokes existing `CHAT_HISTORY.sync` unchanged.
- `src/orion_v3/product_server.py` contains an experimental-only conditional around `/api/chat-history/sync`. With env `ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL` absent or not equal to `1`, the original `CHAT_HISTORY.sync(body)` runs unchanged.
- If manually enabled only in disposable qualification environments, the archive file is `STATE_ROOT/history_archive.sqlite3`; archiving precedes bounded live-store sync. Archive failure prevents live sync. Separate SQLite files cannot provide a shared transaction; crash recovery and ordering still require testing.
- For safety, experimental route currently refuses `deleted` conversation rows and unknown project identity. Owner deletion semantics are not yet proven, so this is a deliberate qualification blocker, not a finished production feature.
- No edit to frozen `chat_history.py`, `canonical_memory_integration.py`, `memory_retrieval.py`, verifier, approvals, STOP or TheHands runtime. TheHands PowerShell 1 **task file only** updates for tests.

## Test plan
- `python -m unittest -v tests.test_history_archive_v1 tests.test_history_archive_sync_v1` (11 tests expected)
- `python -m py_compile src/orion_v3/modules/history_archive_v1.py src/orion_v3/modules/history_archive_sync_v1.py src/orion_v3/product_server.py`
- GITCHECK in TheHands PowerShell 1: source commit `6cc9a828c388048396cd66213588f92f88265fae`; Hand task commit `0e97e727ab1d08f6b0f22334852241813929c5b2`.
- No stage B PASS until actual evidence is returned.

## Remaining release blockers
1. Read exact Windows and Android sync and Delete/archive actions; distinguish owner deletion from transport's 'deleted' metadata and pruning; implement safe tombstone propagation and retry ordering.
2. Recover from multi-DB partial failures, prevent stale client re-upload/replay after owner delete.
3. Prove upstream raw text available before any client truncation and normalize project identity for both clients.
4. Benchmarks, current-thread injection, archive retrieval adapter and per-request operating guide are later, separate stages.
5. Do not enable this experimental flag on live ORION before cross-client qualification.
