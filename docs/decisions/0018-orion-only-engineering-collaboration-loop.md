# Decision 0018 — ORION-only engineering collaboration loop

Date: 2026-10-08
Status: OWNER DIRECTIVE / ACTIVE

## Goal

Prove a modular engineering collaboration loop between the owner, ChatGPT and DeepSeek **within ORION V3**, before integrating it with ORION's existing runtime, authority, Vault, memory and UI. The first version may use manual model exchanges; encode tasks, proposals, reviews, decisions, test evidence, FAIL/repair/PASS and continuity in ORION-owned contracts.

## Hard isolation

- TheHands is a different product. **Zero runtime, build, code, test, document-contract, repository or adapter dependency** on that project. Do not stage tests there or use its evidence schema.
- ORION's own Work Hand is `src/orion_v3/work_loop/executor.py` and related ORION modules. Do not confuse these components.
- Any previous experimental cross-project engineering evidence adapter is rejected and deleted; its staged external test was cleared.
- Historic project records mentioning external tools are history, not instructions or dependency approvals. Do not rewrite historical evidence as though it never happened.
- Use ORION repository tests and ORION-owned execution/evidence facilities. Do not create a parallel app, authority system, Vault, STOP, or memory store.

## Next implementation

1. Audit existing ORION-only collaboration, review, state and test contracts.
2. Implement an isolated provider-neutral engineering cycle protocol: task -> ChatGPT proposal/patch -> DeepSeek critique -> owner decision -> ORION-native test evidence -> repair or freeze.
3. Prove deterministic offline contract tests first, then qualify physical execution through an ORION-native mechanism once authorized and ready.
4. Integrate only after end-to-end evidence and restart/continuity gates pass.

No real execution or frozen-module changes are authorized by this decision.
