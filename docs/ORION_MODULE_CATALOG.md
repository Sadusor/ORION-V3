# ORION V3 — Module Ownership Catalog

Updated 2026-10-11. Based on the GitHub main repository tree; category placement is organizational, **not proof of runtime use**. This document moves no code and does not authorize changing frozen components.

## Invariant and current integration checkpoint

**Chat → project-scoped indexed retrieval (memory, MyGitea2, documents when connected) → provenance validation → Qwen → existing verifier → UI.** Indexed content remains context-only; no implicit promotion to canonical memory. The live deployment last reported by owner was commit `a3ce320d2ef680f739576c905f76826dae2387e5`; the later keyword routing commit `2192cdc` has **not** been deployed or accepted as architecture. Current work: unify retrieval behind the existing `UniversalRetrievalV1` façade and preserve memory / STOP boundaries.

**Freeze policy:** After complete end-to-end PASS, freeze the module. No broad edits to already frozen Memory V1/V1.1 or canonical approvals, STOP, work loop, remote V1 or separate TheHands product. A source-only test is not runtime qualification.

## Existing Python modules — primary logical owners

### 01 MEMORY / CANONICAL

- `src/orion_v3/modules/canonical_memory_integration.py`
- `src/orion_v3/modules/canonical_memory_retrieval_foundation.py`
- `src/orion_v3/modules/memory_auto_candidate.py`
- `src/orion_v3/modules/memory_candidate_queue.py`
- `src/orion_v3/modules/memory_conflict_suggestions.py`
- `src/orion_v3/modules/memory_consolidation.py`
- `src/orion_v3/modules/memory_historical_query.py`
- `src/orion_v3/modules/memory_integrity_anchor.py`
- `src/orion_v3/modules/memory_review_promotion.py`
- `src/orion_v3/modules/memory_shadow_audit.py`

### 02 INDEXED RETRIEVAL

- `src/orion_v3/modules/memory_indexed_retrieval_v2.py`
- `src/orion_v3/modules/memory_retrieval.py`
- `src/orion_v3/modules/universal_retrieval_v1.py`

### 03 KNOWLEDGE SOURCES

- `src/orion_v3/modules/document_index_v1.py`
- `src/orion_v3/modules/gitea_auto_index_v2.py`
- `src/orion_v3/modules/gitea_brain_adapter_v1.py`
- `src/orion_v3/modules/gitea_chat_brain_v1.py`
- `src/orion_v3/modules/gitea_code_index_v1.py`
- `src/orion_v3/modules/gitea_codebase_map_v1.py`
- `src/orion_v3/modules/gitea_qwen_context_v1.py`
- `src/orion_v3/modules/gitea_readonly_v1.py`
- `src/orion_v3/modules/gitea_relevance_v2.py`
- `src/orion_v3/modules/gitea_search_context_v1.py`
- `src/orion_v3/modules/gitea_search_service_v1.py`
- `src/orion_v3/modules/gitea_source_context_v1.py`
- `src/orion_v3/modules/gitea_source_context_v2.py`
- `src/orion_v3/modules/orion_project_context_v1.py`

### 04 CHAT & AI

- `src/orion_v3/modules/brain_pipeline.py`
- `src/orion_v3/modules/chat_history.py`
- `src/orion_v3/modules/local_brain.py`
- `src/orion_v3/modules/memory_brain_pipeline.py`
- `src/orion_v3/modules/streaming_brain_pipeline.py`
- `src/orion_v3/modules/streaming_local_brain.py`

### 05 VERIFICATION

- `src/orion_v3/modules/conversation_verifier_v1.py`
- `src/orion_v3/modules/conversation_verifier_v2.py`
- `src/orion_v3/modules/verifier_preflight.py`

### 08 RUNTIME

- `src/orion_v3/modules/update_manager.py`

### 06 AUTONOMOUS WORK LOOP — preserve isolation

