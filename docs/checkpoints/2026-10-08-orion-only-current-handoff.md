# ORION V3 — current handoff (2026-10-08)

Active owner directive: Decision 0018. Build the owner–ChatGPT–DeepSeek collaboration protocol inside ORION V3 only. No code, adapter, runtime, test, repository, evidence-schema or document-contract dependency on the separate TheHands project. ORION's internal Work Hand is `src/orion_v3/work_loop/executor.py`.

Precedence: Decision 0018 supersedes historical TheHands/GitCheck engineering workflow instructions in `AI_OPERATOR_BRIEF.md`, `AGENTS.md`, `docs/ROADMAP.md`, and `docs/STATUS.md` for this collaboration loop. Keep historical evidence intact; do not follow older conflicting active-task language.

Existing foundations: `work_loop/contracts.py` Proposal/EvidenceRecord/WorkState; authorization, Vault, verifier, STOP, and executor contracts. Frozen modules are read-only by default. Experimental Windows isolation and cross-process STOP tests are partial; network confinement remains inconclusive; full eight-check qualification not run. Production real execution remains disabled.

Immediate work: (1) audit ORION-native review/collaboration contracts; (2) add one isolated provider-neutral offline collaboration-cycle module and deterministic tests for task→proposal→critique→owner decision→evidence→repair/freeze; (3) ensure neither model outputs nor tests grant execution authority or self-assert PASS; (4) only then integrate with existing ORION authority/Vault after review; (5) qualify physical execution separately. Do not create a second STOP, Vault, verifier, memory, or Hand.

Documentation debt: canonical ROADMAP/STATUS/AI_OPERATOR_BRIEF still contain conflicting older active tasks and TheHands instructions. Reconcile active sections without deleting history. This handoff records the precedence and does not claim those files were rewritten.
