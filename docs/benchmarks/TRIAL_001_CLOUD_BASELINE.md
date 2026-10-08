# Trial 001 — Single cloud model

Status: prepared, not executed or scored.

Use the exact frozen Task Ledger HTTP contract and common model submission protocol. Give the coding model only those two documents, never the reference implementation or evaluators.

Prompt: Implement a Python standard-library Task Ledger HTTP service satisfying the supplied contract. Return complete task_ledger package, at least 20 tests, and README. Use SQLite and loopback only. Do not claim unexecuted tests passed.

Record model ID, prompt hash, output hash, latency, tokens and file manifest. Save output as inert source text in a separate disposable workspace. Perform static inspection before execution. Do not run generated code until independent Windows confinement is qualified. Do not report a model score until independent evaluation has run. Repeat at least three independent trials per configuration with equal budgets.

The existing remote test transport is not an approved sandbox for generated code.
