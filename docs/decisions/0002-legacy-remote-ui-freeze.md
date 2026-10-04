# Decision 0002 — Freeze Legacy ORION Remote UI

Date: 2026-10-04  
Status: ACCEPTED / OWNER DIRECTIVE

## Decision

The current legacy ORION Remote UI is frozen.

The owner explicitly decided that the existing Remote is now a stable operational surface and must not keep changing while the new UI is being built.

Future UI work belongs in the ORION V3 new-UI lane:

`Sadusor/ORION-V3 -> ui/new-foundation`

Do not make visual, interaction, status-label, Evidence Pack viewer/download, layout, button, WebView, or operator-flow changes to the legacy Remote unless the owner explicitly says to unfreeze the legacy UI.

## Frozen rollback anchors

### PC-hosted legacy Remote UI

Repository: `Sadusor/Orion`  
Frozen branch: `frozen/remote-ui-2026-10-04`  
Exact SHA: `a5e649fe09b9993ed69b7d12e0f49a7f3f1fe872`

This is the deployed Remote state visible on the phone when the owner issued the freeze directive.

### Android ORION Remote client

Repository: `Sadusor/Orion-Copilot`  
Frozen branch: `frozen/remote-ui-android-2026-10-04`  
Exact SHA: `651eae831d6feab60030178c5c0f26b426b22c7b`  
Version: `0.3.2`

## Accepted state at freeze

The owner can open the Evidence Pack viewer on the phone and inspect the generated screenshots.

ZIP download from the legacy Android surface is not required for the freeze. The attempted Android download-handler change was intentionally not merged.

Closed experiment:

`Sadusor/Orion-Copilot PR #1 — Fix Android Evidence Pack ZIP download`

The missing ZIP download must not be used as justification to modify the frozen legacy UI. If download UX is wanted later, implement and validate it in the new UI lane.

## Rules

1. Keep the frozen branches as rollback/evidence anchors.
2. Do not develop directly on the frozen branches.
3. Do not merge legacy UI experiments merely because they exist.
4. Do not alter the legacy phone layout, buttons, Evidence Pack viewer, WebView behavior, status rendering, or operator interaction flow without a new explicit owner approval to unfreeze it.
5. Backend/security emergency fixes are separate from UI work. If one is unavoidable, keep the UI behavior unchanged and prove the legacy Remote still works.
6. Build new UI work in `ui/new-foundation` and compare it against the frozen legacy Remote.
7. Remote V1/legacy remains available for daily operation while the new UI is developed and benchmarked.
8. A new UI does not replace the legacy Remote until the owner explicitly accepts it after physical testing.

## Rationale

Repeated small fixes to the working Remote created regression risk and distracted from the new UI foundation. The current viewer already gives the owner the physical screenshots needed to understand runs. The safest architecture is therefore to preserve the known working Remote and move all further UI iteration to a separate replaceable surface.
