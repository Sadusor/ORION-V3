# Task Ledger HTTP Contract — Benchmark A v0.1

Status: candidate contract for approval and freeze before scored model trials. This is a benchmark fixture, not an ORION production API.

- Bind to 127.0.0.1 only; no outbound networking. JSON UTF-8, Content-Type application/json.
- `POST /tasks`: `{"id":"task-1"}` -> 201 `{"id":"task-1","state":"PENDING"}`; duplicate -> 409.
- `GET /tasks/{id}`: 200 task object or 404.
- `GET /tasks`: 200 `{"tasks":[...]} `; deterministic ID ascending.
- `POST /tasks/{id}/transition`: `{"state":"RUNNING"}` etc. -> 200 updated task; illegal or conflicting transition -> 409; missing task -> 404.
- `GET /tasks/{id}/evidence`: 200 `{"id":"task-1","evidence":[]}` for a valid task, 404 otherwise.
- Allowed transitions: PENDING -> RUNNING; RUNNING -> DONE/FAILED/CANCELLED. Terminal states have no outgoing transitions, including self-transitions. No direct PENDING -> terminal.
- IDs: 1–64 ASCII characters matching `[A-Za-z0-9_-]+`. Invalid IDs -> 400, including IDs in URL; missing fields, unknown fields, wrong JSON types, malformed JSON, oversized body (>16 KiB) -> 400. Unknown routes -> 404; unsupported methods -> 405. Empty JSON object is not a valid task.
- Successful transitions must be atomic and durable before the response is emitted. Exactly one of two simultaneous identical transitions from RUNNING to DONE succeeds; the other returns 409.
- SQLite is allowed and recommended. Database path supplied via `TASK_LEDGER_DB` environment variable; process launched with `python -m task_ledger --host 127.0.0.1 --port <port>`. No third-party packages required.
- `GET /health`: 200 `{"status":"ok"}` only after database initialization.
- Crash safety: abrupt termination must not produce half-committed state; durable state is consistent after restart. OS-specific kill mechanism chosen by evaluator. No claims of surviving unacknowledged operations.
- Evidence endpoint is read-only and returns an empty list in this benchmark version; it does not imply production evidence authentication.

Evaluator expectations: exercise only disposable loopback service and disposable database. Run public smoke tests against a known-good fixture and at least one intentionally defective fixture before relying on results. Hidden tests must live outside the code/model-accessible repository and must not be shipped in agent workspaces.

**Freeze this contract before scored runs; do not alter it to accommodate model output.**
