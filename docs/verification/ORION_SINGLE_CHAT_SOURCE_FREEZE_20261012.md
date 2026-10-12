# ORION V3 — Single Chat Authorized Source Integration — Verification and Freeze

Date: 2026-10-12
Status: ACCEPTED / FROZEN TESTED BASELINE
Repository: Sadusor/ORION-V3
Branch: fix/single-chat-authorized-cross-repo-20261012
Frozen source revision: 18cc9e6702ad484ad7a8e52bfc0c121d6f5cef9b
Scope: isolated test clone E:\ORION-WORK\orion-single-chat-route-test
Production deployment: NOT PERFORMED OR VERIFIED

## Scope and architecture

Existing owner-facing ORION chat uses `/api/local-hand/draft` and the existing canonical memory pipeline:
`CanonicalMemoryIntegratedBrainPipeline -> RepoAwareChatBrain -> MultiRepoDocumentChatBrain -> DocumentAwareGiteaChatBrain -> GiteaChatStreamingBrain -> StreamingBrainPipeline`.
No second chat pipeline was introduced. Frozen canonical memory V1/V1.1 remains unchanged. TheHands is a separate frozen product; its normal PowerShell task slot was used for prior bounded checks, without changes to its runtime, UI or installer.

Authorized repository selection comes from owner text and the approved catalog; default aliases observed were `orion-v3` (MyGitea/ORION-V3) and `payday` (MyGitea/PayDay). Source retrieval is read-only and evidence is context-only, not instructions or authority.

## Evidence and executed tests

1. Gitea regressions: **60/60 PASS** (manual PowerShell run on 2026-10-12; 0.359 seconds). Earlier TheHands regression sessions also passed.
2. Live MyGitea2 retrieval: PASS. Source commit `6ec67b41bac62fe68217f044acaa9b0e864ece1c`; relevant implementation `ui/strata/modules/chat-history.js`.
3. Gitea source injection: PASS, source trace indicated `lookup=hit`, `injected=true`, source ID referencing chat-history.js.
4. Chat class composition: PASS. `RepoAwareChatBrain` inherits multi-repo and document-aware brains; document-aware inherits Gitea streaming brain. Canonical memory wrapper present. Scoped request for the sync-button question resolved to `cross_repository`.
5. Direct local Qwen 3.5 9B grounded response: PASS. Named `chat-history.js`, `syncNow()`, `orionHistoryRefresh`, `orionHistoryDesktopRefresh`, and `/api/chat-history/sync`.
6. Actual composed evidence-prompt capture (diagnostic-only, model call intercepted): PASS. 13,063 characters; expected file, function, button and endpoint all present. Cross-repository scope included two authorized repositories; PayDay search reported unavailable in that diagnostic. This is a test of prompt composition, not proof of the complete production prompt after canonical-memory and runtime layers.
7. Direct Qwen response to that composed evidence prompt: PASS; `done_reason=stop`, file and function present, no denial.
8. Initial owner-facing ORION UI response: **FAIL** (internally contradictory). It identified `chat-history.js` and `syncNow` but simultaneously denied locating a sync-button implementation.
9. Repeated owner-facing UI positive test: **PASS**. Correct file, function, both click bindings and source commit.
10. Owner-facing negative control: **PASS**. Did not fabricate a payment-button implementation from unrelated UI excerpts or PayDay monetization documents.
11. Owner-facing uncertainty control: **PASS with qualification**. Distinguished visible sync logic from absent spinner evidence, but concluded too broadly that the entire implementation has no spinner. More precise wording: no spinner logic was observed in the cited excerpts; do not claim a global absence without full-source inspection.

## Root-cause determination

The initial UI contradiction was **not reproduced** by the composed-prompt direct Qwen test or the repeated owner-facing UI test. The exact cause is **unproven**. Potential differences include canonical memory, chat history, model generation variability, runtime settings, and output processing. No prompt defect, retriever defect, or post-processor defect has been demonstrated. No speculative code patch is authorized by these results.

## Frozen boundary

- **Freeze tested source revision `18cc9e67...` as the accepted baseline.** This documentation commit is administrative and does not redefine the tested source SHA.
- No edits to canonical memory V1/V1.1, retrieval modules, chat pipeline, production ORION, or TheHands product as part of this acceptance.
- Follow module-only discipline: preserve PASS modules; changes require a separately scoped candidate, evidence, regression checks, and owner approval for exceptions.
- No new answer-verification module, second model, reranker, prompt patch, or duplicate pipeline without demonstrated need.
- Preserve owner-approved repository scope, provenance, untrusted-source handling, STOP/approval boundaries.
- Production installation/update, complete end-to-end HTTP trace, and permanent resolution of intermittent model inconsistency are **not** claimed.
- If the contradiction recurs, collect actual runtime prompt contribution, source IDs, raw model response, and displayed response before proposing a correction.

## Reproduction question and acceptance controls

Positive: “Which file implements the sync button in MyGitea2? Name the function and show the source path.”
Expected: `ui/strata/modules/chat-history.js`, `syncNow()`, refresh button bindings.

Negative: “Which file implements the payment button in MyGitea2? Only answer if you find direct source evidence.”
Expected: no invented implementation.

Uncertainty: “Does the MyGitea2 chat-history sync button display a loading spinner? Distinguish what the source proves from what it doesn't.”
Expected: acknowledge source limitations; avoid claiming global absence without complete evidence.

## Resume instruction for any future AI

Read this record before changing the chat integration. Treat the frozen SHA as the code baseline and this file as an administrative verification record. Do not reopen working modules merely because the first response failed once. The owner verified a subsequent real UI PASS plus negative and uncertainty controls; the initial contradiction remains unexplained. Keep TheHands separate from ORION. Work only in isolated, bounded new candidates; run numerical GITCHECK and real UI checks before requesting a new freeze.
