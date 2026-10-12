# ORION internal Hands — preservation and donor boundary
Date: 2026-10-12
Status: READ-ONLY FINDING / NOT PHYSICALLY TESTED

Owner directive: Preserve every existing internal ORION Hand and its capabilities. Add narrowly scoped adapters, never replace or strip abilities. Do not modify frozen code without approval. Existing independent TheHands- remote remains the owner's manual GITCHECK control.

Repository discovery (GitHub owner Sadusor):
- Sadusor/TheHands- — separate manual Windows/Android remote.
- Sadusor/OpenHands — public fork of OpenHands coding-agent donor; not proof that ORION internal Hands are stored there.
- Sadusor/ORION-V3 — contains the internal work-loop/Hand-facing modules.
- No standalone public repository literally identified as 'ORION internal Hands' from repository-name search. Need trace actual imports/entrypoints before claiming their source of truth.

Confirmed ORION-V3 source:
- src/orion_v3/work_loop/sandbox_srt.py: work_hand_plan and SrtSandboxPlan produce Windows sandbox configuration ONLY; no process launch or qualified sandbox.
- src/orion_v3/work_loop/authorization.py: Authorization, issue_authorization, verify_authorization; binds task, project, proposal hash and optional source revision; current verification shown is signature/expiry and does not itself prove one-time nonce consumption.
- src/orion_v3/work_loop/verifier.py: verify_evidence validates evidence type, task, proposal hash and source revision; not alone proof of physical execution.
- src/orion_v3/work_loop/engine.py: WorkLoopEngine gates proposals and evidence; keep intact.
- docs/contracts/THEHANDS_LIFECYCLE_BRIDGE.md: TheHands independent; bridge is UNCONFIGURED until actual ORION production START/STOP/STATUS exists; not an execution tunnel.

Preservation rules for subsequent phases:
1. Inventory each ORION Hand and supported operations before touching implementation.
2. Reuse existing Hands through an additive dispatcher/adapter and preserve prior APIs.
3. Preserve OpenHands as a donor; no forced migration or destructive replacement.
4. Never use TheHands- as autonomous ORION Hand. Use TheHands- only for remote manual GITCHECK/approval/test.
5. All new Hand-related changes require a compatibility test suite verifying legacy abilities, plus STOP, revision binding, idempotency and physical evidence.
6. No claim of PASS until real GITCHECK evidence.

Audit ledger: Step 1 IN PROGRESS; public repository naming checked, internal Hand implementations not yet fully enumerated.
