# Claude STRATA V3 UI Package Review

Date: 2026-10-04  
Status: REVIEWED, NOT INTEGRATED  
Source: owner-supplied Claude UI ZIP package(s)

## Package identity

The owner supplied three ZIPs. The most complete/current package is the nested `orion-strata-v3.zip` contained in `files (5).zip`.

It contains:

- `ui/strata/` complete frontend, docs and tests;
- `spikes/coding_mode_github_loop/strata_static.py`;
- a marker-wrapped additive server patch;
- a reversible patch tool.

The smaller supplied ZIPs mostly duplicate files inside the complete package:

- `files (3)(1).zip`: `routes.js` and `config.js` are byte-identical to the complete package;
- `files (4).zip`: bridge/integration files are byte-identical except its standalone `test_browser.py` is an older timing-based variant. Treat the browser test inside the complete `orion-strata-v3.zip` as canonical.

## Architectural fit

STRATA is strongly aligned with ORION's authority model.

Good properties:

- UI is presentation/control only; backend remains authority.
- Explicit bridge -> normalize -> canonical UiState -> renderer split.
- Raw backend field names are isolated in `normalize.js`.
- Live page never silently falls back to mock data.
- Real state is backend-driven; no timer-driven operational transitions.
- Execution state and verdict are represented separately.
- Request/launch/verification evidence are represented separately.
- Stale/reconnecting/disconnected/backend-error states are explicit.
- Route allowlist prevents unregistered UI actions.
- Approval routes require a trusted human click.
- Legacy `/` and `/operator` remain available.
- Static mount is additive under `/v3/` and does not replace the frozen legacy UI.
- Patch is small and reversible.

The server patch anchors currently still exist exactly once on the active Orion development branch, and STRATA is not currently mounted there.

## STOP handling

STRATA is materially better than the frozen UI defect found today.

The canonical UiState builds a list of every currently stoppable execution:

- Local Hands PowerShell;
- manual run;
- exact-SHA GitHub run;
- named dispatch sessions;
- reviewer run.

The main Stop control:

- is always present;
- disables when nothing is stoppable;
- directly stops the only active target when exactly one exists;
- opens a target chooser when multiple executions are active;
- includes a "Stop all running" option.

This avoids the frozen UI bug where the large STOP always routed to the legacy GitHub runner.

However, registered capability runs are documented as non-stoppable in the current backend. V3 must not imply otherwise until backend stop semantics exist for them.

## Tests run during this review

From a clean extraction of the complete package:

- UNIT assets: PASS — 97 checks
- UNIT normalize: PASS — 35
- UNIT state reducer: PASS — 88
- UNIT routes & safety: PASS — 98
- UNIT boot: PASS — 18
- UNIT static serving: PASS — 36
- BRIDGE real bridge over HTTP: PASS — 33

Total independently executed non-browser checks: **405 PASS**.

Browser suite could not be independently executed in the review environment because Playwright's expected bundled Chromium executable was not installed.

This exposed a small test-runner/documentation mismatch: `TESTING.md` says browser tests auto-skip when Chromium is unavailable, but if the Python Playwright package exists while the bundled executable is missing, `test_browser.py` reaches `chromium.launch()` and the suite is classified as FAIL rather than SKIPPED.

This is a harness issue, not evidence of a UI runtime failure.

ORION integration and physical phone tests were not run during this review.

## Current gaps versus the latest ORION direction

STRATA was designed before today's multi-lane/personal-learning decisions, so it should be treated as a strong foundation rather than integrated unchanged.

### 1. Personal Assistant + Project Assistant are not first-class lanes yet

The current main state contract still collapses the cockpit to one dominant `task` / `action` / ORION state.

Named sessions exist and multiple stops are represented, but there is no first-class model such as:

- Personal Assistant: READY / THINKING / ACTING;
- Project PayDay: CODING / TESTING / WAITING / APPROVAL;
- Benchmark: RUNNING.

V3 should extend the state contract to expose concurrent logical lanes rather than hiding them only inside Command Center/task-session lists.

### 2. Local Brain backend is still effectively one conversation lane

The primary natural-language route is:

`POST /api/local-hand/draft {goal, model}`

There is no lane/project/conversation identifier in that contract.

The multi-lane architecture needs backend-owned task/lane identity so a Personal Assistant request cannot overwrite or inherit a Project Assistant context.

### 3. Adaptive thinking mode is not visible

The UI exposes the selected model but not:

- FAST / THINKING mode;
- why ORION escalated to thinking;
- whether a request was retried with thinking;
- stronger-model/human escalation.

The new UI should expose this compactly without making the owner manually manage reasoning mode for normal use.

### 4. Personal memory is not implemented yet

STRATA correctly labels Memory as preview/candidates only.

The new direction requires later support for:

- accepted ORION memory;
- approved files/downloads/browser exports;
- screenshots/PDF/image sources;
- provenance/source links;
- retrieval evidence.

Do not fake this in the UI before backend APIs exist.

### 5. Vision and PC Live View remain planned

This is correctly represented as unavailable today.

The future UI should distinguish:

- vision over an explicitly supplied/approved image;
- passive/view-only PC Live View;
- computer control authorization.

Viewing must never imply control authority.

### 6. Voice remains planned

The disabled hold-to-talk UI is acceptable as a placeholder, but should not be promoted until the PC STT path and shared turn journal physically exist.

## Recommended use

Adopt STRATA as the **visual/state-contract donor for the V3 phone/PC UI alpha**, not as a frozen final implementation.

Preserve:

- visual shell / sky-planet concept;
- bridge-normalize-store separation;
- backend-driven truth rules;
- route allowlist;
- explicit connection health;
- approval card;
- evidence ladder;
- targeted/global Stop behavior;
- additive `/v3/` coexistence with legacy;
- Command Center/adapters.

Extend before production adoption:

1. concurrent lane schema;
2. Personal vs Project Assistant identity;
3. per-lane model + FAST/THINKING mode;
4. truthful global Stop semantics across every backend lane;
5. backend-owned turn/task journal;
6. accepted memory/personal-file retrieval when backend exists;
7. vision/Live View/voice only after physical qualification.

## Integration timing

Do **not** patch the frozen legacy Remote UI.

Do not integrate STRATA while the current model tournament is still the active bounded task.

After Proof V2/model-selection work reaches the next UI gate:

1. copy STRATA into the ORION-V3/new-UI workspace;
2. update its state contract for multi-lane assistants first;
3. run the full unit/bridge/browser suite;
4. test its additive patch against the then-current Orion server in a temporary copy;
5. serve under `/v3/`;
6. physically test on PC and phone while legacy remains untouched;
7. only then consider it a qualified UI alpha.
