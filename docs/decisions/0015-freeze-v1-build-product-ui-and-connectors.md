> **PARTIALLY SUPERSEDED — 2026-10-05.** Decision 0016 changes only the engineering-Remote role: TheHands is now primary, while the older Remote remains frozen emergency fallback. The product-UI separation/freeze rules below remain valid.

# Decision 0015 — Freeze V1 Remote; Build Connectors + Separate ORION Product UI

Date: 2026-10-05  
Status: ACCEPTED / OWNER DIRECTIVE

## Decision

The existing V1 Remote is frozen **and remains the dedicated ORION engineering Remote even after the new ORION product UI launches**.

ORION development must **not** modify, redesign, refactor, extend, replace, migrate, or recreate V1 Remote. There is no active "Remote V2" product lane.

V1 is used only exactly as already deployed. Existing Check GitHub, Approve & Run, STOP, status/evidence, recovery, and other already-proven controls may continue to be used for the work they already support. V3 must not require new task definitions, payloads, adapters, launchers, or any other repo changes in V1.

## Product direction

The new ORION product is built separately from Remote:

1. connector contracts/seams;
2. STRATA/Claude-inspired ORION PC UI;
3. STRATA/Claude-inspired ORION phone UI;
4. connect those UIs to ORION/backend/connectors;
5. physically qualify each connected capability.

The PC and phone surfaces are two views of the ORION product, not Remote V2 and not parity clones of V1. They are a separate app/surface by design and may run alongside V1 indefinitely.

Chrome may be used during development to inspect a web-rendered product UI when useful. That does not make Chrome a new Remote or a replacement control path.

## V1 rules

- Do not touch V1 Remote code for normal ORION feature development.
- Do not add new Remote buttons, layouts, labels, WebView behavior, parity adapters, or migration features.
- Do not create a second canonical Remote state.
- Do not spend product work recreating Check GitHub, Approve & Run, STOP, or Remote parity.
- Use V1 exactly as it already exists; do not commit or stage new V3 tasks, launchers, adapters, catalogs, payloads, or connector logic in `Sadusor/Orion`.
- All new launch/control/connector/product logic belongs in `Sadusor/ORION-V3` (or another explicitly designated new-project repo), never in V1.
- Any future change to V1 requires a new explicit owner directive that unfreezes it.

## Superseded plan

This decision supersedes `docs/decisions/REMOTE_V1_V2_SHADOW_MIGRATION.md` as an active architecture plan.

That ADR is retained as historical context only. Its V2 Remote/parity-adapter phases are not current work. There is no planned cutover where the product UI replaces V1 Remote.

## Relationship to Decision 0002

`0002-legacy-remote-ui-freeze.md` remains valid. This decision strengthens it: the freeze now covers the Remote as a development target, not only its visual UI. V1 is a tool we **use**, not a component we continue developing during this lane.

## Rationale

The working Remote already solves the remote engineering/control problem. Rebuilding the same job in a second surface creates duplicate state, regression risk, and wasted effort.

The useful new work is the ORION product itself: replaceable connectors, PC UI, phone UI, memory/AI/work surfaces, and later voice/media/skills, all connected to ORION-owned authority and state.