- `src/orion_v3/work_loop/__init__.py`
- `src/orion_v3/work_loop/authorization.py`
- `src/orion_v3/work_loop/calculator_simulation.py`
- `src/orion_v3/work_loop/commit_coordinator.py`
- `src/orion_v3/work_loop/contracts.py`
- `src/orion_v3/work_loop/coordinator.py`
- `src/orion_v3/work_loop/dry_run.py`
- `src/orion_v3/work_loop/engine.py`
- `src/orion_v3/work_loop/evidence_gate.py`
- `src/orion_v3/work_loop/executor.py`
- `src/orion_v3/work_loop/independent_observer.py`
- `src/orion_v3/work_loop/nonce_store.py`
- `src/orion_v3/work_loop/observer.py`
- `src/orion_v3/work_loop/owner_input.py`
- `src/orion_v3/work_loop/paths.py`
- `src/orion_v3/work_loop/policy.py`
- `src/orion_v3/work_loop/read_verification.py`
- `src/orion_v3/work_loop/sandbox_srt.py`
- `src/orion_v3/work_loop/simulated_hand.py`
- `src/orion_v3/work_loop/stop.py`
- `src/orion_v3/work_loop/transaction_identity.py`
- `src/orion_v3/work_loop/vault.py`
- `src/orion_v3/work_loop/vault_lock.py`
- `src/orion_v3/work_loop/vault_transaction.py`
- `src/orion_v3/work_loop/verifier.py`

### 07 INTERFACES

- `ui/strata/bridge/mock-bridge.js`
- `ui/strata/bridge/normalize.js`
- `ui/strata/bridge/real-bridge.js`
- `ui/strata/bridge/routes.js`
- `ui/strata/modules/chat-history.js`
- `ui/strata/modules/chat-reading-controls-v1.js`
- `ui/strata/modules/conversation-controls-v2.js`
- `ui/strata/modules/history-integrity-v1.js`
- `ui/strata/modules/live-brain-chat.js`

### 08 RUNTIME AND TESTS

- `src/orion_v3/product_server.py` — live HTTP route and pipeline creation
- `scripts/`, `tests/`, module-level `*_test.py` — build/deployment and acceptance evidence, not candidates for deletion

## Verified live composition and known gaps

- `product_server.py` constructs `CanonicalMemoryIntegratedBrainPipeline(brain=GiteaChatStreamingBrain(), recall=MEMORY_RETRIEVAL, durable=MEMORY_CONSOLIDATION, history=MEMORY_HISTORY)`.
- Its `/api/local-hand/draft` starts the canonical memory pipeline; the Gitea request context is currently enabled conditionally via question detection or `gitea_search` request flag.
- `GiteaChatStreamingBrain.start` receives that context and calls `search_live_gitea_v2` when present.
- No `UniversalRetrievalV1` reference was found in the inspected product-server/live wrapper source. Universal discovery is **not yet on the normal chat path**.
- `memory_indexed_retrieval_v2.py` is read-only candidate-ID lookup; candidates must be validated against canonical provenance and supersession before being used.
- `document_index_v1.py` provides an FTS document index, not proof of automatic general database ingestion.
- `gitea_source_context_v1/v2`, `gitea_search_context_v1`, and `gitea_qwen_context_v1` are **not** safe to merge or delete based on naming alone: they can have different extraction, sanitization and rendering roles.

## Consolidation candidates — by orchestration, not file deletion

| Batch | Existing pieces | Goal / acceptance | Status |
|---|---|---|---|
| A — Chat + indexed knowledge | `universal_retrieval_v1`, existing scoped memory retrieval, `gitea_auto_index_v2`, `gitea_chat_brain_v1`, product server | All normal chat turns retrieve from permitted indexed sources; trace what reached Qwen; E2E question about History Integrity V1 is correctly answered | **Not connected / pending** |
| B — Ingestion | `document_index_v1`, durable-source projections, repository index and eventual DB catalog/records | Imported supported content becomes discoverable; verify freshness, deletion, IDs and source permissions | **Partial; DB unproven** |
| C — Chat answer / Revise quality | `conversation_verifier_v2`, live chat UI, response identity and audit | Answer quality, stale-turn guards, truthful statuses and no execution authority leak | **Source-only PASS; E2E pending** |
| D — Work loop | `work_loop/` | No change as part of knowledge retrieval | **Isolated** |

## Maintenance rules

1. New modules must have one primary category, an explicit call site, provenance/trust boundary and named end-to-end acceptance check.
2. Do not create a new retriever or prompt assembler while an existing one can be wired by an adapter.
3. Do not confuse a search index with canonical memory; no imports auto-promote.
4. Record source commit, actual running commit, real output and PASS/FAIL separately.
5. Physical Python package moves require import, packaging and Windows/Android regression qualification; **do not move files during integration**.
