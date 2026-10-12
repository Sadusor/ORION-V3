# ORION V3 CodeSpace and autonomous cloud workflow — roadmap checkpoint (2026-10-12)

## Authority and separation
- Qwen local = conversational coordinator and intent proposer, NOT approval authority.
- ORION = policy, canonical state, budget, approval, STOP, verification.
- ORION internal Hands/executor = bounded execution only after Windows isolation/STOP qualification.
- TheHands- = separate external development/test remote; do not merge into ORION.
- Forge CodeSpace = PC code drafting, proposed diffs and review, NO direct writes, deletes, shell, executable preview, or generated code execution.
- Android = Qwen conversation, task progress, approval/STOP surface, and remote CodeSpace open request; no Forge clone.
- All frozen modules remain untouched.

## Actual proof / status
1. Existing policy, memory, council and work-loop modules: multiple independent physical regression PASS records. NOT an end-to-end autonomous loop.
2. Forge projection V1: physical 7/7 PASS, frozen.
3. Forge static HTML adapter V1: physical 7/7 PASS, frozen.
4. Forge staging V3: physical 12/12 PASS and JS syntax PASS, frozen candidate. Chrome produced a valid 1440x900 screenshot, visually inspected by owner/assistant; interactive controls not yet verified.
5. CodeSpace open + cloud role contract V1: candidate source and 12 tests committed; NOT YET PHYSICALLY TESTED. This is a pure contract, not an actual window opener or model adapter.

## Next milestones (in order)
A. Physically GITCHECK CodeSpace open contract and freeze only on PASS.
B. ORION dark theme applied as a NEW Forge candidate; retain three-pane layout and review-only behavior.
C. Standalone ORION-owned Windows window/WebView2 host; do not require external Chrome; test launch/focus/STOP and non-execution.
D. Wire PC button and Qwen chat intent to one authenticated `codespace.open` host action; Android requests routed to connected PC; report actual launch result. No pretend success.
E. Read-only authenticated task/project projection from canonical ORION/Gitea; separate staged diffs and ORION authorization; verify source provenance.
F. First real **free cloud** coder + independent reviewer through existing provider adapters. Qwen coordinates, ORION applies budgets, free tier enforced, fail closed on exhaustion. Collect code proposals, reviews, task ledger and verification evidence. Do not execute generated code until isolation qualification.
G. Qualify Windows filesystem/network isolation and process-tree STOP physically. Only then enable bounded generated-code execution under ORION gates.
H. Run a small end-to-end project with evidence and regression; freeze successful modules.
I. Add a paid provider **only with explicit owner authorization and spending caps**; preserve same coder/reviewer contract, swap models without changing ORION authority.

## Current risk
CodeSpace open and cloud routing V1 are **pure decisions only**. The provider routing contract is not a provider connector, does not measure live quotas, and cannot guarantee that a model is actually free. Host UI and live model execution remain separate milestones.
