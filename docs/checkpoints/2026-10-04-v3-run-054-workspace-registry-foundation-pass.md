# V3-RUN-054 — canonical Workspace Registry foundation PHYSICAL PASS

Date: 2026-10-04

## Evidence

Authoritative Remote session:
`87d7c683ee3a`

Remote source SHA:
`ac9a0ffb2e21595217149420fc9ea2005d81c973`

Exact V3 SHA:
`56a2a133044fb0345e0cd0592eb3f8f3af9bc60a`

Remote result:
- state: completed
- exit_code: 0
- result: PASS

Regression suite:
- 248 passed in 17.94 s

## Physically proven registry properties

- 5 project entries created;
- owner-only project mutation;
- owner-only project-group membership mutation;
- initial registry versioning;
- immutable revision/checksum model;
- direct current trusted-root tamper: BLOCKED;
- direct current group-membership tamper: BLOCKED.

## Physically proven semantic scopes

- `active_project`
- `registered_projects`
- `donor_repos`
- `archived_projects`
- `project_group:work`

Archived projects are default-excluded unless explicitly requested.

Project-count cap:
BLOCKED when exceeded.

## Provenance/policy metadata

Model-safe scope metadata carries:
- logical project IDs/names;
- repo identity;
- trust class;
- archive state;
- no-cloud policy;
- license state;
- revision;
- registry version/hash.

Trusted absolute root leak:
0

Donor license metadata:
PASS

No-cloud metadata visibility:
PASS

## Frozen resolution

A previously resolved scope remained unchanged after an owner registry update.

A new resolution reflected:
- new registry version;
- new revision;
- new resolution ID.

## Gate mode

- model calls: 0
- Hand executions: 0
- external provider calls: 0

## Conclusion

The Project/Workspace Registry is physically proven as a canonical,
owner-controlled source of semantic cross-project scope.

The next isolated authority primitive is the cross-project read capability that
binds one frozen ScopeResolution into a read-only lease and emits
provenance-bearing evidence.

After that primitive passes, ordinary read/refusal examples move to the batched
Usage Scenario Suite V1.
