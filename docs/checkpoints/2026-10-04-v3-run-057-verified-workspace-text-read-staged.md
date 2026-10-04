# V3-RUN-057 — evidence-bound workspace text read staged

Date: 2026-10-04

## Why this is isolated

Usage Scenario Suite V1 passed.

The next planned authority boundary is cross-project cloud egress.

Before code can be sent to a cloud reviewer, ORION needs a safe primitive for
retrieving file contents from cross-project discovery evidence.

RUN-057 proves that read primitive separately instead of hiding file-content
access inside the egress gate.

## Principle

The model never supplies a filesystem path.

Model-facing control:
`orion_read_verified_text`

Only argument:
`path_identity_sha256`

The identity must match exactly one already verified
`workspace.search_exact` RESULT match.

## Provenance binding

The previous workspace RESULT carries:
- project ID/name;
- repo identity;
- revision;
- registry version/hash;
- relative path;
- trust class;
- no-cloud;
- license state;
- file kind;
- size;
- modification timestamp;
- path identity SHA256.

Before reading, ORION requires the current registry entry to still match the
verified evidence.

## File race protection

Workspace search now preserves:
- `size_bytes`
- `modified_ns`

The text reader checks both against the current physical file before reading.

If the file changed after search:
`workspace_file_changed`

No read ACTION is appended.

This avoids silently reading a different file version under old search evidence.

## Path safety

ORION resolves:
`trusted project root + verified relative path`

The reader:
- requires containment under the trusted root;
- rejects symlink evidence;
- requires a regular file;
- accepts no arbitrary path from the model.

## Read bounds

Default:
32768 bytes

Maximum allowed:
262144 bytes

If file exceeds `max_bytes`:
- read is bounded;
- `truncated=true`;
- bytes read are explicit;
- content SHA256 covers exactly the bounded bytes returned.

UTF-8 is required for this first text primitive.

## Canonical chain

Successful read:

`workspace RESULT -> ACTION(read) -> EVIDENCE -> RESULT(text)`

Text RESULT carries:
- project provenance;
- safe relative path;
- evidence identity;
- content hash;
- bytes read;
- truncation flag;
- bounded text;
- `absolute_root_exposed=false`;
- authority = `verified_read_only_evidence`.

## Physical fixture

Two real registered temporary projects both contain:

`__ORION_RUN057_TARGET__.py`

Alpha additionally contains a 512-byte text file.

RUN-057 first performs a real pinned OpenJarvis cross-project search to obtain
verified path identities.

Then prove:

1. Alpha target can be read only by its exact verified evidence identity.
2. Returned content and SHA256 are exact.
3. Trusted absolute roots leak 0.
4. Forged evidence identity is BLOCKED before read ACTION.
5. 512-byte text read with max_bytes=64 returns exactly 64 bytes and
   `truncated=true`.
6. Beta file changed after search is BLOCKED with `workspace_file_changed`
   before read ACTION.
7. Alpha registry revision changed after search is BLOCKED with
   `workspace_evidence_stale` before read ACTION.
8. Successful read has exact causal chain.

## Gate mode

- local model calls: 0
- external provider calls: 0
- prerequisite real OpenJarvis workspace-search Hand: yes
- verified content reader: deterministic bounded ORION Hand

## PASS meaning

PASS proves cloud egress can later consume bounded, hashed, provenance-bound text
without allowing a model or cloud provider to invent local paths or silently
read changed files.
