# HistoryArchive V1 — Stage A evidence and hold points
Date: 2026-10-11
Status: SOURCE PROTOTYPE COMMITTED, TESTS NOT YET EXECUTED, NOT INTEGRATED OR DEPLOYED
Approved policy: docs/HISTORY_ARCHIVE_V1_POLICY_AND_IMPLEMENTATION_20261011.md

## Source-level inspection
- The actual backend ingress is `POST /api/chat-history/sync` in `src/orion_v3/product_server.py`: it executes `CHAT_HISTORY.sync(body)`, then runs nonblocking memory-candidate intake.
- `ChatHistoryStore.sync(payload)` receives batches of `conversations` and `messages`, deduplicates message IDs, and calls `_prune` before returning a snapshot.
- The live store truncates message text to 8,000 characters in its normalizer; archive must capture pre-normalized sync text. Its UI bound is 50 conversations and 100 messages each.
- `conversations.deleted` is a stored state flag. Do NOT infer from that flag alone that it is the owner's irreversible delete; confirm exact PC/Android semantics before wiring archive deletion.
- `memory_retrieval.py` uses snapshot-based bounded lexical matching. Its source remains untouched.
- `canonical_memory_integration.py` currently creates same-thread context from recognized legacy Android wrapper only. Its source remains untouched.

## Committed additive Stage A prototype
- `src/orion_v3/modules/history_archive_v1.py` — isolated second SQLite journal with original text, immutable ID-based append, scoped reads, explicit owner-delete-only tombstones, export, idempotent resync and validation.
- `tests/test_history_archive_v1.py` — isolated tests of >8k text, delete/replay, scope isolation, atomic validation failure, export, >100 archived messages and restart.
- No calls into the archive from `product_server.py` yet. No production SQLite schema modification. No live migration.
- No existing frozen modules were modified.
- Tests are source-committed but not yet physically run. Do not report PASS.

## Required before enabling Stage B
1. Run `python -m pytest -q tests/test_history_archive_v1.py` from a current ORION checkout; capture exact pass/fail count.
2. Review original Windows/Android serialization of sync, including project IDs, message IDs, model ID, current chat context, deletion/archive semantics, and whether source text is truncated upstream.
3. Protect initial archive migration with verified DB backup and documented recovery; no auto-deployment.
4. Plan explicit deletion/tombstone protocol and cross-DB partial-failure recovery before wiring into sync; do not interpret automatic prune as owner delete.
5. Then stage behind a non-live feature gate, test 50+ conversations, >100 messages, restart and phone/PC retry; only then offer owner activation.
6. Build current-thread prompt injection and operating guide separately after archive acceptance.
