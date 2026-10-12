# ORION V3 — Separate Gitea Write API Contract
Date: 2026-10-12
Status: OWNER DIRECTIVE / DESIGN ONLY / NOT IMPLEMENTED

## Preserve existing read path
The current Qwen -> ORION -> MyGitea2 read-only API and repository knowledge retrieval MUST remain unchanged. Its endpoint, token scopes, caches, database access, index, and retrieval behavior are protected. No write permission may be added to its existing token or route.

## New additive write module
Create a separate ORION-owned, replaceable Gitea write adapter, with separate write credentials and a distinct endpoint/operation namespace. Qwen may REQUEST changes but cannot call Gitea with a raw privileged token. ORION owns the action lease and decides if a write is permitted. Never directly modify gitea.db, repository filesystem internals or SQLite tables; use Gitea supported REST API/Git mechanisms.

Initial permitted actions, each behind ORION policy: create task branch from pinned revision, create/update task-scoped files, commit approved patch, read commit receipt, record task/revision association. Explicitly deny default-branch write, deletion, force push, credential changes, repository administration and merges unless separately designed, approved and tested.

Required inputs: project_id, task_id, trusted repository ID, base commit SHA, task branch, path allowlist, proposal hash, exact patch/content hash, action lease, expiry, one-shot idempotency key, expected revision, spending/operation budget.
Required output: authenticated Gitea response, repository/branch, resulting commit SHA, changed paths, operation ID, timestamp, failure/retry status. Feed into existing ORION event/evidence system; Gitea receipt is NOT equivalent to passing tests.

Security: separate least-privilege write token, never expose to Qwen, Android, Claude HTML or logs; replay protection; concurrent revision checks; protected branch enforcement; STOP/cancel checks; explicit fail-closed on missing permissions or Gitea outage.

Test gates:
1. Existing read API and Qwen knowledge queries unchanged.
2. No-write without ORION lease; invalid/wrong project/expired/replayed lease denied.
3. Only test repository and task branch can be written; protected main rejected.
4. Conflict, retry, STOP and network failure leave consistent task status.
5. Successful test branch commit returns exact SHA; Hands independently test that SHA.
6. Manual GITCHECK through separate frozen TheHands- remote; owner confirms physical PASS before freeze.

## Audit dependency
Locate exact existing read API code and tokens by read-only source inspection before implementing. Do not infer locations from file names. Preserve all ORION internal Hands abilities. Existing provider design: Qwen coordinator, DeepSeek Flash code author, Grok API reviewer. OpenHands excluded from loop.

## Step ledger
Step 0 DOCUMENTED on GitHub branch docs/autonomous-loop-plan-20261012.
Step 1 IN PROGRESS: locate read-only Gitea adapter and write seam.
Step 5 now explicitly includes new Gitea WRITE adapter; NOT STARTED.
