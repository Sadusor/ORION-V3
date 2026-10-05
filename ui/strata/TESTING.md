# Testing

## Current foundation gate

Run:

```bash
python tests/run_tests.py --no-browser
```

Current verified result (2026-10-05):

- assets: 102 PASS
- normalize: 35 PASS
- state reducer: 88 PASS
- routes & safety: 28 PASS
- boot: 18 PASS
- static serving: 36 PASS
- real bridge over HTTP: 33 PASS

**340 checks, all PASS.**

The connector-safety test now verifies that the product connector catalog is status-only and exposes **zero backend call actions** before connector wiring.

## Browser rendering

The inherited Playwright suite still exists under `tests/browser/`. In a normal environment it can use Playwright Chromium or a system Chromium fallback. The current build environment blocks browser navigation to both `file://` and localhost by administrator policy, so the exact HTML/CSS/JS was additionally rendered by injecting it into real system Chromium.

Verified renders:

- desktop Home / AI / Connectors;
- phone Home / AI / Connectors;
- 6 product navigation destinations;
- 4 logical lane cards;
- 5 AI slots;
- connector-card surface;
- no page/console errors;
- no horizontal overflow at 1440×900 or 390×844.

## What is not yet proven

Physical owner-PC serving, real phone networking, final backend connector contracts, shared turn journal, voice, live PC view, accepted Memory APIs, and FAST/THINKING backend state remain future gates.
