# ORION V3 — Grounded Source Chat Acceptance / Freeze (2026-10-11)

## Owner decision
**FREEZE — do not edit the accepted grounding path or any earlier proven/frozen module.**
Any future capability must be built separately and attached through a minimal, owner-approved integration hook. No refactor, cleanup, routing rewrite, or keyword patch of accepted components.

## Accepted implementation
- ORION source: `6c3680101e003d657acc28b01a6ec3741d2115e2`.
- Existing read-only MyGitea2 index + UniversalRetrievalV1 integration, source-reference formatting and provenance-only trace in `src/orion_v3/modules/gitea_chat_brain_v1.py`; `product_server.py` default-ORION routing.
- Evidence from TheHands `42e5a2d72b99`: `SOURCE_LINE_BOUNDARIES PASS`, `IMPLEMENTATION_EVIDENCE_PRECEDENCE PASS`, `TRACE_COMPATIBILITY PASS`, `ORION_GROUNDING_FORMAT_GITCHECK PASS_SOURCE`.
- Previous live source trace: `lookup=hit`, `injected=true`, `source_errors=[]`, authoritative source ID `a4a4b8d3539cc10148930cba46527e0af3dc5870:ui/strata/modules/history-integrity-v1.js:0`; source was attached to assembled prompt, not proof of model compliance.
- Owner physical live acceptance after updating ORION: Qwen correctly explained History Integrity V1 placeholder detection, warning rendering, read-only behavior and absence of Git-branch security claims, citing `ui/strata/modules/history-integrity-v1.js` at source commit `a4a4b8d3539cc10148930cba46527e0af3dc5870`. **PHYSICAL ANSWER PASS**, not a general guarantee across all questions.

## Scope and non-goals
- Frozen: accepted Gitea grounding wrapper, formatting, prompt citation/tracing, frozen canonical memory, history integrity, STOP/approval. TheHands remains a separate, frozen product.
- Not yet accepted: end-to-end natural-language document/database lookup, general multi-source retrieval evaluation, retrieval correctness on all prompts.
- 50 historical conversations were observed in the default project scope; `orion-v3` explicit recall scope returned no hits. Do not rewrite project associations or bypass access scope.

## Next work
Create isolated document/database retrieval adapter over existing `DocumentIndexV1` and `UniversalRetrievalV1`. Make no changes to frozen components without a separately scoped owner decision. Prefer a standalone adapter + tests first; do not imply live chat wiring is proven.
