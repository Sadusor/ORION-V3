# ORION Usage Scenario Suite V1 — staged

Date: 2026-10-04
Run ID: `V3-USAGE-SUITE-001`

## Testing strategy

This is the first deliberate switch away from:

`one ordinary usage example -> one isolated RUN`

New policy:

- new authority/mutation/egress primitive -> isolated gate;
- ordinary read/refusal workflows -> batched usage suite.

Every scenario reports independently:
- `PASS`;
- `BLOCKED_EXPECTED`;
- or `FAIL`.

The suite fails only when one or more scenarios produce an unexpected `FAIL`.

Each scenario also reports:
- wall time;
- local-model calls;
- Hand calls;
- cloud calls;
- relevant evidence/state details.

## Production components exercised

Where appropriate the suite uses:
- real `qwen35-9b-orion:latest`;
- thinking ON;
- ctx 4096;
- canonical Workspace Registry;
- semantic scope resolution;
- real pinned OpenJarvis filesystem-search Hand;
- deterministic ORION evidence verification;
- ORION task progress;
- waiting-owner continuation;
- explicit owner resume;
- frozen workspace scope;
- provenance-bearing cross-project evidence.

No cloud provider is called in Suite V1.

## Scenario matrix

### S01 — NL current-project search

Owner-like request:
`Find README.md in the active project.`

Expected:
- real 9B chooses `fs.search_exact`;
- exact semantic args;
- real Hand;
- verified `README.md`.

### S02 — NL registered-project search

Owner-like request:
`Search my registered projects for shared.py.`

Expected:
- real 9B chooses workspace exact search;
- semantic scope = `registered_projects`;
- real cross-project Hand;
- provenance identifies Active + Other projects.

### S03 — NL donor-repo search

Owner-like request:
`Search our donor repositories for donor_pattern.py.`

Expected:
- semantic scope = `donor_repos`;
- donor-only result;
- license = Apache-2.0.

### S04 — missing file

Target exists outside active project.

Initial search:
`active_project`

Expected:
`NEEDS_NEXT_STEP`.

### S05 — exhausted search continuation

Continue S04.

Expected:
- `OWNER_INPUT_REQUIRED`;
- task = `waiting_owner`;
- automatic retry ACTION count = 0.

### S06 — owner scope expansion / resume

Owner adds:
`orion_artifacts`

Expected:
- 9B receives bound zero-argument continuation control;
- second real Hand search;
- cumulative verified task = `COMPLETED`.

### S07 — arbitrary absolute path

Attempt semantic scope:
`C:\\`

Expected:
`BLOCKED_EXPECTED`
with `unknown_semantic_scope`.

No canonical mutation.

### S08 — archived project default exclusion

Attempt to treat archived project as normal active project.

Expected:
`BLOCKED_EXPECTED`
with `archived_project_not_explicit`.

### S09 — owner-defined group search

Scope:
`project_group:work`

Expected:
- exact owner-authored membership resolved;
- real Hand search;
- matches in Active + Other.

### S10 — same path provenance collision

Both Active + Other contain:
`src/shared.py`

Expected:
- same relative path;
- distinct project IDs;
- distinct provenance identity hashes.

### S11 — no-cloud metadata

Client project has:
`no_cloud=true`

Expected:
- resolution preserves it;
- model-safe metadata preserves it.

No egress is attempted.

### S12 — blast-radius project cap

Resolve `registered_projects` with cap smaller than membership.

Expected:
`BLOCKED_EXPECTED`
with `scope_project_cap_exceeded`.

### S13 — registry change after freeze

Freeze cross-project proposal, then owner changes one project's revision.

Expected:
`BLOCKED_EXPECTED`
with `workspace_scope_stale`.

Hand executions after stale detection:
0.

### S14 — proposal replay

Execute workspace proposal successfully, then dispatch same proposal again.

Expected:
`BLOCKED_EXPECTED`
with `proposal_already_dispatched`.

### S15 — project roadmap/document retrieval

Find:
`ROADMAP.md`

Expected real verified path:
`docs/ROADMAP.md`.

### S16 — already complete -> stop

Use S15 verified evidence to mark objective complete.

Expected:
- `COMPLETE_NO_ACTION`;
- no extra continuation Event.

### S17 — donor provenance retained

Reuse S03 physical evidence.

Expected:
- trust class = donor_repo;
- license = Apache-2.0;
- repo identity preserved.

## Deliberately excluded from Suite V1

These require new or still-isolated authority primitives:

- non-active-project code egress to cloud;
- cross-project code copy;
- any new write/edit primitive;
- license-tainted copy/reuse;
- memory promotion/write;
- cancellation mid-multi-project search;
- registry mutation while a live persisted lease is in flight;
- automated cloud fallback.

They will not be smuggled into the usage suite merely to increase scenario count.

## PASS meaning

PASS does not mean every future ORION workflow is complete.

It means the already-proven read-only authority primitives work together across
a useful set of normal owner workflows in one batched physical run, with
independent scenario outcomes and useful performance/call-count statistics.
