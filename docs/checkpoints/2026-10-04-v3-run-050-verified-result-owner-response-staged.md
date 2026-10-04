# V3-RUN-050 — verified RESULT to grounded owner response staged

Date: 2026-10-04

## Purpose

Close the first complete conversational production loop:

```
OWNER
 -> 9B semantic capability selection
 -> ORION canonical PROPOSAL
 -> ORION Action Lease
 -> real read-only OpenJarvis Hand
 -> ORION EVIDENCE
 -> deterministic ORION RESULT
 -> sanitized verified-result packet
 -> 9B owner-facing response
```

## New grounding boundary

`verified_result_packet(...)`

The governor may report only from an ORION RESULT that:
- belongs to the exact task;
- is EventType.RESULT;
- is `routine_capability_result`;
- carries deterministic `verification.status=PASS`;
- has an intact exact lineage:
  `PROPOSAL -> ACTION -> EVIDENCE -> RESULT`;
- preserves one action SHA across proposal/action/evidence/result;
- preserves exact event identities.

The packet removes:
- absolute trusted roots;
- Action-Lease identity/token;
- raw Hand prose;
- unverified donor state;
- file metadata not needed for owner reporting.

Packet authority is:
`verified_evidence_only`

## Physical task

Owner asks:

Find `pyproject.toml` and `gateway.py` inside `active_project` and tell me
where they are. Do not modify anything.

The gate performs a real filesystem search against the V3 worktree through the
same pinned OpenJarvis Hand used in RUN-049R.

## Owner-response contract

The 9B receives no tools on the reporting turn.

It receives only the verified result packet and must return structured JSON:
- `status`;
- `summary`;
- `found_paths`;
- `actions_performed`.

Required:
- `found_paths` equals every verified relative path exactly once;
- no invented path;
- `status=FOUND`;
- `actions_performed=["read_only_search"]`;
- summary does not claim edits, writes, publishes, approvals, deletes or creation;
- reporting does not mutate canonical Task/Event state.

## Security

A user-facing answer is not itself canonical RESULT truth.

The 9B is allowed to explain verified facts but not manufacture new evidence.

## Efficiency

If the pinned donor native extension already imports, RUN-050 reuses the
existing OpenJarvis environment without another `uv sync`. Native sync/build
runs only if the Rust import is unavailable.

## PASS meaning

PASS proves the full safe read-only conversational loop from owner language to
real PC evidence and back to an evidence-grounded owner answer.
