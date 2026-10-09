# Proposed first owner-approved multi-cloud build: offline task tracker

Status: **DRAFT FOR OWNER REVIEW — NOT APPROVED; NOT EXECUTABLE**
Date: 2026-10-09
Decision basis: 0020, physical advisory session `thehands-58edd7d97157`.
Source advisory file: `E:\ORION-WORKLOOP-REMOTE-TEST\artifacts\multi-ai\live-70483bb2c45747e3b58cf4215d0221db.json`.
Source file SHA256: `9002fbff85ea57d86fa5baf6d519cd284095af9fa4b148c15f4edab6f1225633`.
Models: `groq:openai/gpt-oss-120b` and `groq:openai/gpt-oss-20b`.
Review evidence: two independent proposals and two reciprocal critiques, with individual content hashes validated by read-only reader. Some printed proposal excerpts were truncated; do not claim this document is a verbatim reproduction of all four full texts.

## Goal
Create a tiny task tracker using only the Python standard library: SQLite persistence, localhost HTTP CRUD API, reproducible tests, disposable project directory. No third-party installation, remote connections, shell commands in the application, or writes outside the approved disposable workspace.

## Bounded API contract
- `POST /tasks`: title required, nonempty string; optional status defaults to `todo`; returns 201 with task ID and JSON.
- `GET /tasks`: return all tasks in stable ID order.
- `GET /tasks/<positive integer>`: return task or 404.
- `PUT /tasks/<positive integer>`: update title/status with validation; return task or 404.
- `DELETE /tasks/<positive integer>`: delete task; return 204 or 404.
- Status enum: `todo`, `in_progress`, `done`. Malformed JSON, unknown fields, wrong types and invalid IDs return deterministic 400/404 errors as appropriate.
- Bind HTTP server to `127.0.0.1` only, using an ephemeral port for tests. No pagination, authentication, UI, dates, retries or concurrency features in V1 unless explicitly approved as follow-on scope.

## Minimal modules
- `tracker/db.py`: SQLite schema and CRUD, transaction boundaries, one short-lived connection per operation; SQLite busy timeout and bounded failure response; never auto-delete/recreate a corrupt database.
- `tracker/api.py`: `http.server` request handler, route parsing, bounded JSON request bodies, explicit error mapping and localhost bind.
- `tracker/model.py`: minimal input/status validation and output serialization; avoid redundant framework layers.
- `tests/test_api.py`: stdlib `unittest` integration tests with `tempfile.TemporaryDirectory`, ephemeral port and clean `shutdown()/server_close()`.
- `README.md`: exact stdlib run/test commands, API contract and failure modes.

## Acceptance gates
1. CRUD HTTP happy paths, persistence after server restart, stable list order.
2. Missing/empty title, invalid status, invalid IDs, malformed/oversized JSON, nonexistent task and unsupported method are rejected predictably.
3. Tests use temporary SQLite DB, loopback ephemeral port, bounded shutdown and leave no external artifacts.
4. DB errors never trigger automatic data deletion; clean failure and recovery instructions are documented.
5. No dependencies, no internet access, no subprocess execution and no writes outside authorized disposable workspace.
6. Owner can inspect proposed patches and independent test evidence. A model statement cannot mark PASS.

## Recorded model disagreements and adjudication
- **Module count:** 120B preferred about seven focused modules; 20B preferred about four. Choose three implementation modules plus tests/docs; avoid overengineering.
- **Tests:** 20B proposal mentioned `pytest`/`conftest.py`, contrary to pure stdlib. Require `unittest` only.
- **Routing:** both critiques called out ambiguity. Choose explicit small path matcher within `api.py`; no separate router module.
- **SQLite concurrency:** proposals suggested `check_same_thread=False`, pools, global locks and retries. Choose short-lived per-operation connections and a single-threaded `HTTPServer` for V1; do not introduce shared cross-thread connections or pool. Later concurrency work is a separate milestone.
- **Pagination:** proposed inconsistently; exclude from V1.
- **Corruption recovery:** one proposal suggested vacuum/drop/recreate on integrity failure. Reject automatic destructive recovery. Preserve DB and fail visibly.
- **Lifecycle:** explicit server shutdown and test cleanup required.
- **Security:** HTTP loopback bind is application scope, not proof of OS network isolation for the ORION execution substrate.

## ORION execution gate (NOT YET SATISFIED)
1. Owner explicitly approves an immutable digest of this exact plan; editing requires a new digest and approval.
2. Cloud models independently submit code patches and cross-review them; proposals remain untrusted.
3. ORION's existing typed authorization and Vault scope checks reject unauthorized changes, stale digests and replay.
4. ORION's native Work Hand must physically pass Windows filesystem/network confinement, process-tree STOP and verification/commit gates before any generated patch is executed.
5. Only then perform disposable project build, independent tests and deliberate FAIL -> restart -> repair -> PASS qualification. STOP, owner decisions and evidence remain authoritative.
6. TheHands is not ORION's Work Hand; prior owner-controlled PowerShell 1 was transport for evidence inspection only.

## Proposed owner decision
Owner may **approve the plan for the next proposal/patch-design phase**, request changes, or reject. Approval of a plan is NOT permission to execute generated code before ORION's native safety gates pass.

## Next action
Record plan digest, display exact contents to owner, obtain explicit decision. Do not treat this draft or a chat response as automatic ORION `owner_decide` state transition. No cloud or code execution is authorized by this document.
