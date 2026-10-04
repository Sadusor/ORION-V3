# V3-RUN-049R — first production routine Hand loop PHYSICAL PASS

Date: 2026-10-04

## Evidence

Authoritative Remote session:
`01f84e2eb1a5`

Remote source SHA:
`cc9c3875064b858652a581a74ac6352f5ad06901`

Exact V3 SHA:
`2c4f767486f9e67e376ff8114eceaf428bb228dc`

Remote result:
- state: completed
- exit_code: 0
- result: PASS

Regression suite:
- 217 passed in 11.98 s

## Native donor environment

- pinned OpenJarvis SHA: PASS
- desktop-native environment sync: PASS
- `openjarvis_rust` import: PASS

## Governor

- model: `qwen35-9b-orion:latest`
- thinking: ON
- context: 4096
- governor tool selection latency: 3.166 s
- selected capability: `fs.search_exact`
- selected names:
  - `pyproject.toml`
  - `gateway.py`
- selected location:
  - `active_project`

## Canonical proposal

Proposal Event:
`0eb8df50-1ccb-4d37-9cce-5651955edd2e`

Canonical action SHA256:
`62b7da4bb9f5d9107479f1fd0b482e56f8aef4485e915bc445a2c529670c7208`

## Real Hand execution

ORION Action-Lease dispatch: PASS

Action Event:
`79497571-e0fb-44e2-9d58-fe5c67d1aa79`

Evidence Event:
`9c5b7bc9-db3c-4d8a-aa96-502fa3199444`

Result Event:
`ef25ba6d-296d-4536-b5fd-443205a0b328`

Hand:
`openjarvis.tool.orion_filesystem_search.v1`

Hand outcome:
`confirmed`

Verified:
- requested basenames found: PASS
- expected relative paths found: PASS
- match count: 8
- trusted absolute root leaked: 0
- deterministic verification: PASS

## Causal history

Exact chain physically proven:

`PROPOSAL -> ACTION -> EVIDENCE -> RESULT`

Every child was bound to the immediately preceding canonical Event.

## Replay

A second execution attempt using the same canonical proposal was blocked:

`proposal_already_dispatched`

## External calls

Cloud/provider calls:
0

## Conclusion

ORION V3 has now physically completed its first production read-only effect loop:

`OWNER -> local 9B governor -> ORION semantic proposal -> ORION Action Lease -> real OpenJarvis Hand -> ORION evidence normalization -> deterministic ORION RESULT`

The model chose semantics only.

ORION owned:
- canonical proposal truth;
- capability version/hash validation;
- dispatch eligibility;
- Action Lease;
- trusted filesystem root;
- Hand execution boundary;
- evidence normalization;
- deterministic verification;
- RESULT truth.

## Next

V3-RUN-050:
feed only an ORION-verified RESULT packet back to the local governor and prove a
user-facing response remains grounded in that RESULT without inventing extra
paths, side effects, approvals, edits or success claims.
