# Coding Factory Attempt Ownership Contract

Status: **V3-RUN-019 candidate — must be physically gated before being called proven**

## Purpose

A WorkPackage may be immutable and reviewed while still having zero execution authority.
Before any WorkPackage can touch code, ORION must own a durable Attempt and exactly one
short-lived execution lease for that Attempt.

## Authority rule

`worker output != ORION state`

A worker may compute late, crash, restart or continue after losing ownership. ORION
accepts checkpoints and results only when they carry the current Attempt lease.

## Durable Attempt state

Each Attempt persists:
- project/task identity;
- lifecycle status;
- monotonically increasing lease generation;
- current worker identity;
- current opaque-token hash;
- lease issue/expiry/revocation times;
- checkpoint sequence + payload;
- terminal result;
- Stop truth.

The opaque lease token is returned to the worker but never stored in plaintext.

## Fencing rule

Every successful claim increments `lease_generation`.

If a lease expires, a later worker may claim the Attempt with a new generation/token.
The old token immediately becomes stale even if the old process is still alive.

Therefore a late checkpoint or result from an earlier worker is denied rather than
silently advancing canonical state.

## Stop rule

Stop is ORION-owned durable state.

When Stop is recorded:
1. Attempt status becomes `STOPPED`;
2. current lease is revoked before any later checkpoint/result can be accepted;
3. subsequent claims/checkpoints/results fail closed;
4. restart/reopen preserves the stopped truth.

## Relationship to Gate-1 ActionLease

`authority/leases.py` remains the low-level short-lived operation authorization
primitive used before individual Hand dispatch.

Attempt ownership is a higher-level durable execution-ownership contract. It does not
replace the ActionLease and it does not grant arbitrary tool authority.

## V3-RUN-019 acceptance evidence

The physical gate must prove:
- one active lease owns an Attempt;
- second worker cannot claim while it is active;
- checkpoint requires the current lease;
- expired lease cannot advance;
- a new claim after expiry fences the old worker;
- stale late result is denied;
- restart preserves Attempt/checkpoint/lease truth;
- Stop revokes ownership;
- checkpoint/result after Stop are denied;
- no network/model dependency is required.
