# ORION Android Offline Model Storage

Status: PHYSICALLY PROVEN PASS on 2026-10-06; frozen after model-less APK update preserved and reused the existing phone model.

## Goal

Normal ORION APK updates must not carry the ~429 MB Qwen3-0.6B GGUF again.

## Invariants

- Phone model lives persistently in app-private `files/models/Qwen3-0.6B-Q4_0.gguf`.
- Normal APK updates preserve that app-private file.
- The model is SHA-256 verified before loading.
- Normal update APKs contain no `.gguf` entry.
- A one-time/bootstrap build may opt in with `android/scripts/build.ps1 -BundleOfflineModel`.
- The PC build cache is `%LOCALAPPDATA%\ORION-V3\models`; it is not shipped in normal updates.
- If a phone has no persistent model and the APK has no bundled model, Local mode fails truthfully and asks for the one-time model pack. It must not silently claim Local is available.

## Physical acceptance gate

1. Existing bundled app runs Local Qwen successfully. This proves the old APK materialized the model into app-private storage.
2. Build ORION 0.2.2 with the default build path.
3. Prove the APK contains no `.gguf` and record APK size.
4. Install 0.2.2 over the existing app without uninstalling it.
5. Settings reports the persistent local model present.
6. With PC/ZeroTier unavailable if desired, ask Local Qwen a message and get a valid reply.
7. Only then freeze this module.


## Physical result — 2026-10-06

PASS.

- Model-less APK gate built successfully at 14.5 MB.
- Normal APK contained no GGUF.
- Owner installed the model-less Android update over the existing ORION app.
- Local Qwen3-0.6B answered successfully after the update.
- Therefore the app-private persistent model survived the APK update and remained usable.
- PC model discovery also remained available after reconnect.

Known follow-up outside this frozen module: Local Qwen currently exposes `<think>...</think>` text in the chat UI. That is a presentation/output-sanitization issue, not a model-storage failure.
