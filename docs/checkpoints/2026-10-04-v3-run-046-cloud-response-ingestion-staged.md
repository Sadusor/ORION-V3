# V3-RUN-046 — cloud specialist response ingestion staged

Date: 2026-10-04

## Purpose

Prove the return path from a queued cloud specialist request back into ORION
before connecting a live provider.

RUN-045R already physically proved:

`9B -> ORION -> cloud:coding queue`

RUN-046 proves:

`cloud response envelope -> ORION REVIEW evidence`

## Authority rule

A cloud specialist response is advisory evidence only.

It may not:
- mint approval;
- create a DECISION;
- create an ACTION;
- execute a Hand;
- mutate the queued request;
- widen task scope;
- become canonical success merely because a model said so.

## Binding

Every response is bound to:
- exact ORION cloud request ID;
- exact request SHA256;
- exact parent request Event;
- source system;
- external provider message ID;
- provider ID;
- model ID;
- immutable response text hash.

The response is emitted into the Local Event Exchange as:
- event type: `REVIEW`;
- recipient: `orion:governor`;
- actor kind: `cloud_specialist`;
- authority marker: `advisory_only`.

## External idempotency

Exact repeated provider message:
- same deterministic Event;
- duplicate=true;
- no duplicate review.

Same source/external message ID with changed immutable content:
- fail closed.

## Gate mode

RUN-046 is:
- zero model;
- zero network;
- zero provider API;
- zero Hand execution.

It uses a clearly labeled synthetic response fixture only to prove the immutable
ingestion/authority envelope.

A later slice may connect Groq/Gemini/another approved provider to this already
proven return contract.

## PASS meaning

PASS proves that cloud reasoning can return to ORION without becoming an
authority peer.
