# HistoryArchive V1 — Stage C client sync/delete contract inspection
Date: 2026-10-11
Status: SOURCE-INSPECTED; NO LIVE CHANGE; NOT YET QUALIFIED

## Already established (do not re-audit)
The POST /api/chat-history/sync handler calls ChatHistoryStore.sync(body), with bounded prune; Stage B has an off-by-default archive-first seam, isolated 11/11 Windows PASS, TheHands session a01537046e02.

## Actual clients inspected
- ui/strata/modules/chat-history.js
- android/app/src/main/java/com/sadusor/orionv3/history/ChatHistoryStore.kt
- android/app/src/main/java/com/sadusor/orionv3/online/OrionPcBridge.kt
- src/orion_v3/modules/chat_history.py

## Findings and mandatory fixes (not implemented)
1. Desktop chat-history.js starts conversations with project_id: '' by default (ensureConversation/newConversation). Stage B experimental gate correctly refuses archive messages without explicit project identity. Need policy-defined identity mapping from authenticated project context, not silent global fallback.
2. Desktop Archive sets archived:1 and filters it from active list. Delete sets deleted:1 and filters it. Neither is by itself a verified owner-intent durable-delete operation at server; do not equate these flags with physical archive erasure without an authenticated, replay-resistant deletion protocol.
3. Android ChatHistoryStore uses MAX_TEXT_CHARS=8000 and bounded prune; once the Android local store has truncated message text, posting snapshot cannot restore original characters. Capture untruncated owner/assistant turns at ingress before client normalization, with a focused Android boundary test.
4. Android OrionPcBridge.syncHistory obtains local snapshot, POSTs /api/chat-history/sync, then merges server response into Android SQLite. Desktop does similar POST and merge, periodically. Without a server-owned tombstone/epoch, a stale device can replay older conversation state. Current live ChatHistoryStore uses updated_at_ms for conflicts, but retention/automatic prune must never be mistaken for owner Delete.
5. Existing live ChatHistoryStore _normalize_message truncates to 8000 and _prune removes over-limit messages/conversations. Neither is an archive. Preserve frozen behavior.
6. Stage B experimental archive-first adapter refuses deleted rows and missing project scope. Leave ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL off. A successful 11/11 Stage B test does NOT establish full cross-client deletion or true untruncated Android ingress.

## Next bounded modules/tests
A. Add independent authenticated owner-delete command contract with durable archive tombstone and server replay protection (including stale PC/phone snapshots, timestamp collisions, and retry ordering). Do not modify frozen archive module: use additive coordinating/ledger module and physical tests.
B. Qualify project identity transport (desktop + Android) for archive sync without changing frozen live store behavior.
C. Qualify source-text capture at earliest client/response boundary before Android/PC 8000-character trimming. Avoid silently claiming raw text preserved when client already truncated it.
D. Test cross-file partial failures/retries, then owner-approved feature activation, not before.

Decision: Keep the separate archive DB; keep Gitea and frozen modules untouched. No production deployment or flag activation.
