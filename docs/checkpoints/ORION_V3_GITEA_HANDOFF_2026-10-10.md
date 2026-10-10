

## CURRENT VERIFIED HANDOFF — 2026-10-10 evening (read this before historical entries)

**Purpose.** ORION V3 is the owner's local Windows/Android everyday assistant and controlled development environment. Qwen local 9B provides chat and proposals; ORION deterministic code remains responsible for authorizations, STOP, verification and canonical memory. Original PC/phone chat remains the interaction surface. MyGitea2 is the owner's local forge and read-only knowledge source for Qwen; GitHub is a separate upstream/backup. Cloud specialist DeepSeek Flash is a future integration, not operational today.

**TWO DISTINCT HANDS CONCEPTS — do not conflate them:** (A) ORION **internal Work Hands** are the proposed/built-in bounded execution path inside the ORION-V3 repository, subject to independent policy, Windows confinement, approval and STOP qualification; never assert autonomous execution is proven until an evidence run proves it. (B) **TheHands** (Sadusor/TheHands-) is an independent, previously working, now frozen Windows/Android remote for owner-approved testing and PowerShell GIT CHECK. It is NOT the next evolutionary agent architecture, NOT to be modified for ORION except owner-authorized test slot staging, and NOT integrated as the ORION execution runtime. If a user asks "what are the hands?", distinguish the two, or clarify ambiguous wording.

**Physical evidence (not invented status).** TheHands test sessions: `5c8e7b3f90fe` 41/41 Gitea bridge contracts; `20c93635ca1a` physically retrieved checkpoint/roadmap from MyGitea2 pinned branch; `ae8961b6e809` candidate Windows UI/backend launched at commit `42d2111b`; `1afb4bf38d2b` 47/47 chat/UI static and context tests; `e3b9a9892dd2` native desktop rebuild at `ab5691a2`; `b7a9534e071b` 49/49 Gitea and prompt-budget tests at `5107a7b5`. The latest chat prompt fix is **code-qualified**, but live candidate deployment must be separately checked before claiming runtime PASS. Previous FTS5 `def` live failure was a **historical failed gate**, not proof that all current MyGitea2 retrieval remains broken: later real checkpoint document retrieval and Qwen answer were observed. Do not claim fully functioning universal multi-repo live search based on document retrieval alone.

**Actual conversation observations.** Qwen answered "What is ORION and how far are we on the roadmap?" with structured project knowledge, but relied on an older pinned checkpoint. In a separate question about "thehands", Qwen composed ambiguous/excessive claims about autonomous agent capabilities and future work; ORION semantic verifier blocked the draft with FAILED VERIFICATION. The verifier correctly flagged unsupported statements but conflated missing evidence with a conclusive falsehood and did not disambiguate internal ORION Hands versus separate TheHands. "Ask Local Brain to revise" returned a capability-not-connected error in the screenshot. Do NOT represent the revise control as operational.

**Verified source fixes awaiting full live behavior proof.** ORION chat UI code includes longer Qwen output cap (4096 tokens), selective scrolling and Copy Response UI. Gitea prompt-integration now bounds reference material after memory composition to fit an existing 16 KiB byte admission limit, with Greek/multibyte regression checks. Long conversation **history** should be persistent and retrievable; each *individual* Qwen generation has a finite context and output budget. Don't remove safety admission limits or claim literal unlimited context. Frozen canonical Memory V1, V1.1 and Indexed V2 untouched.

**Next bounded work after publishing this checkpoint to local MyGitea2:** (1) verify running candidate source/version and ask Qwen to explain both Hands with correct Gitea provenance; (2) make factual conversational review separate from deterministic command/authority gates; allow uncertainty notes and targeted correction of questionable claims, while blocking fabricated actions and unsafe execution; (3) ensure semantic verifier can see provenance/context actually used by Qwen and does not treat owner message alone as the universe of evidence; (4) verify real chat copy/scroll/long-output on PC and phone; (5) build freshness-aware retrieval/checkpoint sync (no forged PASS, no privileged promotion of repository text). Work in independently tested modules, freeze on PASS; do not change frozen bases or MyGitea2 application.

**Checkpoint freshness rule:** MyGitea2 `MyGitea/ORION-V3` pin `orion-checkpoint-20261010` was historically at `96aaceb70741b99a606282ae5a35c6f6a3059a28`. It does not automatically track GitHub. Publish this documentation to the pinned branch via normal fast-forward Git only after the latest source tree is consistent; verify the resulting remote commit explicitly. Until then Qwen may cite a stale roadmap. Never assert a push to MyGitea2 without TheHands local push evidence.

