# ORION mobile update + clean local reply — physical PASS

Date: 2026-10-06

## Result

PASS.

The owner physically completed the full remote phone-driven update flow and confirmed the expected behavior on-device.

## Proven sequence

1. ORION phone app triggered **Update ORION PC** remotely.
2. ORION ran its regression gates.
3. ORION stopped and restarted itself successfully.
4. The phone reconnected to ORION after restart.
5. Pairing remained valid after refresh; no new pairing was actually required.
6. ORION reported: **Update PASS · ORION PC restarted; latest Android APK is ready to install.**
7. The owner installed the model-less Android APK.
8. The existing app-private Qwen3-0.6B model remained available after APK update.
9. Local Qwen answered successfully after the update.
10. The local reply sanitizer removed newly generated `<think>...</think>` reasoning blocks from the visible answer.

## Important implementation facts

- Normal Android update APKs do not bundle the ~429 MB GGUF.
- The persistent local model remains under Android app-private storage and is reused across normal APK updates.
- The updater uses a Windows-owned restart handoff.
- `taskkill.exe` is best-effort; final process-state verification is authoritative.
- STRATA malformed-response tests now explicitly refresh the bridge after changing fake-backend state, removing a timing-dependent false failure.
- Pairing token digests persist on the PC; temporary network loss may show LOCAL until refresh, but does not imply pairing loss.

## Frozen boundary

The following behavior is now treated as proven and should not be casually refactored:

- phone-triggered PC update
- regression-gated update refusal/recovery
- PC restart and phone reconnect
- persistent pairing across restart
- model-less Android APK updates
- persistent local Qwen reuse
- local `<think>` output suppression
- final stop verification semantics

Current proven source commit before this evidence record:
`355d62fa639fb8547f395f926cf3304f9110a2b4`
