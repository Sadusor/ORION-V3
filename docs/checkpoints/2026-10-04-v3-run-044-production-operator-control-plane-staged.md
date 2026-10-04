# V3-RUN-044 — Production Operator Control Plane V0 staged

Date: 2026-10-04

Status: **STAGED / PHYSICAL RUN PENDING**

## Purpose

Move ORION from benchmark-only operator composition toward a production
control-plane path.

This slice deliberately contains no local model call, no cloud provider call and
no execution side effect. It proves the deterministic authority substrate first.

## New production module

`src/orion_v3/operator/control.py`

Exports:
- `OperatorControlPlane`
- frozen exact capability actions
- approval records/status
- idempotent approval request/decision results
- single-use approved-action consumption
- cloud-specialist queued-request records

## Approval authority

A model may request approval, but ORION:
- resolves the semantic capability from the Capability Registry;
- normalizes parameters;
- rejects the approval lane for capabilities below bounded-modification risk;
- freezes capability id/version/params;
- computes canonical SHA256;
- records the request in SQLite + append-only Event history atomically.

Human transitions:
- PENDING -> APPROVED
- PENDING -> REJECTED
- APPROVED -> REVOKED before effect
- APPROVED -> CONSUMED exactly once

Resume does not accept new model parameters.

The caller receives the exact frozen action already approved.

Therefore a model cannot use the resume step to change:
- target;
- content;
- capability;
- normalized parameters.

## Event atomicity change

`OrionStateStore.append_event(..., commit=False)` is now supported.

Default remains `commit=True`.

The operator control plane uses caller-owned SQLite transactions so canonical
authority state and Event history commit or roll back together.

## Cloud-specialist queue

V0 supports bounded queue requests for:
- architecture;
- coding;
- review.

No provider is called.

The request is:
- frozen;
- SHA256-addressed;
- deduplicated per task;
- persisted;
- emitted as an Event Exchange-compatible PROPOSAL to
  `cloud:<specialty>`.

## RUN-044 physical proof requirements

The gate must prove:
- Event rollback under caller transaction;
- exact-action freeze/hash;
- duplicate model approval request idempotency;
- pending action cannot execute;
- duplicate human approval idempotency;
- foreign-task approval reuse denied;
- exact frozen action returned on resume;
- model rewrite on resume impossible by API shape;
- consumed approval is single-use;
- human can revoke an approved action before effect;
- revoked action cannot execute;
- rejected action cannot execute;
- stored action tampering detected;
- causal PROPOSAL -> DECISION -> ACTION chain;
- cloud request deduplicated;
- cloud request visible in Local Event Exchange;
- restart persistence;
- stale replay denied after restart;
- model dependency NONE;
- network dependency NONE;
- execution side effect NONE.

## What RUN-044 does not yet prove

It does not yet:
- attach the 9B model to this production control plane;
- dispatch an approved action to a Hand;
- connect live Groq/Gemini/provider calls;
- prove UI approval cards;
- replace AttemptAuthority for execution ownership.

If RUN-044 passes, the next slice should attach the qualified
`qwen35-9b-orion:latest` operator to this deterministic control plane while
keeping all execution authority in ORION.
