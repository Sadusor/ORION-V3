# V3-RUN-055 — frozen cross-project read authority PHYSICAL PASS

Date: 2026-10-04

## Evidence

Authoritative Remote session:
`1ec9aea25e37`

Remote source SHA:
`5c74ea7999266afdc75e90bc765539b3189cbee5`

Exact V3 SHA:
`2caf9c1c5432e8f57d785a730805f9fc3e73e1da`

Remote result:
- state: completed
- exit_code: 0
- result: PASS

Regression suite:
- 255 passed in 21.81 s

## Physically proven

Capability:
`workspace.search_exact`

Semantic scope:
`registered_projects`

Frozen project set:
- `project-alpha`
- `project-beta`

Real Hand:
`openjarvis.tool.orion_filesystem_search.v1`

Real projects searched:
2

Real matches:
2

Both projects contained the same relative path.

ORION preserved distinct provenance identity using:
`project_id + revision + relative_path`

Same-relative-path provenance collision:
0

## Provenance carried

Verified cross-project matches retained:
- logical project ID;
- human project name;
- repo identity;
- revision;
- trust class;
- license state;
- no-cloud policy;
- registry version/hash;
- safe relative path;
- provenance identity hash.

Trusted absolute root leak:
0

## Authority / replay

Canonical chain:
`PROPOSAL -> ACTION -> EVIDENCE -> RESULT`

Duplicate workspace dispatch:
BLOCKED

## Registry-change falsifier

A second workspace proposal was frozen.

The owner then changed one registered project's revision before execution.

Result:
`workspace_scope_stale`

Hand executions after stale detection:
0

## Model / cloud

Local model calls:
0

External provider calls:
0

## Conclusion

Cross-project read authority is physically proven.

ORION can resolve a semantic registered-project scope, freeze its exact registry
state, issue one bounded read-only lease to the proven OpenJarvis Hand and
return provenance-bearing evidence without exposing local trusted roots.

Ordinary read/refusal examples now move to the batched Usage Scenario Suite.
