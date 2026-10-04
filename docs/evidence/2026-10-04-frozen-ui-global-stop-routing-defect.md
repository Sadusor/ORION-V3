# Frozen Remote UI — Global STOP Routing Defect

Date: 2026-10-04  
Status: CONFIRMED UI/ROUTING DEFECT  
Legacy Remote UI: FROZEN / DO NOT MODIFY

## Physical observation

While the named dispatch task `Qwen Thinking ON vs OFF - Reasoning V2` was still running, the owner pressed the large orange `STOP` button in the frozen Remote UI.

The UI returned:

`No active GitHub run.`

This means the visible top-level STOP did not target the active named dispatch session.

## Root cause

The frozen UI's large orange STOP button is wired to:

`POST /api/run/stop`

That endpoint controls the legacy GitHub runner only.

Named dispatch tasks use a separate session runtime and are stopped through:

`POST /api/session/stop`

with the active `session_id`.

The UI therefore presents one prominent STOP control while two execution systems exist underneath it. When a named dispatch task is active and the legacy GitHub runner is idle, the large STOP reports `No active GitHub run` and does not stop the named session.

## Safety / authority

No authority boundary was bypassed.

The failed STOP attempt did not start a new task, approve anything, or modify Proof V1/V2 artifacts. The named benchmark is interpretation-only and has no Hand dispatch or real side effects.

The issue is operational UX: the owner cannot rely on the most prominent STOP button to stop whichever ORION execution is currently active.

## Current workaround

For the frozen UI only:

- focus another completed session so the active named session appears under `Other executions`;
- use that session row's small `STOP` control, which calls `/api/session/stop`.

Do not modify the frozen legacy UI to repair this.

## New V3 UI requirement

The new UI must expose one truthful global STOP that routes to the actually active execution lane.

At minimum it must handle:

- legacy GitHub runner;
- named dispatch session;
- Local Brain / Hand lane;
- manual lane;
- future specialist/agent substrate lanes.

STOP must:

1. identify the active execution deterministically;
2. terminate only that execution tree/lane;
3. update visible state to `STOPPING` then `STOPPED`;
4. never report success when nothing was stopped;
5. never report `No active GitHub run` when another ORION execution is active;
6. remain visible regardless of which details/session panel has focus.

This defect is one of the reasons the frozen Remote is only a development/fallback UI and the V3 phone UI must consolidate execution state.
