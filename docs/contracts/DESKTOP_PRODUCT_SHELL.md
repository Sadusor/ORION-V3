# ORION Native Desktop Product Shell

Status: **NATIVE PRODUCT PATH**

ORION on Windows is a launchable product application, not a browser tab and not an engineering Remote.

## Product identity

Primary executable:

`dist/windows/ORION.exe`

Normal owner entry point:

`START ORION.bat`

Normal explicit stop entry point:

`STOP ORION.bat`

The window hosts Claude's existing STRATA HTML/CSS/JS inside the Windows WebView2 runtime so the accepted design is preserved exactly. No external Chrome/Edge window is part of the product flow.

WebView2 is an embedded Windows application runtime, not a Chrome dependency and not an external browser process owned by the user.

## Shared PC / phone model

The PC is the authoritative ORION host.

`ORION.exe` renders:

`http://127.0.0.1:8890/v3/`

The Android ORION app renders the same STRATA product from the same PC backend over the private ZeroTier address:

`http://10.109.233.27:8890/v3/?view=phone`

The PC-local console is trusted localhost. The phone must pair to the same runtime.

## START protocol

`scripts/start_orion.ps1` owns one ORION product session:

1. refuse to spawn a duplicate native ORION UI;
2. clean stale ORION-owned runtime/process state;
3. inspect ZeroTier;
4. if ZeroTier desktop UI is already open, leave it alone and record it as pre-existing;
5. if ZeroTier desktop UI is not open, start it and write an exact ownership record;
6. probe Ollama at `127.0.0.1:11434`;
7. if Ollama is already healthy, leave it running and do not claim ownership;
8. if Ollama is not running, start `ollama serve` hidden and record the exact ORION-owned PID/executable;
9. start the ORION backend on port 8890 without launching any browser;
10. launch `ORION.exe`;
11. wait for the native window to close;
12. run ORION cleanup automatically.

`START ORION.bat` launches that lifecycle host hidden so no orphan command window remains on the desktop.

## STOP / close protocol

Closing `ORION.exe` is the normal product close.

The STRATA top bar exposes a native-only `CLOSE` control. It sends an `orion-close` message to the native host, which closes the same `ORION.exe` window. That enters the exact same lifecycle cleanup path as closing the window normally or running `STOP ORION.bat`.

After the native window exits, the hidden lifecycle host automatically:
- stops the ORION backend;
- removes stale ORION runtime/pairing state;
- closes ZeroTier desktop UI only if this ORION session opened that exact process;
- leaves a pre-existing ZeroTier UI untouched;
- stops Ollama only if this ORION session started the exact `ollama serve` process;
- leaves a pre-existing Ollama runtime/model session untouched;
- never stops the shared ZeroTier service;
- removes stale ORION lifecycle hosts.

`STOP ORION.bat` performs the same bounded cleanup when an explicit stop is needed.

## Proof

The native app writes:

`%LOCALAPPDATA%\ORION-V3\desktop-ready.json`

only after STRATA navigation completes successfully inside `ORION.exe`.

`scripts/smoke_desktop.ps1` proves:
- native executable exists;
- backend is healthy;
- executable build commit = repository commit;
- backend commit = repository commit;
- exact native `ORION.exe` process is running;
- STRATA reached ready state inside the native app;
- backend launcher contains no external-browser launch path;
- Ollama API is reachable;
- Ollama ownership is either a validated ORION-owned serve PID or explicitly pre-existing/unowned;
- native CLOSE control is wired from STRATA to `ORION.exe`;
- START/STOP lifecycle files exist.

## Separation from TheHands

TheHands remains a separate frozen engineering tool. It may build/install/test ORION as an external runner, but it is not imported into ORION and owns no ORION runtime/UI code.
