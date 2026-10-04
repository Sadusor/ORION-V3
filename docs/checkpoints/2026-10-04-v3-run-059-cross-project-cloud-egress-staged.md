# V3-RUN-059R — cross-project cloud egress staged

Date: 2026-10-04

## Purpose

Prove the first cloud egress of code/content retrieved from multiple registered
projects.

Local read authorization must not imply cloud authorization.

This gate physically proves:
`verified local evidence -> ORION egress policy -> bounded prompt -> real Groq -> advisory REVIEW`.

## Fixture

Two real temporary registered projects:

### project-public
- trust: owner_project
- no_cloud: false
- contains a unique permitted sentinel.

### project-private
- trust: shared_or_client
- no_cloud: true
- contains a unique private sentinel.

Both files are:
1. found by real pinned OpenJarvis cross-project search;
2. read locally by the RUN-058 evidence-bound content reader.

Therefore local ORION can legitimately inspect both.

Only project-public may leave the machine.

## Egress policy

`build_cloud_egress_packet(...)`

Inputs:
only verified workspace-text RESULT events.

For each source, ORION rechecks:
- RESULT kind;
- task binding;
- authority = verified_read_only_evidence;
- absolute_root_exposed = false;
- text/content SHA256 integrity.

Policy:
- no_cloud=false -> eligible evidence;
- no_cloud=true -> excluded metadata only;
- all evidence excluded -> fail closed;
- total cloud prompt is bounded;
- packet truncation is explicit.

## Cloud prompt

Permitted evidence carries:
- project ID/name;
- repo identity;
- revision;
- safe relative path;
- path identity hash;
- source content hash;
- trust class;
- license state;
- source truncation;
- bounded content.

Excluded evidence carries only:
- logical provenance;
- exclusion reason = no_cloud.

The private file content/sentinel must not appear in the prompt.

Absolute trusted roots must not appear.

## Canonical owner-visible egress decision

Before network access, ORION appends a DECISION:

`cloud_egress_policy_decision`

It records:
- exact provider/model;
- purpose;
- prompt SHA256;
- included projects/files/hashes;
- excluded projects/files/reasons;
- packet truncation;
- authority = orion_deterministic_policy.

Raw code is intentionally not copied into the DECISION.

## Causal cloud request

The existing cloud specialist lane is reused.

The cloud PROPOSAL must be parented directly to the egress DECISION.

The request text must exactly equal the canonical bounded prompt.

## Real provider

Provider:
`groq`

Model:
`openai/gpt-oss-120b`

No fallback model is permitted.

The returned provider prompt SHA256 must equal the canonical packet SHA256.

This binds the actual network call to the local egress decision.

## REVIEW

Real provider response is ingested through the existing cloud-response path.

Required:
- Event type = REVIEW;
- parent = exact cloud request;
- provider/model exact;
- authority = advisory_only;
- no ACTION authority;
- no Hand authority;
- no tools;
- no fallback.

## Required privacy proof

The private project has a unique sentinel.

Required before and after live provider call:
- private sentinel in cloud prompt: 0;
- private sentinel in queued cloud request: 0;
- trusted absolute roots in prompt: 0.

The cloud may be told that a project was excluded by local policy, but receives
none of its code/content.

## Expected cloud event tail

After local search/read evidence is complete:

`DECISION(egress policy) -> PROPOSAL(cloud request) -> REVIEW(advisory)`

No cloud ACTION.

## PASS meaning

PASS proves ORION can use strong cloud reasoning on permitted cross-project
evidence without treating local read permission as permission to export every
project.

The owner/audit surface can see exactly which logical projects were included or
excluded, while the cloud remains non-authoritative.


## Final pre-staging hardening

Two additional invariants were added before Remote staging.

### Exact packet bound

The final REVIEW instruction is reserved inside `max_total_chars` before
evidence content is allocated.

Therefore the bound covers the complete provider prompt, not just evidence
blocks.

### Egress-decision-bound request identity

When a cloud request is parented to an egress policy DECISION, that exact
`parent_event_id` participates in the cloud request hash/dedupe identity.

Therefore two identical prompt strings authorized by two different egress
decisions do not silently collapse onto an older cloud request.

Legacy cloud requests without a causal parent keep their existing identity
semantics.
