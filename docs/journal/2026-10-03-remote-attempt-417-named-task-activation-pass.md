# Remote Attempt 417 — Named-task Remote activation PASS

Date: 2026-10-03

Status: **PHYSICAL PASS**

Remote tested SHA:
`98b1a78beb3edcab95f7dfe22fbf4b87d7c3580e`

Remote attempt:
`417`

Runner exit code:
`0`

Observed evidence:
```text
PRIMARY_APPROVE_SOLE_NAMED_TASK> PASS
PRIMARY_APPROVE_MULTIPLE_TASKS> DENIED
REMOTE_EXACT_SHA_SYNC> PASS
WINDOWS_RESTART_HANDOFF> PASS
UPDATED_REMOTE_SHA> 98b1a78beb3edcab95f7dfe22fbf4b87d7c3580e
STATUS> PASS
```

Meaning:
- the new server code contains the primary-button named-task routing behavior;
- ambiguous multi-task auto-routing fails closed;
- the real ORION Remote checkout was fast-forwarded to the exact approved SHA;
- restart ownership was handed to the already-proven Windows restart mechanism.

This fixes the transport/UI problem that caused attempts 415 and 416 to execute stale `CURRENT_TASK.ps1` logic.

Next proof:
with the restarted server live, use the normal two-button path:
`CHECK GITHUB -> APPROVE & RUN`.

The sole named task at this SHA is `v3-current-gate`, driven by data-only `V3_GATE.json`.
The current manifest labels that transport proof as `V3-RUN-017` and re-runs the already-passed local Event Exchange bootstrap at its pinned V3 SHA.

A PASS will prove the normal main button now dispatches the named V3 gate without manual PowerShell or secondary task selection.
