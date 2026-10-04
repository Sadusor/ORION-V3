# Decision 0015 — Production Operator Control Plane V0

Date: 2026-10-04

Status: ACCEPTED FOR PHYSICAL GATE

## Context

RUN-042 proved the lightweight 9B model is the best current routine local
operator candidate on this PC.

RUN-043 then showed why security-critical workflow truth must not live in the
model loop: valid models may duplicate requests, inspect state, retry or produce
non-minimal action sequences.

The production operator path therefore needs a deterministic ORION-owned layer
between model proposals and real execution.

## Decision

Introduce `OperatorControlPlane` as the first production authority/state layer
under the local operator.

It reuses:
- the semantic Capability Registry;
- canonical SQLite state;
- append-only Events;
- the Local Event Exchange.

It does not create another tool registry.

## Exact approval contract

A model may request approval for a semantic capability, but ORION:

1. resolves the registered capability;
2. normalizes its parameters deterministically;
3. rejects the approval lane if that capability does not require bounded or
   consequential approval;
4. freezes:
   - capability id;
   - capability version;
   - normalized parameters;
5. hashes the frozen action canonically;
6. records the request in canonical state and Event history.

Human approval applies only to that exact hash.

### Duplicate handling

An identical still-live approval request for the same task and action hash is
idempotent and returns the existing approval.

Repeated human approval of an already-approved exact action is idempotent.

### Resume

Resume does not accept replacement parameters from the model.

`consume_approved_action(approval_id, task_id, consumed_by)` returns the exact
frozen action already approved.

This prevents a model from changing the target or content after the human has
approved it.

### Single use

An approved action may be consumed exactly once.

After consumption:
- replay is stale;
- a foreign task cannot reuse it;
- a rejected approval can never become executable.

### Tamper protection

The stored frozen action is re-hashed before consumption.

A changed action payload after approval is denied.

## Atomic state + Event history

`OrionStateStore.append_event()` now supports `commit=False`.

Default behavior remains unchanged.

The production control plane uses a caller-owned SQLite transaction so the
authority-table transition and canonical Event append commit or roll back
together.

## Cloud-specialist queue

The local operator may request a bounded cloud specialist:
- architecture;
- coding;
- review.

V0 does not call a provider.

ORION freezes and hashes the request, records it in canonical state and writes
an Event Exchange-compatible PROPOSAL addressed to:
- `cloud:architecture`
- `cloud:coding`
- `cloud:review`

Identical requests inside the same task are idempotent.

This gives future provider connectors an ORION-owned inbox rather than letting
the local model call arbitrary cloud providers directly.

## Non-goals of V0

V0 does not yet:
- dispatch the approved action to a Hand;
- connect Groq/Gemini/other cloud providers;
- run the 9B operator in production;
- implement UI approval cards;
- replace durable AttemptAuthority for actual execution ownership.

Those are subsequent slices.

## Required physical proof

V3-RUN-044 must prove:
- exact-action freeze/hash;
- duplicate approval request idempotency;
- pending execution denial;
- duplicate human approval idempotency;
- foreign-task denial;
- exact approved-action resume;
- single-use stale replay denial;
- rejected-action denial;
- frozen-action tamper denial;
- causal PROPOSAL -> DECISION -> ACTION Events;
- restart persistence;
- stale replay remains denied after restart;
- cloud queue idempotency;
- cloud request appears in Local Event Exchange;
- no model dependency;
- no network dependency;
- no execution side effect.
