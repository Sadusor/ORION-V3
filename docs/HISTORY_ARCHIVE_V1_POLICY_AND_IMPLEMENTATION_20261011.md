# ORION V3 — History Archive V1: Approved Policy and Implementation Record
Date: 2026-10-11
Status: OWNER-APPROVED DESIGN; NO LIVE DEPLOYMENT AUTHORIZED
Scope: ORION V3 only. TheHands is an independent frozen product: DO NOT CHANGE.

## Why this work is needed
Physical ORION/Qwen conversations showed three distinct failures:
- Qwen mistook recalled *older* conversation snippets (History Integrity V1) for the first question in the *current* chat.
- Qwen lost contextual references ("there", "other repositories") after successful MyGitea2/PayDay retrieval, prompting a temporary phrase router fix; this is not general conversational continuity.
- Qwen stated it had no access to Gitea at all, when in fact Qwen has no direct tools but the ORION platform has verified read-only MyGitea2 retrieval (109 repositories enumerated, PayDay ROADMAP and STATUS documents retrieved).
The owner needs searchable original conversations even one year later, without inserting all prior chat into every model prompt.

## Existing facts from source inspection
- `src/orion_v3/modules/chat_history.py`: `ChatHistoryStore` uses `chat_history.sqlite3`, handles `sync(payload)`; `_prune` deletes beyond 50 conversations / 100 messages per conversation; incoming text is truncated at 8,000 characters. These are retention limits, not UI-only limits.
- `src/orion_v3/modules/memory_retrieval.py` reads `ChatHistoryStore.snapshot()` and uses bounded in-Python lexical/BM25-style retrieval; no FTS5 archive proven.
- `src/orion_v3/modules/canonical_memory_integration.py` only populates its current-conversation context using a recognizable legacy Android wrapper; passing `conversation_id` from `product_server.py` alone does not establish ordered transcript injection.
- `src/orion_v3/modules/local_brain.py` currently tells the model it has no tools, without clearly distinguishing direct model powers from ORION's authorized backend retrieval.
- Live MyGitea2 retrieval and inventory were previously tested; local 17 Python + 388 STRATA regression and follow-up routing check passed, but evidence publishing through TheHands failed separately. TheHands must not be edited.

## OWNER-APPROVED POLICY (2026-10-11)
1. Keep existing bounded UI/sync ChatHistoryStore behavior and frozen files intact.
2. Add an independent, durable SQLite HistoryArchive journal preserving original owner and assistant message text, project/conversation/message IDs, role, timestamp, source/model metadata and provenance. Archive is NOT canonical memory or an instruction source.
3. Automatic live-history pruning NEVER deletes permanent archived records.
4. Owner action Archive means hide from active list but retain permanent searchable history.
5. Owner action Delete means delete that conversation from both live history and permanent archive. Explicit archive deletion also removes archive data. Never silently preserve intentionally deleted conversations. No separate preserve flag in V1.
6. Export copies messages to an independent owner-managed file; export does not modify storage.
7. Preserve idempotence across PC/Android resync; prevent duplicate message records; enforce project scope at the query boundary and treat assistant messages as unverified assistant-generated text.
8. Ensure durable capture is confirmed before considering a message durably saved; surface archive write failures. Because SQLite files are separate, analyze recovery/reconciliation and partial failure rather than claiming a cross-DB transaction.
9. Never modify ORION verifier/STOP/approval authority, frozen canonical memory/retrieval modules, or TheHands.
10. Back up existing DB files before installation/migration; test in isolated fixtures, then run GITCHECK and real Windows/Android acceptance; no auto deployment.
11. Current-thread context comes from ordered messages with the actual active conversation identity, not semantic recall. Historical archive is queried only for appropriate historical retrieval, never indiscriminately injected into live chats.

## Agreed modular implementation order
A. Trace exact write/sync/delete contracts across `product_server.py`, Windows STRATA UI, Android client and `chat_history.py`. Confirm original untruncated text and real project/message identity. Do not assume `ChatHistoryStore.add` exists; observed method is `sync`.
B. Add standalone `history_archive.py` SQLite writer/reader with schema, idempotent append, scoped query, export and explicit deletion. Ensure archive write ordering at actual ingress and reliable failure reporting; do not modify frozen storage module. Preserve raw source messages where available and document any upstream truncation.
C. Integrate archive at verified message-ingress boundary; ensure user Delete and background prune differ, including tombstone/replay handling so sync cannot resurrect deleted material.
D. Wire bounded, accurately labeled current-thread messages from history to Qwen at a non-frozen request handler seam; preserve first message and recent turns, with explicit gap when needed; do not weaken 16 KiB local-brain request limit.
E. Add a concise versioned `config/ORION_IDENTITY_V1.md` loaded with each effective request. Qwen has no direct tools; ORION can perform authorized read-only retrieval; current-thread, historical recall, verified sources and durable memory are separate. Capabilities are not evidence of a completed retrieval.
F. Benchmark historical archive retrieval at 1k/10k/100k messages for exact phrase/date/project/role and latency; reuse existing retrieval semantics through an adapter. Add FTS5 only on measured need. No embeddings without specific benchmark failure.

## Acceptance requirements
- >100 messages per conversation, >50 conversations total: original text still retrievable after prune and restart.
- Automatic prune retains archive; explicit Delete removes from both stores, including non-resurrection after stale sync.
- Ordered first question of current conversation answered accurately after 20+ turns, without confusing other chat recall.
- PayDay -> "there" -> other repos -> "first two" follow-ups grounded in actual authorized evidence, not invented repo lists.
- One-year-old dated fixture retrievable with exact original message, date, role, conversation and project; missing record acknowledged.
- All writes idempotent under phone/PC resync, including failures and recovery.
- Scoped retrieval cannot leak cross-project; assistant outputs never become owner instructions or canonical facts.
- Model properly distinguishes Qwen direct limitations from ORION read-only Gitea backend; never claims unperformed verification.
- Freeze regressions pass, including verification, STOP, canonical memory, Gitea. TheHands unchanged.

## Review / corrections already incorporated
Independent DeepSeek reviews initially suggested just a prompt plus existing wiring; later corrected after discovering destructive live pruning. Owner advocated separate long-term database instead of modifying pruning. Subsequent reviews agreed independent archive is simpler, and clarified: automatic prune != explicit Delete; actual write path is `sync(...)` not an assumed `add(...)`. Final policy above explicitly approved by owner.
Do not treat reviewer approval as deployment approval.

## Status ledger
- Approved: policy and phased investigation/implementation.
- Not yet proven: actual ingress in Windows/Android, delete sync semantics, upstream truncation, safe multi-DB failure handling, full historical recall performance.
- No tests of new archive reported PASS as of creation.
