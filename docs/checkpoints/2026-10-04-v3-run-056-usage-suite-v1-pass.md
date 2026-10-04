# V3-RUN-056 / Usage Scenario Suite V1 — PHYSICAL PASS

Date: 2026-10-04

Logical suite ID:
`V3-USAGE-SUITE-001`

Remote-compatible run ID:
`V3-RUN-056`

## Evidence

Authoritative Remote session:
`454db6c20c5c`

Remote source SHA:
`126dbafa37dcff1f782a3cb07d1de6aa5f5dcb1e`

Exact V3 SHA:
`3e0aefaf88748932380bf7ab72124587117f4b7a`

Remote result:
- state: completed
- exit_code: 0
- result: PASS

## Suite totals

Scenarios:
17

PASS:
12

BLOCKED_EXPECTED:
5

Unexpected FAIL:
0

Local governor:
`qwen35-9b-orion:latest`

Thinking:
ON

Context:
4096

Real model calls:
4

Real Hand calls:
8

Cloud calls:
0

Scenario wall-time sum:
14.516 s

## Scenario outcomes

### PASS

S01 — NL current-project exact file search

9B:
- `fs.search_exact`
- `README.md`
- `active_project`

Verified:
`README.md`

S02 — NL cross-project registered-project search

9B:
- workspace exact search
- `shared.py`
- semantic scope `registered_projects`

Physical matches:
- project-active
- project-other

S03 — NL donor-repo search with license provenance

9B:
- workspace exact search
- `donor_pattern.py`
- scope `donor_repos`

Physical provenance:
- project-donor
- license: Apache-2.0

S04 — missing file -> NEEDS_NEXT_STEP

Verified missing:
`__ORION_SUITE_RESUME_TARGET__.txt`

S05 — exhausted search -> waiting_owner without retry

State:
`OWNER_INPUT_REQUIRED`

Task:
`waiting_owner`

Automatic retry ACTIONs:
0

S06 — owner expands scope -> bound resume -> COMPLETED

Bound continuation model arguments:
0

Final state:
`COMPLETED`

S09 — owner-defined project-group search

Resolved:
- project-active
- project-other
- project-client

Physical matches:
- project-active
- project-other

S10 — same relative path remains provenance-distinct

Path:
`src/shared.py`

Projects:
- project-active
- project-other

Distinct provenance identity:
PASS

S11 — no-cloud policy survives resolution

project-client:
`no_cloud=true`

S15 — retrieve project roadmap/document

Verified:
`docs/ROADMAP.md`

S16 — already complete -> stop, no extra action

Continuation:
`COMPLETE_NO_ACTION`

Extra Events:
0

S17 — donor provenance remains attached

Trust:
`donor_repo`

License:
`Apache-2.0`

Repo identity:
preserved

### BLOCKED_EXPECTED

S07 — arbitrary absolute path scope

Denial:
`unknown_semantic_scope`

S08 — archived project default exclusion

Denial:
`archived_project_not_explicit`

S12 — registered-project blast-radius cap

Denial:
`scope_project_cap_exceeded`

S13 — registry change invalidates frozen search

Denial:
`workspace_scope_stale`

Hand calls after stale detection:
0

S14 — workspace proposal replay

Denial:
`proposal_already_dispatched`

## Conclusion

The testing-strategy pivot is validated.

Ordinary read/refusal workflows can now be batched without losing per-scenario
diagnostics.

The suite physically proves that multiple already-qualified ORION primitives
compose correctly in one run:
- local natural-language governor;
- deterministic current-project read;
- canonical Workspace Registry;
- semantic cross-project scope;
- owner groups;
- donor scope;
- provenance;
- no-cloud metadata;
- waiting-owner continuation;
- explicit owner resume;
- replay and stale-scope refusal.

## Next authority milestone

The next new trust boundary should remain isolated:

`cross-project local evidence -> cloud egress policy -> bounded cloud REVIEW`

Required properties:
- local read authorization does not imply cloud egress;
- `no_cloud=true` evidence is excluded;
- owner-visible egress record identifies projects/provider/model;
- provenance survives into the cloud packet;
- packet truncation/exclusion is explicit;
- cloud REVIEW remains structurally non-authoritative;
- excluded projects are reported to the local governor;
- zero cloud authority over project selection, reads, writes or Hands.

After this authority primitive is individually proven, cloud-assisted comparison
scenarios can be added to a later Usage Scenario Suite.
