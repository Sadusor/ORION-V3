# ADR — Remote V1 Protected / V2 Shadow Migration

Date: 2026-10-05
Status: SUPERSEDED 2026-10-05 by Decision 0015
Owner decision at time of this ADR: build a V2 shadow migration beside V1.

> **SUPERSEDED:** The owner later locked a simpler direction: V1 Remote is frozen and used only as the existing development/control path. ORION will not build a V2 Remote/parity surface. New work is connectors plus separate STRATA/Claude-inspired PC and phone product UIs, then backend/connector wiring. See `docs/decisions/0015-freeze-v1-build-product-ui-and-connectors.md`. The remainder of this file is retained only as historical context.

## Decision

Remote V1 is the protected production control surface. It is not redesigned in place.

The new ORION UI (V2) is built as a separate process/surface and initially behaves as a client/proxy of V1. V1 remains the authority and execution owner for all already-proven operations until an individual replacement is physically proven.

Initial topology:

```text
Phone
 ├─ V1 Remote :8766  ← protected fallback, remains usable
 └─ V2 UI     :8770  ← new shell
                    │
                    ├─ existing actions → localhost V1 adapter → SAME V1 backend
                    ├─ AI Council       → new sidecar/service
                    ├─ Memory           → new sidecar/service
                    └─ later media/voice→ separate sidecars
```

V2 MUST NOT maintain a second canonical run state. For legacy/proven operations it renders V1's backend-reported state and forwards actions to V1. No duplicated attempt counters, approvals, session truth, or evidence truth are allowed.

## Protected V1 invariants

The protected V1 path continues to own:
- Check GitHub
- exact checked SHA
- one-task primary Approve & Run
- named dispatch session
- authoritative STOP for the running task
- result/evidence publication
- pairing/device security already used by V1
- existing safe shutdown behavior

The frozen backup branch `backup/coding-loop-proven-2026-10-05` remains the recovery reference.

## V2 rules

1. Different port/process. A V2 crash cannot terminate V1.
2. No direct Hands execution from V2 during migration. Existing execution actions proxy to V1.
3. No invented UI state. V2 displays only state returned by V1 or an explicitly identified new sidecar.
4. Every new capability is feature-gated and off until physically tested.
5. Global STOP in V2 first calls the V1 authoritative STOP path for V1-owned work, then stops V2-owned sidecars. V1's direct STOP remains independently reachable.
6. V2 failure must never prevent the operator from opening V1 directly.
7. V2 does not change legacy attempt counters or result history.
8. Existing V1 server files should not be changed merely for V2 cosmetics.

## V2-to-V1 adapter

V2 gets one narrow local adapter responsible for forwarding approved existing API operations to `127.0.0.1:8766`.

The adapter may proxy:
- status
- Check GitHub
- Approve & Run
- STOP
- evidence retrieval
- task/session status

It does not reinterpret results. It preserves V1 response semantics.

Authentication is bridged locally without exposing the V1 service token to browser JavaScript. V2 has its own phone session; its server-side adapter holds the V1 loopback credential. Pairing/bootstrap must fail closed if V1 is unavailable.

## New-feature sidecars

New functionality is added outside V1 first:
- five-cloud-AI Council
- memory visualization/retrieval
- project/roadmap context
- live PC view
- voice

These services can be developed and restarted independently. They may read V1/project state where permitted but cannot gain execution authority merely because they are connected to V2.

## Five-cloud-AI coding workflow

Target path:

```text
Owner goal
  ↓
ORION freezes project / roadmap / task context
  ↓
5 cloud AIs reason independently
  ↓
review / critique / revision loop
  ↓
ORION deterministic aggregation + policy checks
  ↓
Owner approval when required
  ↓
existing proven execution path / Hands
  ↓
tests + evidence
  ↓
optional cloud review of result
```

Cloud models never gain PC authority. ORION/Hands remain the execution boundary.

## Parallel validation

Every migrated V1 capability uses a parity test:

A. Perform/read the operation through V1.
B. Perform/read the same operation through V2.
C. Verify same checked SHA, task/session identity, result, STOP behavior, and evidence pointer.
D. Mark the V2 feature QUALIFIED only after physical phone proof.

During this phase both V1 and V2 remain available.

## Promotion gates

A V2 capability may become the normal surface only when:
1. backend parity test passes,
2. physical phone test passes,
3. STOP/recovery test passes where execution is involved,
4. evidence proves no regression,
5. direct V1 rollback remains available.

Promotion is per capability, never a whole-system flag day.

## UI build order

Phase 1 — shell only:
- Home / status
- Work / tasks
- AI Council
- Memory
- System / Remote
- global STOP
- exact SHA / evidence visibility

Phase 2 — V1 parity adapter:
- status
- Check GitHub
- one-task Approve & Run
- STOP
- evidence

Phase 3 — five-cloud-AI Council:
- five explicit slots
- provider/model health
- independent outputs
- review rounds
- deterministic final packet
- owner approval
- handoff into the proven execution path

Phase 4 — Memory, project context, media, voice.

## Rollback

Rollback is immediate: use Remote V1 directly. V2 does not need to be repaired before work can continue.

This is the core migration principle: **extend beside the proven system, test against it, and replace only after proof.**
