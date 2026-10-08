# Decision 0019 — Qwen + ORION Hands engineering loop

Date: 2026-10-08
Status: OWNER CLARIFICATION / ACTIVE

## Intended product
Recreate the proven owner–AI–execution–review working pattern as an ORION V3-native engineering loop: owner submits work; ORION owns task state, authority, policy, approval, STOP, evidence, and Vault; local Qwen is the low-consumption reasoning/coordinating model; optional cloud AIs (ChatGPT, DeepSeek and replaceable reviewers) propose code and critique; **ORION's own Work Hand** executes only bounded, authorized operations; independent verification records FAIL/repair/PASS and continuity.

The owner wants the familiar remote-app working experience as a product interaction pattern, not TheHands implementation. The separate TheHands project is a reference for UX/workflow only, **not** a runtime, code, build, test, evidence, repository, or authority dependency. Never conflate ORION Hands with the separate TheHands product.

## Execution order
1. Read existing ORION-native work_loop contracts, authority/Vault/STOP/verifier, model adapters, UI and current canonical state before implementing.
2. Implement the smallest replaceable ORION-owned collaboration protocol around the existing contracts: task -> Qwen coordination -> specialist proposal -> critique -> owner decision when required -> ORION authorization -> ORION Work Hand -> independent evidence -> repair/freeze. Initially manual cloud exchange is acceptable.
3. Offline deterministic contract tests first; no model or remote UI can authorize execution or self-assert PASS.
4. Physical bounded execution only after applicable isolation, STOP and recovery gates qualify it. Real execution remains disabled now.
5. Connect proven protocol to existing PC/Android ORION UI. Preserve low idle consumption, modularity, frozen modules and historical evidence.

## Documentation precedence
This clarification supplements Decision 0018 and supersedes any interpretation that the target product is a ChatGPT–DeepSeek-only loop, or that the separate TheHands project is the executor. Existing historical mentions remain history; active instructions must use ORION's own Hands.

No production execution or frozen-module modification is authorized by this documentation decision.
