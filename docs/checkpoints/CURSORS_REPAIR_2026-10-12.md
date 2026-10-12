# Cursor's Repair — ORION V3 everyday chat and evidence
Date: 2026-10-12
Status: OWNER-LOCKED REPAIR PLAN; INSPECT-ONLY DIAGNOSIS; NOT IMPLEMENTED
Canonical roadmap: [docs/ROADMAP.md](../ROADMAP.md), section CURRENT REPAIR LOCK — CURSOR'S REPAIR.

## Source and boundaries
This plan is derived from the owner's two pasted Cursor repository-inspection reports. Cursor reported no code rewrites. The plan must not be mistaken for runtime proof. No new chat route, new Understanding V2, arbitrary DB reader, or premature donor install. TheHands is a separate frozen engineering remote; internal ORION Work Hands remain unproven and execution-disabled. Preserve frozen memory, MyGitea2, Gitea SQLite, V1 Remote, approvals, STOP, canonical state and verifier authority.

## Root causes Cursor reported
- `named_repo_scope` sees only the current question (first 500 chars); ORION-V3 default chat path in `gitea_chat_brain_v1.py` searches raw first 300 chars, skipping `orion_understanding_v1.interpret`; named/cross-repo path calls it. This makes casual questions miss.
- Visible MyGitea repositories (Cursor counted 109) are not the same as owner-authorized search. Default catalog permits only MyGitea/ORION-V3 and MyGitea/PayDay. Other repositories require explicit catalog approval; never auto-grant.
- `.sql` is mapped as code but excluded by `gitea_auto_index_v2.py` and `gitea_multi_repo_v1.py` indexing allowlists. Git schemas therefore can be absent from FTS. No live SQL database reader exists; never conflate Git schema text with live database state.
- Older checkpoint citations may be stale relative to current default branch; pin source evidence to commit SHA and disclose freshness.
- Verifier should see exact excerpts delivered to Qwen, assess the owner's question, and permit unsupported/unknown answers rather than invent.
- Persistent document library and chat upload/restart proof remain open; older module catalog/STATUS are out of date.
- Separate recorded live error: `Local Brain request is too large; limit is 16 KiB`. Exact guard not yet traced; do not remove it blindly.

## Repair order and acceptance
1. Trace and fix the request-size overflow at the existing canonical chat boundary; bound history+retrieved excerpts without losing latest question. Make normal-language default ORION questions pass through the existing interpreter without granting repository access.
2. Index `.sql` in existing allowlists; verify with actual authorized Git schema, file path, commit SHA and FTS evidence. No live DB SQL reader.
3. Keep repository inventory separate from approved search; confirm branch SHA and freshness for roadmap/code answers.
4. Feed verifier exactly the retrieved excerpts Qwen received; assess owner question and allow evidence-absent result.
5. Follow document lane: persistent library across restart, upload, fan-out, Greek/English semantic retrieval, live update.
6. Batch regression and read-only real-index checks through TheHands; deploy only via controlled candidate and backup/rollback. Physically test PC and Android using the owner's own words, long chat, scrolling/copy, cited source path+commit, revise after turn. Only then update STATUS and module catalog and freeze passed changes.

## Donor review decision
Inspected fork sources: Haystack InMemoryBM25Retriever delegates to InMemoryDocumentStore (not an automatic SQLite FTS backend); Zoekt parser is Go and requires its own search/index integration; Ragas faithfulness requires an LLM evaluator; DSPy signatures and Semantic Router are not substitutes for broken routing. Do not add a framework merely to fix bypassed existing wiring. Benchmark and borrow proven code only where it demonstrably improves the existing pipeline.

## Proven vs unproven
- TheHands 23/23 tests and three-file deployment to Windows candidate were recorded PASS (session 1b6c6808dc1a). This does NOT demonstrate live Qwen success.
- Live user recording showed 16 KiB rejection and missing authorized evidence; root causes need controlled tracing.
- This checkpoint is documentation only. No code fix, DB scope expansion, runtime restart, or donor integration has been performed by this commit.
