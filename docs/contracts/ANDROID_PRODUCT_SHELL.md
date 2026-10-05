# ORION Android Product Shell

Status: **DIRECT STRATA SHELL**

The Android application is ORION itself. It is not an engineering Remote and it must not present a launcher/dashboard before the product UI.

## Required startup behavior

Launching package `com.sadusor.orionv3` opens:

`http://10.109.233.27:8890/v3/?view=phone`

directly inside the Android WebView.

The first visible product surface is therefore Claude's STRATA ORION interface:
- ORION core / sky;
- conversation area;
- `Ask ORION…` composer;
- truthful connection state;
- Home / Work / AI / Memory / Connectors / System product navigation;
- STRATA pairing overlay when the device is not yet paired.

## Forbidden launcher behavior

The Android application must not add a pre-ORION control dashboard or engineering workflow.

The following labels are forbidden in the Android launch path:
- `OPEN ORION`;
- `CHECK ORION`;
- `OPEN ZEROTIER`;
- Git Check / Approve / Start / engineering-Remote workflow language.

Private-network connectivity is transport, not the product identity.

## Failure behavior

If the page cannot load, the shell may show a minimal ORION unavailable message. It must not fall back to an engineering dashboard.

## Regression proof

`android/scripts/smoke.ps1` launches the installed APK and fails if an obsolete launcher label is detected. It accepts the actual STRATA surface / pairing UI as the launch result.
