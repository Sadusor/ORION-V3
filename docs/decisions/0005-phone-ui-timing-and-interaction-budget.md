# Decision 0005 — Phone UI timing and interaction budget

Date: 2026-10-04  
Status: PLANNED OWNER REQUIREMENT  
Legacy Remote UI: FROZEN / UNCHANGED

## Requirement

The production phone experience must require materially fewer operator actions than the current development Remote.

The current CHECK GITHUB -> inspect SHA -> APPROVE & RUN -> manual refresh/evidence flow is a development harness, not the target product UX.

## Timing

Build the first new V3 phone/UI alpha immediately after Proof V2 (Qwen 9B interpretation under the frozen authority contract) and before the broad Hands/substrate tournament.

Reason:

- Proof V1 has now stabilized the core authority concepts;
- Proof V2 will stabilize the natural-language -> structured-contract boundary;
- waiting until all Hands are benchmarked would force the owner to keep using a deliberately temporary development workflow for too long;
- the Hands tournament can then run through the new UI and improve it with real evidence.

## Target interaction budget

### Low-risk read/open/search tasks

One owner request should be sufficient authorization when the requested operation, target and risk class are already exact.

Target phone flow:

`speak/type request -> ORION/Qwen interpret -> ORION validates -> run -> result/evidence`

No separate CHECK GITHUB button and no redundant second approval.

### Bounded writes / material changes

At most one compact confirmation card when the interpreted structured plan adds meaningful state change that the owner's original request did not already make exact enough.

Target phone flow:

`request -> short plan card -> APPROVE -> automatic execution -> evidence`

### High-risk / destructive / external actions

Explicit confirmation remains mandatory.

Examples include destructive deletion, credentials, external publication/sending, installs, shutdown, privilege changes, or scope expansion.

STOP remains globally visible and immediate.

## New UI alpha

The first V3 UI should prioritize:

- one primary text / hold-to-talk input;
- current ORION state in plain language;
- automatic exact-SHA/task plumbing hidden from normal operation;
- automatic refresh / event stream;
- one approval card only when policy requires it;
- one global STOP;
- clear active Hand/model identity;
- inline PASS/FAIL with VIEW EVIDENCE;
- current task plus a compact history drawer;
- stale/disconnected state shown honestly;
- no duplicate buttons or duplicate Evidence Pack elements.

The old Remote remains the rollback/fallback until new UI parity is physically proven and accepted by the owner.

## Non-goal

Reducing taps must never weaken authority.

Fewer UI actions are achieved by moving deterministic bookkeeping into ORION and by treating an explicit owner request as authorization when policy can safely bind it to an exact low-risk operation. It is not achieved by giving models broader permission.
