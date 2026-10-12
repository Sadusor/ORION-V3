# ORION V3 — Single Chat Retrieval Breakthrough and Understanding V1
Date: 2026-10-12
Status: **candidate; not frozen or deployed** (except earlier focused retrieval deployment reported PASS by owner).

## Owner's non-negotiable product contract
- ONE canonical chat route for all authorized databases: Gitea/MyGitea2, SQLite, documents, memory, and future connectors.
- All model-backed conversations present as **ORION**; underlying model identity is truthfully disclosed when asked. This does not change provider/model technical identity.
- Natural language must work without memorizing phrases or keywords.
- Preserve repository authorization boundaries; visible Gitea inventory is not permission to read all repositories.
- Frozen memory, V1 remote, and TheHands runtime remain untouched. TheHands is a separate product, used only for bounded engineering execution through its designated Hand task files.
- Do not claim PASS until real tests/evidence exist; no automatic source promotion or execution from retrieved text.

## Breakthrough: what we proved
1. Original question: 'Search MyGitea2 and tell me what UI button code exists in my repositories. Include repository names, file paths, and source references.'
2. Read-only SQLite FTS5 comparison on real PC index:
   - Original-style retrieval surfaced irrelevant docs and tests, e.g. memory_shadow_audit_product_wiring_test.py and Gitea handoff docs.
   - Targeted UI query surfaced actual UI implementations: ui/strata/modules/chat-history.js, chat-reading-controls-v1.js, conversation-controls-v2.js, live-brain-chat.js, and ui/strata/product/workspace.js.
   - **RELEVANCE_READONLY> PASS** proved the evidence existed in the index; did not prove Qwen response quality.
3. Authorized indexed repositories observed: MyGitea/ORION-V3 (324 source entries, 81 UI-related filenames), MyGitea/PayDay (12 source entries, no UI-named entries). Authorization catalog defaults to those two, optionally owner-controlled.
4. Focused query router isolated commits: 7d82be9, fe31ee0. Windows router regression passed earlier; owner later reported TheHands deployment/restart PASS.
5. Owner video: Qwen earlier denied MyGitea access; later answered with some real UI control identifiers (orionHistoryRefresh, orionHistoryDesktopRefresh, data-oh-act) and repository/file references, but also irrelevant test files and incomplete results. **Partial end-to-end improvement, not final acceptance.**
6. Root cause: broad lexical OR/FTS search and insufficient implementation-file ranking, plus model prompt conflict: the streaming local model was told not to claim searches even when ORION supplied read-only evidence. Keyword-only routing is insufficient.
7. Natural-language routing and ORION identity edits: commits 73688ce, 2d2188e, 1236406, 84bbb73. First Windows test reported FAIL. Discovered double-escaped regex word boundaries; corrected at 26f553f. Owner ran manual Windows checks at exact commit 26f553f: **9/9** single-chat tests and **8/8** multi-repo tests PASS; py_compile PASS. This proves tests only; production deploy and real conversation verification still pending.
8. Donors present under Sadusor GitHub: dspy, ragas, semantic-router, haystack, zoekt. Source inspected: DSPy signature schema, Ragas faithfulness metric, Haystack BM25 retriever, Zoekt query syntax, ORION gitea_relevance_v2 and universal_retrieval_v1. This was a targeted inspection, NOT a file-by-file audit of all five repositories.
9. Donor decisions: borrow DSPy-style structured interpretation, Haystack-style retrieval composition, Zoekt-style path/symbol scoring, Ragas-style grounded-answer evaluation; defer Semantic Router/model routing until retrieval proven. Do NOT install all frameworks or create parallel chat routes.
10. New additive isolated candidate at 8ca5bda: src/orion_v3/modules/orion_understanding_v1.py plus tests/test_orion_understanding_v1.py. This interprets request, expands concepts, and ranks implementation paths ahead of tests/docs. **NOT wired into production or proven on real PC index yet.** No donor runtime imports or authorization changes.

## Existing single chat route (preserve)
POST /api/local-hand/draft -> CanonicalMemoryIntegratedBrainPipeline -> RepoAwareChatBrain(MultiRepoDocumentChatBrain, DocumentAwareGiteaChatBrain) -> GiteaChatStreamingBrain -> StreamingLocalBrainModule._worker -> Ollama /api/generate.
UniversalRetrievalV1 is read-only, project-scoped, provenance-preserving. Do not bypass it or frozen memory.

## Next gated work
A. GITCHECK candidate commit 8ca5bda: py_compile, new understanding tests, prior 9+8 tests, read-only relevance comparison on the real SQLite index. No deployment/restarts.
B. Inspect failure output, repair only candidate module/tests if needed, repeat gate.
C. If PASS, propose additive adapter wiring into existing route (no second route) and test source ranking with real index and citation preservation.
D. After owner-approved deployment, test multiple ordinary conversational requests against actual Qwen. Verify ORION identity, correct repo/file/commit citations, authorization, no fabricated access, and absence of irrelevant tests/docs. Run regression suite, freeze/document only after acceptance.
E. Other model/provider adapters require separate identity audit; the local model prompt change alone does not prove all models comply.

## Evidence and failure distinctions
- 17/17 tests PASS at 26f553f; **not** proof of actual Qwen answer quality.
- Earlier owner-reported restart PASS applies to earlier focused-retrieval deployment, not 26f553f or 8ca5bda.
- No claims that five donor frameworks have been merged, or that the understanding candidate has been installed.
- Frozen modules and TheHands runtime must remain unchanged.
