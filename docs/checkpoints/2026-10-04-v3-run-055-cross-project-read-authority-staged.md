# V3-RUN-055 — frozen cross-project read authority staged

Date: 2026-10-04

## Why this remains isolated

RUN-054 physically proved the canonical Project/Workspace Registry.

Cross-project read is the final new authority primitive required before ordinary
examples move into the batched Usage Scenario Suite V1.

This gate proves the authority/evidence primitive itself, not a collection of
UX examples.

## Capability

Logical capability:
`workspace.search_exact`

Model-facing semantic form for later suites:
- exact basenames;
- one semantic scope token.

The model never supplies:
- absolute roots;
- project root composition;
- recursion/depth/result policy;
- Action Lease;
- raw trusted bindings.

## Proposal freeze

ORION resolves the semantic scope through the canonical Workspace Registry.

The canonical PROPOSAL freezes:
- exact basenames;
- semantic scope token;
- resolution ID;
- project IDs;
- human names;
- repo identities;
- trust classes;
- archive state;
- no-cloud markers;
- license states;
- revisions;
- registry versions;
- registry hashes;
- ORION-owned execution policy.

Absolute trusted roots are not stored in the proposal.

## Execution

Immediately before lease issuance/Hand execution, ORION reloads each registered
project and requires it to still exactly match the frozen:
- registry version;
- registry hash;
- revision;
- name;
- repo identity;
- trust class;
- archive state;
- no-cloud state;
- license state.

Any change after freeze:
`workspace_scope_stale`

and no ACTION/Hand execution occurs.

## Hand reuse

No new filesystem executor is introduced.

ORION reuses the physically proven pinned OpenJarvis
`orion_filesystem_search` Hand.

The Action Lease's logical `locations` are the frozen project IDs.

ORION supplies:
`project_id -> absolute trusted root`
out of band.

The model never sees those roots.

## Provenance-bearing evidence

Each verified match is enriched with:
- project ID;
- project human name;
- repo identity;
- revision;
- trust class;
- archive state;
- no-cloud marker;
- license state;
- registry version/hash;
- relative path;
- basename/kind;
- path-identity SHA256.

The path identity hashes:
`project_id + revision + relative_path`

so identical relative paths in different projects remain distinct evidence.

This first search primitive does not claim file-content hashing because exact
basename discovery does not read file contents.

## Physical fixture

Create two real temporary registered owner projects:

`project-alpha`
`project-beta`

Both contain the same relative path:

`src/__ORION_RUN055_SHARED_SOLUTION__.py`

Their contents differ, but RUN-055 only tests discovery/provenance, not content
retrieval.

Beta has:
`no_cloud=true`

## Required physical proofs

- frozen scope resolves exactly both projects;
- canonical proposal contains no trusted absolute roots;
- real OpenJarvis Hand searches both roots;
- two matches are verified;
- same relative path has distinct provenance identity;
- project names/repo identities/revisions/trust/license/no-cloud survive;
- verified RESULT contains no absolute roots;
- causal chain is exactly:
  `PROPOSAL -> ACTION -> EVIDENCE -> RESULT`;
- duplicate proposal dispatch is BLOCKED.

## Registry-change falsifier

Create a second frozen cross-project proposal.

Then owner-updates one registered project revision before execution.

Required:
- execution denied with `workspace_scope_stale`;
- task history remains PROPOSAL only;
- stale proposal Hand executions = 0.

## Gate mode

- local model calls: 0
- external provider calls: 0
- real pinned OpenJarvis Hand: yes

## PASS meaning

PASS proves ORION can safely convert a semantic multi-project scope into one
frozen, provenance-preserving read-only lease without exposing trusted paths or
allowing registry drift to silently change what gets searched.

After PASS, ordinary usage examples move to Usage Scenario Suite V1.
