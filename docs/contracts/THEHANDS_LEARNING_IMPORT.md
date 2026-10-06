# TheHands Learning Import Contract

Status: **FEATURE BRANCH / NOT YET PHYSICALLY QUALIFIED**

This contract governs the optional learning connection between the independent
TheHands product and ORION V3.

## Independence

TheHands and ORION remain independent products.

- TheHands must work normally when ORION is stopped, missing, broken or deleted.
- ORION must work normally when TheHands is stopped, missing, broken or deleted.
- TheHands never imports ORION runtime or Memory code.
- ORION never owns TheHands execution, STOP, updater or runtime truth through this path.

## Source truth

TheHands already writes neutral completed-run evidence to:

`%LOCALAPPDATA%\TheHands\learning-outbox\`

Schema:

`thehands.run-evidence.v1`

Those files remain TheHands-owned local evidence. The learning sync does not alter
the Hand finalizer and does not delete outbox files.

## Owner control

The visible TheHands control is one manual START / STOP learning-sync control.

START:
1. probes `http://127.0.0.1:8890/api/health`;
2. if ORION is offline, performs no transfer and leaves all lessons local;
3. if ORION is online, sends only pending unacknowledged evidence.

STOP:
- cancels only the current evidence transfer;
- never stops ORION;
- never stops TheHands;
- never stops a Hand;
- never changes lesson collection.

There is no automatic ORION startup and no background auto-connect loop.

## ORION intake

Endpoint:

`POST /api/learning/thehands/import`

ORION accepts only:
- `schema == thehands.run-evidence.v1`;
- `source_system == TheHands`;
- provenance with `authority == evidence_only`;
- recognized PASS / FAIL / STOPPED results.

ORION computes a canonical SHA-256 over the evidence JSON and returns:
- evidence ID;
- evidence SHA-256;
- candidate ID.

TheHands records that acknowledgement separately in:

`%LOCALAPPDATA%\TheHands\orion-learning-sync.json`

The local outbox file remains present.

## Idempotency

The evidence ID + canonical hash is the replay key.

- same ID + same hash => accepted as already imported;
- same ID + different hash => reject as a collision;
- interrupted transfer => unacknowledged items remain pending.

## Memory authority

Import creates only an ORION MemoryCandidate/evidence candidate with decision
`defer`.

Import does **not**:
- PROMOTE canonical Memory;
- grant permissions;
- create Action Leases;
- mark an execution effect as verified;
- widen scope;
- authorize any Hand.

Canonical promotion remains an ORION-owned later decision.

## Physical qualification gate

Before merging either feature branch:

1. frozen TheHands baseline remains unchanged;
2. TheHands contract tests PASS;
3. isolated sync test proves transfer + acknowledgement + replay idempotency;
4. ORION import test proves evidence-only DEFER candidate creation;
5. ORION offline test proves lessons remain local;
6. native TheHands build succeeds from the feature worktree;
7. live frozen TheHands is not replaced during qualification;
8. final physical UI gate shows START -> progress -> SYNCED and STOP affects only transfer.
