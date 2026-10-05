# Contract — TheHands Lifecycle Bridge

Date: 2026-10-05
Status: CONTRACT DEFINED / REAL LIFECYCLE ENTRYPOINTS NOT YET IMPLEMENTED

## Purpose

Define the only supported process-lifecycle seam between ORION-V3 and TheHands.

TheHands remains a separate manual engineering Remote. ORION-V3 remains the governed product/control plane.

Neither product imports the other's runtime code.

## Required future entrypoints

When the real ORION-V3 backend/runtime is production-ready, expose three stable local lifecycle commands:

1. START
2. STOP
3. STATUS

They may be PowerShell, BAT or CMD wrappers, but they must represent the real runtime, not a demo/mock/test server.

## STATUS contract

The final non-empty stdout line must be exactly one of:

- `OFF`
- `IDLE`
- `WORKING`

Meaning:

### OFF

The real ORION runtime is not active.

### IDLE

The real ORION runtime is active and safe for an owner-requested shutdown.

### WORKING

The real ORION runtime has active governed work and is not safe for a convenience shutdown.

Do not use ambiguous tokens such as RUNNING.

## START contract

START must:

- launch the real ORION-V3 runtime;
- return non-zero on launch failure;
- never start the demo/mock test backend;
- preserve ORION-owned state/authority semantics;
- allow STATUS to transition from OFF to IDLE or WORKING.

TheHands will record lifecycle ownership only when it initiated START.

## STOP contract

STOP must:

- perform ORION-V3's own safe shutdown path;
- return non-zero on refusal/failure;
- not bypass ORION Stop/recovery semantics;
- not report success while governed work remains alive.

TheHands independently refuses STOP while STATUS is WORKING.

## Ownership

TheHands may request STOP only when:

- TheHands initiated the current lifecycle through START;
- STATUS reports IDLE.

If ORION-V3 was started elsewhere, TheHands must treat it as NOT OWNED.

Ownership is a TheHands lifecycle fact only. It does not grant authority inside ORION.

## Separation

Forbidden:

- TheHands importing `orion_v3` modules;
- ORION-V3 importing TheHands runtime modules;
- TheHands writing canonical ORION Task/Event/Memory state;
- using the bridge as a generic command tunnel;
- using demo/mock servers as production lifecycle proof;
- STOP while WORKING.

## Current state

The current V3 repository contains:
- product UI foundation;
- state/bridge contracts;
- fake/test backend;
- demo static server.

It does not yet expose a stable real production runtime lifecycle.

Therefore the correct current TheHands bridge state is:

`UNCONFIGURED`

This is truthful and intentional.

## Physical qualification gate

When real lifecycle entrypoints exist:

1. ORION STATUS = OFF;
2. TheHands START ORION;
3. STATUS reaches IDLE;
4. TheHands records STARTED BY THEHANDS;
5. start one bounded ORION operation;
6. STATUS = WORKING;
7. TheHands STOP ORION is refused;
8. operation finishes;
9. STATUS = IDLE;
10. TheHands STOP ORION succeeds;
11. STATUS = OFF;
12. TheHands clears ownership;
13. TheHands remains operational throughout;
14. shared network transport remains unaffected.
