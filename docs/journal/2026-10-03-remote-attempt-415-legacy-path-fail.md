# Remote Attempt 415 — Named-task transport not exercised

Date: 2026-10-03

Status: **TRANSPORT FAIL / LEGACY PATH USED**

Remote tested SHA:
`c1311a488c37e4d760589b45e59b7a2c9f69f370`

Observed output:
```text
ORION_REMOTE_TO_V3> START
DETAIL> Unexpected fetched V3 SHA: 8cbd69cba7c7ed8ab48c35cdf2a55427e9b632c9
STATUS> FAIL
```

Root cause:
the main `APPROVE & RUN` button was still wired to legacy `CURRENT_TASK.ps1`.
The newly added named-task dispatcher was available only in the secondary task list, so the transport proof never ran.

This is not a V3-RUN-016 failure and not a named-task-dispatch failure.

Correction:
- primary `APPROVE & RUN` now routes automatically to the sole checked named task;
- if multiple named tasks exist, primary run fails closed and requires explicit selection;
- the V3 gate runner now accepts a pinned SHA that is an ancestor of the trusted fetched V3 branch tip, avoiding false staleness from later documentation-only commits;
- a one-time named task activates the updated Remote server so the corrected primary-button behavior becomes live.
