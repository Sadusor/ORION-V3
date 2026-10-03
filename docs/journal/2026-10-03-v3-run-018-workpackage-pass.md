# V3-RUN-018 — Coding Factory WorkPackage Gate Physical PASS

Date: 2026-10-03

Status: **PHYSICAL PASS**

## Transport evidence

ORION Remote source SHA:
`4544acdd1aebb23769392eff9bd4dc5f78e8dc68`

Named task:
`v3-current-gate`

Session ID:
`3c93b3f33491`

Session result:
`PASS`

## Exact observed output

```text
V3_RUN_ID> V3-RUN-018
V3_REGRESSION> RUN
77 passed in 3.02s
V3_REGRESSION> PASS
CODING_FACTORY_WORKPACKAGE_PROBE> RUN
ARTIFACT_DEDUPLICATION> PASS
ARTIFACT_TAMPER_DETECTION> PASS
DETERMINISTIC_PACKAGE_IDENTITY> PASS
PACKAGE_MANIFEST_RELOAD> PASS
OUT_OF_SCOPE_FILE> DENIED
OUT_OF_SCOPE_PATCH_TARGET> DENIED
NON_EXACT_BASE_SHA> DENIED
PACKAGE_BOUND_REVIEW_DECISION_CHAIN> PASS
CANDIDATE_EXECUTION_AUTHORITY> NONE
CROSS_PACKAGE_REVIEW_REUSE> DENIED
PACKAGE_BLACKBOARD_REOPEN_PERSISTENCE> PASS
NETWORK_MODEL_EXECUTION_DEPENDENCY> NONE
CODING_FACTORY_WORKPACKAGE_GATE> PASS
STATUS> PASS
ORION_NAMED_TASK_TO_V3> PASS
STATUS> PASS
```

## Exact tested V3 SHA

`6ef6e9ccd3bea7a9e56c5761173ed76609c47ddc`

## What this physically proves

- content-addressed artifact deduplication;
- direct artifact tamper detection on read;
- deterministic WorkPackage identity/hash;
- deterministic manifest reload with artifact integrity revalidation;
- exact Git base SHA is required;
- out-of-scope FILE artifacts are denied;
- PATCH artifacts must declare target paths and out-of-scope targets are denied;
- candidate PROPOSAL -> independent REVIEW -> ORION DECISION chain is package/hash-bound;
- a review from package A cannot be reused to decide package B;
- an accepted candidate still has `execution_authority=false`;
- no ACTION Event is created by candidate acceptance;
- WorkPackage + Event Blackboard survive close/reopen;
- no cloud/model/execution dependency was required for this gate.

## Architectural meaning

ORION now has the output-side foundation of the Coding Factory:

```text
cloud coder output bytes
 -> immutable Artifact Store
 -> exact WorkPackage bound to project/task/base SHA/scope
 -> independent reviewer record
 -> ORION candidate decision
```

This is still candidate work only. No package is executable yet.

## Next gate

Before any WorkPackage can touch a real checkout, ORION must prove attempt ownership / lease / checkpoint / Stop semantics and an isolated exact-SHA worktree execution boundary.

Only after that should V0 apply one harmless package mechanically and verify exact changed paths and resulting Git diff/SHA.

## Agent benchmark position

Yes: after the execution boundary is proven, benchmark at least one mature coding agent/semantic Coding Hand on the PC against the same bounded coding case.

Candidate classes already qualified/audited include OpenHands/Software Agent SDK and Claude Code-style coding Hands.

The agent remains a replaceable Hand under ORION authority. It does not own Task state, permission, Memory, PASS/FAIL, or acceptance.
