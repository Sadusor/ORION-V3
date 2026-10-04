# Decision: Cross-project read architecture and Usage Scenario Suite

Date: 2026-10-04
Status: ACCEPTED DIRECTION

## Why this decision exists

RUN-049 through RUN-053R proved the V3 read-only authority loop from owner
language through real PC evidence, deterministic task progress, waiting-owner
continuation and explicit owner resume.

That work also exposed an important product distinction:

`execution scope != information-discovery scope`

Blocking arbitrary locations is correct.
Trapping normal read-only discovery inside `active_project` is not.

Developers work across many repos, donor projects, old prototypes and reference
implementations.

## Accepted authority model

Scope is split into three independent axes.

### 1. Trust class

Examples:
- `owner_project`
- `donor_repo`
- `shared_or_client`
- `cloud_derived`

Trust class affects:
- local readability;
- write eligibility;
- cloud egress policy;
- license policy;
- memory promotion policy.

### 2. Access class

Examples:
- read-only
- bounded modification
- consequential/system

A read grant never turns into a write grant.

Search evidence is inert.

### 3. Authorization lifetime

Examples:
- owner command / one task
- one Action Lease
- explicit standing owner grant

A scope used once in a task is not silently promoted to permanent authority.

## Project / Workspace Registry

Build one canonical ORION registry.

The model never supplies local absolute roots.

Each project entry should eventually carry:
- `project_id`
- human `name`
- repo identity
- current revision / revision source
- trusted local root binding
- trust class
- archive state
- read policy
- write policy
- no-cloud / egress policy
- license state for donor repos
- tags / groups
- canonical version

Registry mutation is owner-only ORION state.

Models may read registry-safe metadata but cannot:
- add/remove projects;
- change trusted roots;
- change group membership;
- change trust class;
- change egress/write policy.

## Semantic scopes

First-class semantic scopes should include:
- `active_project`
- a specific registered project ID
- owner-defined `project_group:<id>`
- `registered_projects`
- `donor_repos`
- `archived_projects` only when explicitly named

A model proposes a semantic scope.

ORION resolves that scope into an exact frozen project set.

The resolved set is:
- capped;
- logged;
- visible to the owner as an audit echo;
- frozen for the execution lease.

A group ID is a capability-like scope token.
The model may name a group but may not compose/change group membership.

## Owner authorization for cross-project reads

For already registered ordinary owner projects:

An unambiguous owner natural-language command is sufficient authorization for
read-only search.

Example:
`check my other registered projects for this implementation`

ORION resolves the semantic scope and emits an audit line such as:

`Searching 4 registered projects: PayDay, ORION-V3, Orion-Copilot, Prototype`

This is not an additional approval gate.

Require owner clarification/approval when:
- semantic scope is ambiguous;
- project is sensitive/restricted;
- archived-restricted scope is requested;
- a new trust boundary is crossed;
- code will leave the machine;
- write/copy/mutation is proposed.

## Provenance

Cross-project evidence must carry at least:
- logical `project_id`
- human project name
- repo identity
- revision / commit SHA when available
- relative path only
- content hash
- retrieval scope / lease identity reference
- trust class
- license state for donor code

Never expose absolute local roots to models.

Two identical relative paths from different projects remain distinct evidence.

## Cloud egress is a separate authority event

Local read authorization does not imply cloud egress authorization.

Flow:

`owner request -> local scope resolution -> local read evidence -> egress policy -> bounded cloud packet -> REVIEW`

Every cloud packet containing project code should record:
- which logical projects contributed data;
- which provider/model received it;
- revision/provenance;
- exclusions due to `no_cloud`;
- packet truncation.

A `no_cloud` project is excluded rather than silently sent.

## Cross-project mutation

Search evidence never implies mutation authority.

Any future cross-project code movement must be a distinct named capability, not
an emergent read+write shortcut.

Future primitive:
`project.copy_from_project` or equivalent.

It must be:
- source-project explicit;
- destination-project explicit;
- license/trust checked;
- owner-approved by default;
- provenance-preserving;
- separate from ordinary file write.

Do not allow one multi-project diff/action to mutate multiple projects.

## Memory

Memory stores:
- decisions;
- lessons;
- compact reusable patterns;
- pointers to provenance/evidence.

Memory should not mirror source code.

Code remains in the source project and is retrieved on demand.

Model may propose that something is reusable.
Model does not directly promote canonical memory.

Memory promotion is ORION policy and/or owner authority.

## Retrieval stack

Preferred order:

1. ORION canonical memory/pointers
2. exact filesystem search
3. symbol index / Serena-like lookup
4. BM25 / Aider-style repo map
5. hierarchical triage for very large corpora
6. optional semantic/embedding retrieval

All retrieval layers must emit the same provenance-bearing evidence contract.

Embeddings are never sole authority.

## Testing strategy change

The project now moves from:
`one normal usage example = one isolated RUN`

to:

`new authority primitive = isolated gate`
`ordinary read/refusal scenarios = batched Usage Scenario Suite`

Batch:
- normal read-only search;
- cross-project retrieval;
- provenance checks;
- disambiguation;
- memory lookup;
- waiting-owner/resume regressions;
- arbitrary-path refusals;
- hostile cloud REVIEW regressions;
- idempotency.

Keep isolated:
- any new write primitive;
- first cross-project copy;
- first non-active-project cloud egress;
- registry mutation during active task;
- cancellation semantics;
- license-tainted copy/reuse;
- memory promotion/write;
- registry-change vs in-flight lease.

## Usage Scenario Suite V1 target

Initial suite should aim for 18 independent scenarios:

1. current-project exact file search
2. missing file -> NEEDS_NEXT_STEP
3. owner expands scope -> resume -> COMPLETED
4. arbitrary absolute path -> blocked
5. search registered projects
6. donor-repo search with provenance
7. compare two projects
8. ambiguous project name -> disambiguation
9. archived project default-excluded
10. same relative path in two projects -> provenance distinct
11. donor license metadata carried
12. stale revision detected
13. bounded cloud analysis with provenance
14. no-cloud project excluded from cloud packet
15. hostile cloud REVIEW remains advisory
16. memory hit points to source evidence
17. retrieve project roadmap/docs
18. replay after registry/revision change -> explicit idempotency/failure semantics

Each scenario records:
- PASS/FAIL/BLOCKED
- wall time
- local-model calls
- Hand calls
- cloud calls
- projects/scopes resolved
- evidence count
- truncation
- reason for failure/block

## Immediate milestone sequence

1. Canonical Project/Workspace Registry foundation.
2. Deterministic semantic scope resolver.
3. Frozen cross-project read scope on existing lease/evidence path.
4. Provenance-enriched cross-project evidence.
5. Usage Scenario Suite V1.
6. Isolated first non-active-project cloud egress gate.
7. Later: license-aware cross-project copy.
8. Memory promotion policy.
9. Retrieval layering.
10. cancellation/replay/registry-mutation hardening.

## Core rule

`MODEL proposes; ORION resolves/freezes/authorizes/verifies.`

For cross-project work:

`OWNER authorizes semantic scope; ORION owns its exact project membership.`
