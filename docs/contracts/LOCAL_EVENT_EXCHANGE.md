# ORION Local Event Exchange v0

Date: 2026-10-03

Status: **V3-RUN-016 TARGET**

The local exchange is a mailbox/view over ORION's append-only Event Ledger.

It does not replace the ledger and it does not create a second source of truth.

## Exchange flow

```text
TASK
 -> PROPOSAL
 -> REVIEW
 -> DECISION
 -> ACTION
 -> EVIDENCE
 -> RESULT
```

## Message identity

Local messages use normal immutable Event IDs.

External messages use a deterministic Event ID derived from:
- project ID;
- source system;
- external message ID.

Re-ingesting the exact same external message returns the existing Event.

Reusing the same external message ID with different immutable content is a
collision and must fail closed.

## Recipients

Recipient is immutable Event payload data.

Acknowledgement is stored separately in an append-only receipt table.

Acknowledging a message never mutates the Event.

## Causal scope

Parent Event:
- must exist;
- must belong to the same project;
- when both parent/current are task-bound, must belong to the same task.

## Task packet

A bounded task packet contains:
- L0 project orientation;
- current task identity/objective/status;
- latest bounded task Events in causal order.

This is the future context packet exposed to replaceable cloud reviewers and
Hands.

## Authority

Exchange Events carry information and requested work.

They do not mint:
- approval;
- Action Lease;
- trusted scope;
- capability authority;
- PASS/FAIL truth.

ORION policy remains authoritative before dispatch.

## V3-RUN-016 acceptance

Physically prove:
- exact external duplicate is idempotent;
- conflicting external duplicate is denied;
- recipient inbox works;
- acknowledgement does not mutate Event;
- receipt is append-only;
- full six-step causal chain persists;
- cross-task parent is denied;
- bounded latest task packet is deterministic;
- cross-project data does not leak;
- close/reopen preserves exchange state;
- no network/GitHub/model is required.
