# ORION PC + Phone Product Milestone — 2026-10-05

Status: **PHYSICALLY WORKING**

## Proven product state

The native Windows ORION product and Android ORION client are both visibly working.

PC:
- `ORION.exe` opens Claude's STRATA UI as a native Windows product surface.
- No external Chrome/Edge window is part of the product path.
- localhost is the trusted PC console.
- the phone pairing code is visible in the PC top bar.
- PC and phone use the same ORION backend.

Phone:
- package `com.sadusor.orionv3`;
- app label `ORION`;
- connects over ZeroTier to the same PC runtime;
- owner physically completed pairing;
- owner physically confirmed the STRATA phone UI renders correctly.

## Automated evidence reached

```text
ORION_DESKTOP_EXE> PASS
ORION_DESKTOP_RUNTIME> PASS
ORION_DESKTOP_BUILD_MATCH> PASS
ORION_DESKTOP_PROCESS> PASS
ORION_DESKTOP_READY> PASS
ORION_NO_EXTERNAL_BROWSER> PASS
ORION_LAUNCH_PROTOCOL> PASS
ORION_DESKTOP_SMOKE> PASS
ORION_ANDROID_WEBVIEW_START> PASS
ORION_ANDROID_WEBVIEW_FINISH> PASS
ORION_ANDROID_DOM_PROBE> PASS
ORION_ANDROID_STRATA_DOM> PASS
ORION_ANDROID_JS> PASS
ORION_ANDROID_ACCESSIBILITY> PASS
ORION_ANDROID_SCREENSHOT> PASS
ORION_ANDROID_VISUAL> PASS
ORION_ANDROID_SMOKE> PASS
ORION_NATIVE_PC_PHONE> PASS
THEHANDS_ORION_JOB> PASS
```

The Android gate includes a real device screenshot test; DOM existence alone is not accepted as visual proof.

## Android rendering lesson

The Huawei WebView reported repeated tile-memory pressure warnings. These were rendering/compositing warnings, not networking or JavaScript failures.

Current mitigations:
- plain native Android WebView shell;
- compatibility rendering path;
- lower phone canvas DPR/detail;
- bounded phone animation rate;
- expensive phone backdrop filters removed;
- warning spam summarized;
- screenshot-based visual PASS retained.

## Native lifecycle

Normal launch: `START ORION.bat`

Native app: `dist/windows/ORION.exe`

Explicit stop: `STOP ORION.bat`

Rules:
- ORION owns its own backend and native app lifecycle.
- ZeroTier already open -> leave it alone.
- ZeroTier opened by ORION -> ORION records that ownership and cleans up its own UI on exit.
- shared ZeroTier service remains independent.
- Ollama already healthy -> leave it alone.
- Ollama not running -> ORION starts hidden `ollama serve` and records exact ownership.
- Ollama started by ORION -> ORION cleans up that owned runtime on exit.
- pre-existing Ollama remains untouched.
- STRATA has a native-only `CLOSE` button; it closes `ORION.exe` and enters the same product cleanup path as the explicit stop launcher.
- hidden lifecycle host exits after cleanup so a terminal is not left behind.

Canonical contracts:
- `docs/contracts/DESKTOP_PRODUCT_SHELL.md`
- `docs/contracts/VISUAL_IDENTITY.md`

## TheHands boundary

TheHands is a separate engineering project. It may build, install and qualify ORION, but it does not own ORION product code.

The known TheHands final-result race is not an ORION failure. The requested correction is limited to UI status-light reconciliation; TheHands runner/finalizer logic remains unchanged.

## Next bounded product task

Connect the ORION Local Brain:
- use the prepared Ollama lifecycle;
- preferred local manager: ORION Qwen 3.5 9B;
- connect `Ask ORION` through governed ORION draft/revise/run semantics;
- preserve authority, evidence, STOP and replaceability.
