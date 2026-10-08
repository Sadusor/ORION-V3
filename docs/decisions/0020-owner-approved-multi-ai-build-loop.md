# Decision 0020 — Owner-approved multi-AI architecture and build loop

Date: 2026-10-09
Status: OWNER-APPROVED TARGET ARCHITECTURE / IMPLEMENTATION NOT YET QUALIFIED

## Non-negotiable product workflow

1. Owner describes a project and acceptance criteria.
2. At least two distinct cloud AI models independently brainstorm solutions from the same task context. Neither sees the other's initial answer.
3. Both cross-review proposals, challenge assumptions, identify risks and propose a build plan. ORION records unresolved disagreements; it never manufactures consensus.
4. Owner sees the plan, disagreements, proposed modules, scope, tests, costs and risks and approves an exact immutable plan digest or requests revision.
5. Cloud AI models cooperatively write implementation patches and review each other's changes. Their outputs remain untrusted proposals.
6. Local Qwen is an optional low-consumption interpreter/coordinator for bounded actions; it is NOT the primary code author, security authority or source of PASS.
7. ORION's native Work Hand applies only explicitly authorized, validated patches in a qualified confined workspace, executes allowed build/test commands, and collects independent evidence.
8. Failed tests and diagnostic evidence go back to the cloud models for bounded repair rounds; ORION validates fresh patches and approvals and independently retests.
9. ORION owns task state, roadmap, policy, authorization, STOP, verifier, Vault, evidence, continuity and memory candidate provenance. The owner owns decisions.

## Current verified foundation

- Three cloud reviewer outputs -> local qwen35-9b-orion synthesis: physical advisory PASS, session e00f23a8b5c0. No owner approval or execution in that run.
- Existing ORION native src/orion_v3/work_loop/engineering_cycle.py implements one proposal, one review and owner digest approval, not a multi-model debate.
- Existing coordinator.py uses SimulatedWorkHand only; no native execution qualification.
- The 45 passing Task Ledger static/HTTP synthetic tests are test-infrastructure evidence, NOT multi-AI collaboration or actual GPT-OSS execution.
- Full Windows filesystem+network confinement and process-tree STOP are not yet qualified.

## Implementation: reuse rather than replace

- Reuse existing cloud provider connectors, reviewer adapters and the frozen advisory/Qwen baseline through new optional adapters; do not modify the baseline.
- Extend the *advisory* collaboration layer only: independent proposals -> reciprocal critiques -> plan with explicit disagreements -> owner digest decision -> patch submissions and cross-review -> ORION-native typed proposal.
- Do not add a second authority engine, STOP, Vault, memory store, or executor.
- Do not connect the separate TheHands project as an ORION dependency. Historical test transport is not product architecture.
- First proof: offline deterministic protocol tests and fake provider outputs. Second: real two-cloud brainstorming with saved provenance and owner-visible plan. Third: approved bounded native build only after confinement/STOP qualification.

## Safety / acceptance

- Reject fewer than two distinct model identities, missing critique, missing owner approval, stale or mismatched plan digest, cross-project scope and unauthorized patch paths.
- Freeze round inputs for fair independent comparison; cap rounds and budgets; record failures without falsely calling them consensus.
- Never run cloud-provided code as a side effect of brainstorming or parsing.
- PASS requires authenticated independent build/test evidence; models' claims are advisory only.

## First demonstration

Owner requests a tiny real application. Two cloud models propose and challenge approaches; owner approves a frozen plan; models produce patches; ORION/Qwen orchestrate authorized execution; independent tests determine success; repair evidence is retained. Until execution is qualified, stop at an owner-approved plan and safe dry-run.

This decision supersedes any older roadmap wording placing single-Qwen coding before multi-cloud architecture collaboration. The existing ORION authority and isolation prerequisites remain mandatory.
