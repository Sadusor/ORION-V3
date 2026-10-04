# V3-RUN-045R — production 9B governor attachment PHYSICAL PASS

Date: 2026-10-04

## Evidence

Authoritative Remote session:
`91d3e204f106`

Remote source SHA:
`9a18b7ac4ddea3422bfec63c7aa373895daf716f`

Exact V3 SHA:
`e1737ce28aa47710316a946d7716694d11754029`

Remote result:
- state: completed
- exit_code: 0
- result: PASS

Regression suite:
- 201 passed in 10.71 s

## Physically proven

Production governor:
- `qwen35-9b-orion:latest`
- thinking ON
- context 4096
- observed model size / VRAM: 5,490,081,790 bytes / 5,490,081,790 bytes

Routine proposal:
- 9B selected `fs.search_exact`;
- ORION normalized and recorded the proposal;
- no filesystem Hand executed.

Approval path:
- 9B selected `project.publish_exact_artifact`;
- ORION froze exact capability/version/normalized parameters;
- frozen action SHA256:
  `e8c05e5b837ba3435bdc4183af474142cd64ffc60d718e6df56d7b1750883c2a`;
- human approval changed authority state;
- resume exposed only `approval_id`;
- ORION consumed the exact frozen action;
- model replacement parameters accepted: 0;
- duplicate resume denied as `stale_approval`;
- publish Hand executions: 0.

Cloud routing:
- 9B selected the ORION coding-specialist queue;
- request entered `cloud:coding`;
- direct 9B -> provider calls: 0;
- cloud execution authority granted: 0.

Causal authority history:
- PROPOSAL -> DECISION -> ACTION: PASS.

## Product conclusion

The real 9B is now physically attached to the production ORION control plane.

The model is a semantic governor, not an authority source:
- it proposes registered operations;
- ORION freezes/normalizes/authorizes;
- human approval remains ORION-owned;
- resume cannot rewrite approved work;
- cloud escalation enters an ORION-owned queue;
- no raw Hand or provider authority is exposed to the model.

## Next bounded slice

V3-RUN-046: ingest a cloud specialist response back into the Local Event Exchange
as immutable advisory REVIEW evidence bound to the exact queued request.

Cloud response ingestion must not:
- mint approval;
- create ACTION truth;
- execute a Hand;
- mutate the frozen request;
- grant provider/model authority.
