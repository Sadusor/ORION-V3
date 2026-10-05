# ORION Product UI Architecture

## Boundary

The UI is presentation/control intent only. **ORION owns authority, canonical task state, approvals, memory truth, evidence and STOP.** Models and connectors never gain authority because they appear in the UI.

The V1 Remote is frozen and outside this architecture. It is an engineering control path we use separately; it is not a dependency, fallback link, or migration target of the product UI.

## Pipeline

`backend/mock → bridge → normalize → store → buildUiState → product shell/components`

| Module | Responsibility | Raw backend JSON? |
|---|---|---|
| `bridge/real-bridge.js` | transport, auth, polling, error classes, route guard | passes through |
| `bridge/normalize.js` | raw backend compatibility layer | yes, only here |
| `state/store.js` | canonical state + evidence/truth rules + logical lanes | no |
| `product/workspace.js` | Home/Work/AI/Connectors/System product surfaces | no |
| `connectors/*` | status descriptors + generic rendering | no |
| `shell/*`, `components/*`, `memory/*` | presentation and user-intent forwarding | no |

## Truth rules

1. No timer advances operational state. Backend facts establish state.
2. Request ≠ execution ≠ verification.
3. Execution state and verdict are separate.
4. UI never invents authorization.
5. Unsupported capabilities are shown as planned/unavailable, never simulated.
6. Unknown/malformed backend state becomes explicit stale/reconnecting/offline/backend-error state.
7. FAST/THINKING is `not_reported` until the backend owns that fact.
8. Viewing a PC never authorizes control of that PC.

## Product lanes

The canonical state exposes four logical lanes:

- **Personal** — everyday assistant/governor work;
- **Project** — active project/task context;
- **Specialists** — cloud reviewers/council;
- **Background** — independent running sessions.

Lane identity is presentation of backend-owned facts. Future backend work must add stable lane/conversation IDs before concurrent assistants are considered fully connected.

## Connectors

Connectors are replaceable adapters. The current UI catalog is **status-only** and intentionally has zero execution call actions. Wiring comes later. A future connector may expose actions only through ORION-owned contracts and policy checks.

## STOP / evidence

The inherited STRATA state model keeps targeted STOP semantics and the evidence ladder. A control may only claim stoppability or verification when the backend reports enough evidence to justify it.