---

# ORION V3 — Gitea publication and Qwen progress test

Checkpoint date: 2026-10-10. This is a factual handoff, not an authority grant.

## What we are building
The existing ORION PC/Android app is the owner interface. Qwen local 9B coordinates development and project questions. ORION deterministic authority owns scope, approvals, STOP, immutable provenance, verified outcome and canonical memory. DeepSeek Flash is the intended first specialist for generating code proposals, **not yet integrated**. ORION's own internal Work Hands will eventually apply authorized edits, test and Git-push them to local MyGitea2 when Windows isolation and STOP qualifications pass. TheHands is a DIFFERENT frozen remote product used for testing. Codespace is strictly a display/evidence UI, never another agent. Existing frozen Memory V1/V1.1/Indexed V2 must not be edited.

## MyGitea2
Local server: http://127.0.0.1:3001, Gitea 1.27.1; E:\MyGitea2. User manual: Sadusor/MyGitea2/windows/GITHUB_SYNC.md and control script. MyGitea2 application itself was frozen; publishing a new ORION-V3 Git branch is separate from modifying Gitea server source/config/SQLite. Its GitHub import is not continuous sync. Use exact commit from local repository, not assumed GitHub parity. No direct database access.

## New ORION-V3 components — all in separate modules
1. src/orion_v3/modules/gitea_readonly_v1.py — loopback-only REST GET, repository/branches/tree; mock contract.
2. src/orion_v3/modules/gitea_codebase_map_v1.py — bounded project/source tree map, exact commit provenance.
3. src/orion_v3/modules/gitea_source_context_v1.py — pinned file text reader with file-size/path restrictions.
4. src/orion_v3/modules/gitea_qwen_context_v1.py — explicit project/repository binding and context-char budget.
5. src/orion_v3/modules/gitea_brain_adapter_v1.py — opt-in wrapper with MyGitea2 operating guidance; NOT activated in running app.
6. src/orion_v3/modules/gitea_code_index_v1.py — separate SQLite FTS5 code index with project/repository/commit scopes; no modification to frozen memory.
7. src/orion_v3/modules/gitea_search_context_v1.py — render bounded retrieved snippets as untrusted reference text.
8. src/orion_v3/modules/gitea_search_service_v1.py — trial fetch/index/search service, currently limited to first 40 selected files and not proven successful against a live search query.
9. src/orion_v3/product_server.py — optional read-only Gitea context-preview route committed, not live-qualified or started in original PC app.
10. tests/test_gitea*_v1.py — isolated regression tests.

## Physically verified results (TheHands result branch evidence)
- b7dfc1c51f09: local server Gitea 1.27.1, 127.0.0.1:3001 GET PASS.
- 3df5af96c917: first page of 50 visible local repositories PASS.
- 0d7a4ee27a62: actual MyGitea/ORION-V3 tree commit be618edb8cd40a7e5da0210ef1b4599a0cfbf220 mapped to 269 source/docs files.
- 85ba347178fa: actually read android/scripts/check_screen.py, 1368 chars, same local commit; 13/13 contract tests PASS.
- 4a87c2a12855: 17/17 tests PASS, project-scoped Qwen context builder.
- 8062926b2840: 21/21 tests PASS, optional Gitea brain wrapper.
- 2e9ff852db31: 24/24 tests PASS, backend preview route contract.
- b756c319af74: 24/24 tests and live Qwen-context assembly PASS.
- f829a4d7f5f0: 30/30 PASS SQLite FTS5 mock-backed tests.
- 38f0ce13672c: 34/34 PASS Gitea search prompt-context tests.
- 2537aad3b6e1: **37/37 PASS** including fake-Gitea search service.
- e822eb76e79b: **LIVE SEARCH FAIL**, real 39 files indexed but query `def` produced 0 hits. Treat this as an open failure; no genuine indexed multi-repo Qwen search has been demonstrated.

## Other milestones that remain valid
PC + phone original ORION chat/UI, paired remote, local Qwen 9B, chat history and canonical memory path have earlier physical proofs. Existing frozen memory must not be rewritten. ORION work-loop research and STOP/Vault checks do not imply autonomous writes are ready. TheHands separate Windows/Android product was frozen. GitHub exists as upstream source and backup. Do not infer production deployment from developer checkout tests.

