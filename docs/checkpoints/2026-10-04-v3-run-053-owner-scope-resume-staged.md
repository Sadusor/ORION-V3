# V3-RUN-053 — owner-authorized scope resume staged

Date: 2026-10-04

## Purpose

Prove the first explicit owner-resume path after ORION has stopped a task in
`waiting_owner`.

The owner may add one exact named search scope.

The 9B may then propose only:
- the still-missing exact basename(s);
- only the newly owner-authorized named root.

The model may not rewrite:
- the prior completion requirement;
- the exhausted prior scope;
- the owner amendment;
- trusted filesystem bindings;
- canonical task state.

## Physical setup

Initial owner objective:
- find `pyproject.toml`;
- find `__ORION_RUN053_OWNER_SCOPE_TARGET__.txt`;
- initial scope: `active_project`.

The gate first proves the synthetic target does not exist in the V3 worktree.

A controlled second real filesystem root is then created inside the gate's
temporary workspace and bound by ORION to the logical named root:
`orion_artifacts`.

That controlled root contains:
`__ORION_RUN053_OWNER_SCOPE_TARGET__.txt`.

No absolute root is exposed to the model.

## Initial path

1. 9B selects `fs.search_exact` for both names in `active_project`.
2. real pinned OpenJarvis Hand executes once.
3. target is missing.
4. ORION progress = `NEEDS_NEXT_STEP`.
5. ORION continuation = `OWNER_INPUT_REQUIRED`.
6. task status = `waiting_owner`.

## Owner amendment

The owner-resume contract appends one immutable `DECISION`:

- actor kind: `owner`;
- authority: `owner`;
- choice: `provide_new_search_scope`;
- prior location: `active_project`;
- new location: `orion_artifacts`;
- missing name remains exact;
- automatic retry before owner input = false.

The old progress and continuation Event payload hashes must remain unchanged.

Task transition:
`waiting_owner -> queued`

The exact same owner amendment is idempotent.

Repeating the exhausted `active_project` scope is blocked.

## Resume packet

The 9B receives only:
- exact missing names;
- new named location;
- prior logical locations;
- effective logical locations;
- owner authority marker.

It never receives:
- absolute trusted paths;
- Action Lease;
- raw filesystem binding.

## Resume proposal gate

`dispatch_owner_resumed_search(...)`

The resumed proposal must match the owner amendment exactly.

Attempts to:
- add a filename;
- omit/change a filename;
- use the old scope;
- use another scope;
- choose another capability

are denied before a canonical resumed proposal is created.

The accepted resumed PROPOSAL is parented directly to the exact owner-input
Event.

## Resumed real Hand

The real pinned OpenJarvis filesystem-search Hand receives an ORION trusted
binding:

`orion_artifacts -> controlled temporary root`

The 9B sees only the logical name `orion_artifacts`.

Required evidence:
- exact target basename found;
- searched location exactly `orion_artifacts`;
- trusted absolute path leak = 0.

## Cumulative completion

ORION combines:
- prior verified evidence that found `pyproject.toml`;
- resumed verified evidence that found the missing target.

Only cumulative verified evidence may transition the task to:
`COMPLETED`.

The original required exact names remain unchanged.

The effective owner-authorized locations become:
- `active_project`;
- `orion_artifacts`.

The cumulative progress DECISION is parented to the resumed RESULT and is
idempotent.

## Canonical event chain

Expected exact types:

1. PROPOSAL — initial search
2. ACTION
3. EVIDENCE
4. RESULT
5. DECISION — initial progress
6. DECISION — continuation / waiting_owner
7. DECISION — owner scope amendment
8. PROPOSAL — resumed search
9. ACTION
10. EVIDENCE
11. RESULT
12. DECISION — cumulative progress

Critical causal bridge:

`continuation -> owner amendment -> resumed PROPOSAL`

## Restart

Final `completed` task state and all 12 canonical Events must survive SQLite
close/reopen.

## Physical-gate note

The owner amendment in RUN-053 is a deterministic fixture inside an explicitly
owner-approved Remote gate run.

RUN-053 proves the backend authority/state contract.

Interactive phone/UI entry of the scope amendment is a later surface-integration
slice; this gate does not claim that UI is already implemented.

## PASS meaning

PASS proves ORION can safely stop, accept an explicit owner scope extension,
resume once under the exact amendment, execute one real bounded Hand action and
complete the original task from cumulative verified evidence without allowing
the local model to rewrite authority.
