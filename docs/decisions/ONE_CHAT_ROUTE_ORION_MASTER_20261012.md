# ORION V3 — One Chat Route Architecture Decision (2026-10-12)

**Owner decision:** ONE model-facing chat route for all authorized data sources. ORION is the master. No parallel Gitea chat route, memory chat route, archive chat route or model-specific chat route. Separate storage and retrieval adapters remain allowed; separate conversation entry points are not.

## Existing production composition — reuse, do not rebuild

`POST /api/local-hand/draft` in `src/orion_v3/product_server.py` starts `LOCAL_BRAIN`, a `CanonicalMemoryIntegratedBrainPipeline` wrapping `RepoAwareChatBrain(MultiRepoDocumentChatBrain, DocumentAwareGiteaChatBrain)`.

- CanonicalMemoryIntegratedBrainPipeline retrieves scoped conversation recall, owner-approved durable memory, and relevant durable supersession history. It composes the owner directive and bounded context.
- DocumentAwareGiteaChatBrain reads indexed_documents.sqlite3 under the selected project.
- GiteaChatStreamingBrain reads the existing MyGitea2 code index and attaches cited source excerpts for the ORION-V3 project.
- MultiRepoDocumentChatBrain handles explicitly selected owner-authorized non-default repository evidence or inventory.
- The final streaming brain sends the composed prompt to the **selected** local model. The model never grants itself access or executes code by reading evidence.
- ChatHistoryStore is a separate live bounded journal, currently 50 conversations and 125 messages with blank project_id in all 50, as verified by the owner. It is already read by conversation recall.
- HistoryArchiveV1 is an opt-in separate long-term journal, NOT live: owner's PC reports no history_archive.sqlite3 and both archive flags OFF. archive_first_sync requires explicit project provenance, so do NOT enable with legacy blank-project history.

## Confirmed limitation

The owner asked to search UI button code across repositories. Existing `named_repo_scope` recognizes named repository or inventory intent, but generic cross-repository code questions default to ORION-V3. The source trace showed injected=true and lookup=hit, but irrelevant paths. This is a selection/relevance defect inside the existing entry path, not proof of a broken Gitea connection.

## Required implementation discipline

1. Preserve existing `/api/local-hand/draft` and selected-model API. No second chat API, no model-specific routing architecture.
2. Preserve frozen memory, Gitea grounding, verifier, STOP, and TheHands. Add only minimal, independently qualified routing/observability changes at the existing composition boundary when evidence requires them.
3. Search ONLY explicitly owner-authorized repositories. Inventory visibility is not authorization. A generic plural question must not silently search every visible repository.
4. Keep independent databases and their trust/provenance policies. One chat route means one coordinated request/response, not one merged SQLite file.
5. Do not turn on history archive until owner-delete replay, blank project migration policy, sync atomicity, Android/PC parity and restoration have physically passed.
6. Prove real Qwen output with exact citations, live trace, authorized repo scope, selected model and no fabricated search or tool execution before declaring PASS.
7. Experimental `qwen_readonly_investigation_candidate_v1.py` and `qwen_gitea_investigation_bridge_candidate_v1.py` on this feature branch are NOT adopted, wired or approved. Do not deploy them.

**Source-level verification:** inspected `product_server.py`, `canonical_memory_integration.py`, `document_chat_connector_v1.py`, `gitea_chat_brain_v1.py`, `gitea_multi_repo_chat_v1.py`, `history_archive_sync_v1.py`. This is not a live runtime PASS.