## Current blockers and next actions
- Real code search: expand bounded source coverage and use known indexed terms; measure keyword search speed and validate actual paths/commits. Avoid testing guessed words in a subset.
- Connect search to the real Qwen chat AFTER canonical memory prompt composition, not via a wrapper that gets replaced by the frozen memory composer. Validate client owner message, project scope, verifier and STOP remain intact.
- Backend rollout: end-to-end HTTP read-only endpoint test, then staged original PC runtime update with rollback and phone query.
- Wider repos and private access: approved credentials handled by Windows owner vault, never prompts/logs.
- Internal ORION Work Hands commits/pushes: remains disabled until real Windows isolation, independent verification and owner authorization pass.

## Qwen milestone acceptance test
Ask Qwen in the ORIGINAL ORION app:
“Read the ORION-V3 project in MyGitea2 using repository search and the current ROADMAP.md, STATUS.md, this checkpoint, and relevant code. Tell me where ORION V3 stands, what has been physically verified versus only coded, what failed most recently, and the next three practical steps. Cite exact Gitea repository paths and commit SHA for each important claim. Do not write or change anything. If Gitea search is not available in this running app, say so explicitly instead of guessing.”

Independent evaluator must compare claims with Gitea commit contents and TheHands evidence, including that 37/37 mock tests PASS but live FTS5 search FAIL and no production Qwen wiring. Passing requires correct distinctions and source paths/commit; not mere confident narrative.

## Publication safety
Publish the entire ORION-V3 repository state as a **NEW non-force Git branch** in MyGitea2 (e.g. orion-checkpoint-20261010), verify remote ref commit, do not overwrite existing local Gitea `main`. Normal owner-driven promotion/merge to main is later; Qwen test must explicitly point to the published branch if not merged. Preserve original ORION PC app and TheHands runtime untouched.

## 2026-10-10 publication failure and conversational Qwen requirement
Owner explicitly requires **the existing ORION PC and Android chat interface** for the final test. No separate CLI chatbot, raw search box, filenames supplied by owner, or canned one-shot status screen qualifies. Qwen must converse naturally about ORION-V3 project status, infer the repository search intents from ordinary owner questions, retrieve source/roadmap/evidence in bounded project scope, retain follow-up context and explain what is verified versus planned/failed. Answers need real Gitea paths, source commit and evidence; source text cannot confer authority. Verifier must not treat unsupported claims as PASS.

Publication session `bac01c88b80f` failed: `git push` to `http://127.0.0.1:3001/MyGitea/ORION-V3.git` returned authentication failure. GitHub source commit `779580853d4154efca9424eb2e90592a96496387` is preserved. No Gitea branch publication verified; `main` unchanged. Existing UI-stored DPAPI Gitea API key does not automatically provide Git command-line credentials. Remedy using a dedicated authorized Git credential pathway; never put tokens in chat, command text, logs or Git remote URL. Re-test on new non-force branch, verify SHA. The running ORION app has NOT been updated or conversationally qualified.

## Document Knowledge V1 — staged, not deployed (2026-10-10)
Owner requested natural PDF/document uploads through the existing ORION PC/Android chat, with indexed retrieval combined at answer time with separate frozen canonical memory and Gitea code knowledge. New disposable sidecar `src/orion_v3/modules/document_index_v1.py` uses SQLite FTS5, explicit project scope, document digest, filename and PDF page/chunk provenance. Supports UTF-8 TXT/MD/CSV/JSON/PY/LOG; PDF text extraction requires optional PyMuPDF at runtime, and scanned PDFs/OCR are not yet supported. Tests in `tests/test_document_index_v1.py`. Data is `untrusted_document` and `context_only`; canonical Memory V2 source remains untouched. **Still missing:** authenticated attachment upload UI/backend, controlled file persistence, DOCX extraction, read-after-ingest checks, post-memory retrieval fusion into Qwen, and actual running-app update. This is a module qualification stage, not a deployed capability.

Previous physical PASS: TheHands session `5c8e7b3f90fe` 41/41 Gitea chat bridge/source tests, ORION source `58f97655d9c6e9ea67ea0ba7d9aa53a57992d023`. Running ORION app untouched. Next test source staged in TheHands task `a030171910054541068991b6bedb70ca93a0a798`, 41 existing plus 7 document tests. This code is NOT yet republished to local MyGitea2 checkpoint branch.
