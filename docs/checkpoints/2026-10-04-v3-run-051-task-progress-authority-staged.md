# V3-RUN-051 — ORION-owned task progress authority staged

Date: 2026-10-04

## Purpose

Prove that task completion/progress is canonical ORION authority, not a model
self-report.

The local governor still chooses semantic capabilities.

The model receives no task-completion/status tool.

After a deterministically verified exact-search RESULT, ORION alone decides:
- `COMPLETED`; or
- `NEEDS_NEXT_STEP`.

## New production contract

`decide_exact_search_task_progress(...)`

Input:
- exact Task ID;
- exact verified RESULT Event ID;
- deterministic completion contract:
  - required exact basenames;
  - required locations.

The function first rebuilds the sanitized, lineage-verified RESULT packet.

It requires:
- capability = `fs.search_exact`;
- searched locations exactly equal the completion contract;
- only verified matches contribute to completion.

State:
- every required basename verified -> `COMPLETED`;
- one or more required basenames absent -> `NEEDS_NEXT_STEP`.

## Atomicity

Task status update and canonical `DECISION` Event are committed in one SQLite
transaction.

The DECISION is parented directly to the verified RESULT.

Authority marker:
`orion_deterministic_policy`

Repeated evaluation of the same RESULT + same completion contract:
- returns the exact existing DECISION;
- `duplicate=true`;
- does not create another Event.

A completed task cannot be reopened by a later progress decision.

## Physical cases

### A — complete

Real Hand searches the V3 worktree for:
- `pyproject.toml`;
- `gateway.py`.

Both are physically present.

Expected:
- verified Hand RESULT;
- ORION state = `COMPLETED`;
- task status = `completed`.

### B — incomplete

Real Hand searches for:
- `pyproject.toml`;
- `__ORION_RUN051_PROVABLY_MISSING_5D6A2C91__.nope`.

The gate first asserts the synthetic basename does not exist in the V3 worktree.

Expected:
- verified Hand RESULT;
- missing synthetic basename recorded;
- ORION state = `NEEDS_NEXT_STEP`;
- task status = `needs_next_step`.

## Required event chain

For both tasks:

`PROPOSAL -> ACTION -> EVIDENCE -> RESULT -> DECISION`

The DECISION must be parented directly to RESULT.

## Restart

Both task states and both DECISION Events must survive store close/reopen.

## Authority rule

`MODEL chooses semantic next action; ORION decides canonical progress/completion.`

## PASS meaning

PASS proves ORION can distinguish a finished objective from an incomplete one
using verified real-PC evidence, without trusting a model's own claim that the
task is done.
