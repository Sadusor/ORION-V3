# V3-RUN-051 — ORION-owned task progress authority PHYSICAL PASS

Date: 2026-10-04

## Evidence

Authoritative Remote session:
`39ff2e8d0f6d`

Remote source SHA:
`1fbba205fe9c250ff8631cb8c0bd968e3c0258e5`

Exact V3 SHA:
`4499e387644bca6e3a4b8803e95e60477d3b006e`

Remote result:
- state: completed
- exit_code: 0
- result: PASS

Regression suite:
- 228 passed in 14.67 s

## Governor authority boundary

Model:
- `qwen35-9b-orion:latest`
- thinking ON
- context 4096

Model-facing task completion/status tools:
0

The model chose semantic file-search actions only.

## Complete case

Owner contract:
- find `pyproject.toml`
- find `gateway.py`
- scope: `active_project`

Real Hand evidence contained both required basenames.

ORION decision:
`COMPLETED`

Task status:
`completed`

Decision retry:
idempotent

## Incomplete case

Owner contract:
- find `pyproject.toml`
- find `__ORION_RUN051_PROVABLY_MISSING_5D6A2C91__.nope`
- scope: `active_project`

The gate first proved the synthetic basename did not exist.

Real Hand evidence found only the real basename.

ORION decision:
`NEEDS_NEXT_STEP`

Missing requirement:
`__ORION_RUN051_PROVABLY_MISSING_5D6A2C91__.nope`

Task status:
`needs_next_step`

Decision retry:
idempotent

## Canonical causal history

Both physical tasks produced:

`PROPOSAL -> ACTION -> EVIDENCE -> RESULT -> DECISION`

The DECISION was parented directly to the verified RESULT.

Decision authority:
`orion_deterministic_policy`

## Durability

After SQLite close/reopen:
- `completed` status persisted;
- `needs_next_step` status persisted;
- both DECISION Events persisted.

## External calls

Cloud/provider calls:
0

## Conclusion

ORION now owns canonical task completion/progress.

A model may propose semantic work and explain evidence, but it cannot self-declare
that an objective is finished.

## Next

V3-RUN-052:
prevent autonomous retry loops after an exhausted exact search.

A non-truncated exact search with required names still missing must transition
from `needs_next_step` to `waiting_owner`, and the 9B may only formulate a
grounded owner question. It receives no execution tools on that turn.
