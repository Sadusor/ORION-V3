# ORION Product UI — STRATA Foundation

Status: **UI FOUNDATION / NOT YET CONNECTED**

This is the new ORION product interface for **PC and phone**. It is based on Claude's STRATA V3 package and keeps its strongest ideas: the sky/planet shell, canonical UI state, explicit evidence, honest stale/offline states, targeted STOP semantics, and strict separation between presentation and authority.

It is **not an engineering Remote**. Manual engineering execution is handled separately by TheHands. The frozen fallback Remote is not modified by this UI.

## Product surfaces

- **Home** — ORION core, truthful state, conversation, evidence/result.
- **Work** — project, task and background-session views.
- **AI** — five cloud-specialist slots plus local governor status.
- **Memory** — preview until canonical Memory read APIs are connected.
- **Connectors** — replaceable capability fabric; status does not grant authority.
- **System** — connection, compute, authority and evidence health.

Four first-class logical lanes are visible on PC and phone: **Personal, Project, Specialists, Background**.

## Architecture

`backend/mock → bridge → normalize → canonical UiState → product shell`

Only `bridge/normalize.js` knows raw backend field names. Product components read only `UiState`. The connector catalog is deliberately **status-only** at this stage; backend wiring comes after the UI foundation is accepted.

## Demo

`demo.html` is synthetic and visibly marked `DEMO / MOCK BACKEND`. `index.html` loads the real bridge only. A failed live connection never falls back to mock data.

## Local checks

```bash
python tools/serve_demo.py
python tests/run_tests.py --no-browser
```

See `PRODUCT_UI.md`, `ARCHITECTURE.md`, `STATE_CONTRACT.md`, and `INTEGRATION.md`.
