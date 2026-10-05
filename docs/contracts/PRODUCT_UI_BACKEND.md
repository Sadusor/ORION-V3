# ORION V3 Product UI Backend Contract

Status: **LIVE-GATE CONTRACT / PHASE A**

This document defines the functions required to connect Claude's STRATA V3 product UI to ORION V3 without turning the UI into authority and without modifying TheHands.

## Boundary

TheHands remains the frozen manual engineering Remote.

The product UI talks only to the ORION V3 product server. The product server may expose facts and owner intents, but ORION remains the authority for policy, approvals, evidence, memory truth and STOP.

## Phase A — functions connected now

| UI need | HTTP contract | Authority / behavior |
|---|---|---|
| Serve product UI | `GET /v3/` and allowlisted static assets | Presentation only |
| Runtime health | `GET /api/health` | Read-only, no auth required |
| Pair phone/browser | `POST /api/pair {code}` | Exchanges short-lived pairing code for device token |
| Canonical live snapshot | `GET /api/status` | Authenticated read-only facts |
| Project list | `GET /api/project-links` | Authenticated read-only |
| Work exchange | `GET /api/work-exchange/latest` | Authenticated read-only |
| Memory candidate preview | `GET /api/memory/candidates` | Authenticated read-only; never promoted Memory |
| Reviewer status | `GET /api/reviewers/latest` | Authenticated read-only |
| Provider status | `GET /api/providers` | Authenticated read-only |

The Phase A server reports the real repository HEAD/branch and its own runtime identity. Missing subsystems are reported as empty/not connected, never simulated.

## Phase B — UI intents requiring real ORION functions

These routes already exist in the STRATA bridge allowlist, but must return an explicit refusal until their real ORION implementation is connected:

- `POST /api/local-hand/draft` — submit owner text to Local Brain for a proposal;
- `POST /api/local-hand/revise` — ask Local Brain to revise a blocked/proposed action;
- `POST /api/local-hand/run` — owner approval boundary for generated PowerShell;
- `POST /api/local-hand/stop` — targeted stop of that Local Hand;
- `POST /api/run/start` / `POST /api/run/stop` — governed exact-revision developer loop;
- `POST /api/session/start` / `POST /api/session/stop` — background work;
- `POST /api/reviewers/stop` — targeted council stop;
- project/provider/mode/update commands already registered in `ui/strata/bridge/routes.js`.

A route being present in the frontend allowlist does **not** mean the backend capability exists.

## Later independent channels

These remain separate contracts and are not faked by Phase A:

- shared PC-owned conversation/turn journal;
- voice/STT;
- view-only PC Live View media channel;
- promoted canonical Memory read/write APIs;
- connector execution contracts;
- governed computer-use / Android-use Hands;
- cloud reviewer execution;
- FAST/THINKING backend-owned state.

## Phone transport

Initial live address is private-network HTTP on the PC:

`http://<PC-private-IP>:8890/v3/`

The server binds to `0.0.0.0:8890` for the private overlay/LAN. Pairing is still required for ORION API state. Direct public-Internet exposure is not supported.

## Truth rule

Unsupported actions return an explicit backend refusal. They must never look like PASS, RUNNING, or connected merely because the button exists.
