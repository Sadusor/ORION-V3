# Backend Wiring — Future Gate

Status: **NOT ACTIVE YET**

The current owner-approved sequence is:

1. freeze V1 Remote;
2. build connector contracts/seams;
3. build the new PC + phone product UI;
4. only then connect the UI to ORION/backend/connectors;
5. physically qualify each capability.

Therefore this UI must **not** be mounted into, proxied through, or used to modify V1 Remote during the foundation phase.

## What is ready now

The frontend already has clean seams for:

- transport (`bridge/real-bridge.js`);
- raw-backend normalization (`bridge/normalize.js`);
- canonical product state (`state/store.js`);
- connector presentation (`connectors/`);
- product workspace (`product/workspace.js`).

## Future wiring requirements

Before a backend endpoint is exposed through the product UI:

- define an ORION-owned typed contract;
- define risk/approval semantics;
- define evidence returned on completion;
- define STOP/cancellation semantics where applicable;
- bind project/lane/conversation identity;
- add truth-preserving normalize/store mapping;
- add unit + bridge + browser tests;
- physically test on PC and phone.

## No Remote parity milestone

Do not recreate `Check GitHub`, `Approve & Run`, Remote status counters, Remote navigation, or a browser copy of V1 as a product milestone. V1 remains separate and untouched unless a future explicit owner decision unfreezes it.
