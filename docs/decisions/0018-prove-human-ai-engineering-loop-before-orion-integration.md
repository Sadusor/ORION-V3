# Decision 0018 — Prove the existing human + AI engineering loop before ORION integration

Date: 2026-10-08
Status: OWNER CLARIFICATION / CURRENT BUILD INTENT; IMPLEMENTATION NOT YET PHYSICALLY PROVEN

## What we are actually building now

The immediate product of this phase is a **replaceable ORION V3 module/subsystem that reproduces the engineering workflow already used by the owner with ChatGPT and DeepSeek**. First prove that workflow as an isolated, bounded system. **Only after physical proof connect it to ORION V3's authority, project Vault, model adapters, Memory and PC/Android UI.**

The existing manual workflow is:
1. Owner defines a goal, constraints, and approval boundaries.
2. ChatGPT acts as engineering architect/coder/operator: inspects real code and project state, proposes one bounded change, writes/stages code and tests.
3. DeepSeek is an independent adversarial reviewer/critic when useful. Its review informs the plan; it does not approve actions or determine verified PASS.
4. TheHands (separate, frozen engineering remote) transfers the staged GitCheck task to the Windows PC, where the owner presses GitHub Check / Approve & Start.
5. Real Windows execution publishes results/evidence; ChatGPT reads the exact source commit and evidence.
6. PASS: record evidence, freeze proven module and choose next bounded task. FAIL: inspect failure, make smallest repair and rerun. Preserve state/checkpoint in GitHub so the owner does not repeatedly reconstruct context.

**First target:** reproduce and qualify this existing workflow as a module, including owner approval, reviewer handoff, GitCheck evidence ingestion, continuity and FAIL→repair→PASS. Do not substitute a new autonomous file-writing agent or sandbox research project for this objective. Manual human-operated steps may remain while proving the protocol; automate them incrementally only after real evidence.

## Distinct loops — never conflate

- **Engineering collaboration loop (CURRENT):** owner + ChatGPT + DeepSeek + TheHands/GitCheck. This is what the owner explicitly wants replicated and proven first.
- **Autonomous Work Loop V1 (LATER INTEGRATION TARGET):** owner -> Vault/STATE -> Qwen -> ORION policy -> confined Work Hand -> verifier -> Vault. Existing code is staged and largely simulation-only; it is NOT the current immediate product goal.
- **ORION product integration (AFTER PROOF):** attach the proven collaboration loop via replaceable adapters to existing ORION V3 services and existing PC/Android product UI. ORION remains authority and independent verifier. Do not merge TheHands product into ORION.

## Engineering constraints

- Work in ORION V3 modules, never a parallel application or a second authority/STOP/Vault/Memory/UI.
- Reuse existing modules and verified donors; preserve frozen code and Remote V1.
- Owner authorizes real operations; model text, reviewer opinion and GitCheck transport success do not themselves grant authority or prove execution.
- Real evidence must bind task, source revision, execution, outcome and reviewer/owner decisions; distinguish GitCheck script PASS from intended functional proof.
- Minimize idle CPU/GPU and avoid heavy permanent agent loops.
- Separate tests for proposal/review, staging, approval, execution, evidence retrieval, continuity and recovery before a full integrated proof.
- Keep experimental Windows isolation work archived/paused; no blanket claim that network confinement passed.
- No production real-execution activation from this documentation decision.

## Next bounded module work

1. Finish repository/documentation and actual code-interface audit, including existing TheHands remote/GitCheck path and ORION project state.
2. Map **existing engineering loop stages** to current modules and classify EXISTS / PARTIAL / MISSING / REUSE, with exact file paths and callable interfaces.
3. Implement the **smallest missing replaceable adapter** for a real owner-approved, GitCheck-backed task/review/evidence cycle; do not change frozen TheHands product internals.
4. Physically qualify one PASS, one FAIL→fix→PASS, owner approval, restart/continuity and truthful evidence. Freeze only what was proven.
5. Then connect the proven subsystem to ORION V3 Work Loop, Vault and UI through their existing contracts, keeping ORION authority.

## Documentation precedence

This owner clarification supersedes any statement that *immediate* priority is an autonomous Qwen→AppContainer append-line execution test. Those tests remain optional **later** Work Loop qualification gates, not the primary current build objective. Older roadmap entries remain historical; do not erase them. This decision is not a claim that the full repository has been read or that implementation is complete.

## Audit progress and remaining scope (truthful)

GitHub tree at commit `17809e6da14f7a26514ca5a51f464d13406ef857`: 436 entries, 364 blobs, 3.75 MB tracked, tree not truncated. Reviewed full canonical operator brief, freeze rule and Autonomous Work Loop specification; read core roadmap/architecture/status and inspected key runtime, Android, UI, Work Loop and Vault code. Retrieved the first twelve `docs/` Markdown blobs in the documentation sweep. **This is NOT a completed full-file, whole-repository audit.** Remaining Markdown/reference/evidence documents and source/tests still require exhaustive review, with findings reconciled to the active engineering collaboration objective. No new real-execution permission was enabled. Future operator must not infer a full audit from the tree inventory.
