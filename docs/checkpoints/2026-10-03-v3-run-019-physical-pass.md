# ORION V3 — V3-RUN-019 Physical PASS — 2026-10-03

Status: **PHYSICAL PASS**

## Exact identities

V3 tested SHA:
`8388fb3f1b445be377c460defdd66a8010b198a4`

Remote staging SHA:
`aadf31b927ef439c91ba0f9d126277e541e7bc38`

Named task:
`v3-current-gate`

Session:
`11afb5138e9d`

Result:
`PASS`

## Physical evidence

Observed regression:
`84 passed in 3.43s`

Observed gate:
```text
ATTEMPT_CREATE> PASS
SINGLE_ACTIVE_LEASE> PASS
CHECKPOINT_REQUIRES_LEASE> PASS
EXPIRED_LEASE_ADVANCE> DENIED
LEASE_RECLAIM_AFTER_EXPIRY> PASS
STALE_LATE_WORKER> DENIED
REOPEN_RECOVERY> PASS
STOP_INVALIDATES_OWNERSHIP> PASS
LATE_RESULT_AFTER_STOP> DENIED
NETWORK_MODEL_EXECUTION_DEPENDENCY> NONE
ATTEMPT_OWNERSHIP_GATE> PASS
STATUS> PASS
```

## Meaning

ORION now has durable execution ownership above its existing low-level
ActionLease primitive.

Only the current fenced Attempt lease may advance checkpoint/result truth.
Expired, replaced or stopped ownership cannot silently advance canonical state.
Restart preserves the Attempt/lease/checkpoint truth.

## Next

V3-RUN-020:
isolated exact-SHA disposable Git worktree execution of one harmless immutable
WorkPackage, with path/diff/verifier evidence, Attempt lease ownership, cleanup,
and no push/merge.
