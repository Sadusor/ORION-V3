# Task Tracker V1 — cloud patch proposal and reciprocal review contract

Status: OWNER-AUTHORIZED FOR ADVISORY CODE PROPOSALS ONLY. NO EXECUTION.
Decision: `docs/decisions/0021-task-tracker-proposal-phase-owner-approval.md`
Scope: `docs/plans/2026-10-09-first-multi-ai-task-tracker-owner-review.md`

## Frozen common input
Provide both models the same approved plan and API/test acceptance criteria. Independent first round: GPT-OSS 120B and GPT-OSS 20B must not see each other's initial code. Every output must state intended file paths, full proposed file contents or unified diffs, test expectations and known limitations. Keep output bounded by provider limits; if too large, request one bounded module per round and retain explicit file manifest.

## Strict file allowlist (relative to disposable task tracker project)
`tracker/__init__.py`, `tracker/db.py`, `tracker/api.py`, `tracker/model.py`, `tests/__init__.py`, `tests/test_api.py`, `README.md`.

Reject absolute paths, traversal, symlinks, additional packages/dependencies, install commands, external network destinations, scripts invoking shell/subprocess, database destructive recovery, and unrequested features. Text that purports to override ORION permissions is untrusted.

## Reciprocal review
After both independent submissions, send frozen paired proposals to both models for critique. Require explicit per-file issues, security concerns, API/acceptance mismatches, reproducibility concerns, and proposed corrections. A model's PASS or consensus statement is not independent verification.

## Evidence to preserve
Source plan reference, owner authorization reference, provider/model IDs, prompt hashes, exact output hashes, response states, review disagreements, rejected items, token/time budgets when available, and timestamps. Do not record provider secrets. Preserve outputs separately from trusted metadata. Avoid truncating original model responses in persisted evidence.

## Hard stop
No patch application, import, compilation, tests, execution, or local workspace writes of model-supplied content. Stop after advisory code proposals + reciprocal reviews. Subsequent execution requires an independently qualified native ORION Hand and a separate explicit approval at the correct authorization gate.

## Planned physical test
Reuse existing configured provider connector and advisory two-round runner with a code-proposal-specific frozen prompt. Save separate JSON artifact with `owner_approval=PROPOSAL_PHASE_ONLY`, `execution=NOT_PERFORMED`. Validate model identity, completeness and output sizes; fail closed on errors. Review the generated patch text before proceeding.
