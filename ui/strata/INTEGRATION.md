# Backend Wiring — Live Gate

Status: **PHASE A CONNECTED / PHYSICAL PC+PHONE VIEW PENDING**

The current owner-approved sequence is:

1. use TheHands for manual engineering Remote execution;
2. keep the frozen fallback Remote untouched;
3. build connector contracts/seams;
4. build the new PC + phone product UI;
5. connect the UI to ORION/backend/connectors;
6. physically qualify each capability.

This product UI must not become or proxy the engineering Remote.

## Phase A live connection

The live product server is now `src/orion_v3/product_server.py`.

It serves Claude's STRATA UI at `/v3/`, provides pairing, and exposes truthful read-only backend facts. Unsupported action routes return explicit refusal rather than synthetic success.

Launcher:

`scripts/start_product_ui.ps1`

Default port: `8890`.

See `docs/contracts/PRODUCT_UI_BACKEND.md`.

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

Do not recreate TheHands engineering controls as a product milestone. Manual engineering Remote work belongs in TheHands; the frozen fallback remains untouched.
