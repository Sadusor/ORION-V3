# ORION V3 live chat retrieval wiring audit — 2026-10-12

Status: SOURCE AUDIT ONLY. No runtime edits, no production changes, no live qualification. This note supersedes the assumption that a new model-led retrieval coordinator is required.

## Verified source path (GitHub main, not independently checked against running production)
- product_server.py constructs CHAT_HISTORY = ChatHistoryStore(STATE_ROOT / "chat_history.sqlite3") and MEMORY_RETRIEVAL = MemoryRetrievalModule(CHAT_HISTORY).
- CanonicalMemoryIntegratedBrainPipeline wraps RepoAwareChatBrain(MultiRepoDocumentChatBrain, DocumentAwareGiteaChatBrain). Memory, document index and Gitea sources are separately assembled into the same Qwen goal.
- /api/local-hand/draft obtains owner_text and source_project, calls named_repo_scope, enters indexed_chat_request and multi_repo_chat_request, and starts LOCAL_BRAIN.
- Default Gitea chat uses gitea_chat_brain_v1, search_live_gitea_v2, UniversalRetrievalV1 and context-only citations. Accepted frozen grounding path physically passed for History Integrity V1.
- Named repository lookup only resolves owner-authorized entries. Generic plural "my repositories" is not a named-repository match and defaults to ORION-V3 when source_project is orion-v3. Inventory visibility does not confer authorization.
- chat-source-trace.jsonl from owner shows lookup=hit, injected=true, source_errors=[] but irrelevant paths (tests, docs, memory sidecar). Therefore the observed failure is NOT proof of broken Gitea API. Relevant implementation evidence was not shown in those traces.
- streaming_local_brain.py tells Qwen "You have no tools" and "Do not claim ... searched". This may conflict with the model's interpretation of pre-retrieved evidence; no live A/B proof of this as sole cause.

## History/archive reality
- /api/chat-history/sync writes to bounded ChatHistoryStore when ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL != "1". It invokes advisory memory candidate selection.
- MemoryRetrievalModule reads ChatHistoryStore.snapshot(), with project scope, 50-conversation and 100-message-per-conversation caps. This is the proven live conversation recall input, not an unbounded historical archive.
- HistoryArchiveV1 and ArchiveSearchProjectionV1 are separate, qualified candidate components. ArchiveSearchProjectionV1 requires refresh. Product archive sync and search are experimental/disabled by default; production October 11 fix ledger explicitly says archive automatic indexed ingestion was not proven.
- Therefore "all databases automatically feed every chosen AI" is an intended architecture, NOT an established current runtime guarantee.

## Safest next acceptance gate
1. Compare running source commit and actual production product_server.py to GitHub main, accounting for the owner's existing uncommitted verifier boundary change in the test checkout. Do not reset or overwrite that file.
2. Read-only examine trace of one new owner query and selected source IDs; verify source scope and relevant paths.
3. Separately inspect actual SQLite counts/project distribution and opt-in flags without mutating databases or exposing message text or secrets.
4. Only then identify a minimal additive integration seam and test with selected Qwen model. No changes to frozen memory, chat history, source grounding, production database, or TheHands.
5. Do not merge or deploy qwen_readonly_investigation_candidate_v1.py or qwen_gitea_investigation_bridge_candidate_v1.py; these are unapproved experimental files on this isolated branch.

## Acceptance
No live fix claimed. The candidate's eight isolated offline unit tests passed per owner PowerShell output; that does not qualify an end-to-end chat change.
