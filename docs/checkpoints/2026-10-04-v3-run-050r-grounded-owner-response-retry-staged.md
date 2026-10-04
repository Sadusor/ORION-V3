# V3-RUN-050R — grounded owner-response retry staged

Date: 2026-10-04

## Prior attempt

V3-RUN-050 did not pass, despite the Remote UI surfacing a misleading Pass state to the owner.

Authoritative Remote session:
`a8f94fabee24`

Remote source SHA:
`c72c14d9556c4980d589101c3352c54050e968ef`

Observed:
- authoring preflight: PASS;
- regression suite: 221 passed;
- pinned OpenJarvis SHA: PASS;
- existing `openjarvis_rust` import: PASS;
- qwen35-9b-orion:latest thinking ON / ctx 4096: available;
- governor selected the correct semantic capability `fs.search_exact`.

Failure:
the model also supplied execution-policy knobs:
- `max_depth=10`;
- `max_results=10`;
- `recursive=true`;
- `reveal_containing_folders=true`.

The capability contract rejected the proposal before canonical PROPOSAL creation because `max_depth=10` exceeded the registered maximum.

No Hand executed.

## Architectural correction

The model should choose semantics, not execution policy.

For `fs.search_exact`, the governor-facing tool now exposes only:
- `exact_names`;
- `locations`.

ORION deterministically owns:
- recursive policy;
- max depth;
- max results;
- reveal policy.

The registry still normalizes the hidden parameters to canonical defaults:
- recursive = true;
- max_depth = 4;
- max_results = 50;
- reveal_containing_folders = false.

Defense in depth:
even if a model attempts to submit a hidden execution parameter outside the advertised tool schema, `dispatch_governor_tool()` denies it with:
`governor_hidden_parameter`.

## Why this is stronger

The prior schema technically advertised numeric bounds, but the 9B still attempted to over-control the execution plan.

RUN-050R narrows the authority boundary instead of relying on model compliance.

Principle:

`MODEL chooses WHAT; ORION chooses HOW BOUNDED`.

## Retry

RUN-050R keeps the same intended full conversational production loop:
- 9B selects semantic exact-name search;
- ORION applies canonical hidden execution defaults;
- real pinned OpenJarvis read-only Hand executes;
- deterministic verification creates RESULT;
- ORION validates RESULT lineage;
- sanitized verified-result packet reaches the 9B;
- the 9B returns a grounded owner-facing response;
- no invented paths or side effects;
- no canonical mutation from reporting.

## PASS meaning

PASS proves the end-to-end owner conversation loop while keeping execution-policy knobs outside model authority.
