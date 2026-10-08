# M3.5 native fixed-action physical PASS — 2026-10-08

Evidence: TheHands manual transport session `a27262b11b82`, source commit `a42b7ce5b7485d2e5cbe10f9bd2c1efcecbcd844`.
https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/a27262b11b82.json

Observed: 28/28 existing regression PASS; 1/1 fixed-action preflight PASS; signed GREEN plan PASS with `execution: not_started`; baseline AppContainer filesystem PASS; new `M35FixedActionProbe.cs` compiled and launched native AppContainer child, Job Object assigned, exit 0, exact fixture file content independently checked, outside read/write denied, outside sentinel unchanged, profile deletion HRESULT 0, build cleaned. `M35_NATIVE> PASS_EXPERIMENTAL_FIXED_ACTION_ONLY`.

Important qualification: native fixed action is still separate from signed preflight. No cryptographic proposal-to-child binding or authoritative STOP gate; no verified Vault commit for this execution. Network isolation inconclusive; descendants and combined eight-gate qualification not run. Production executor disabled. This is experimental native fixed-action execution PASS, not full M3.5 or M4 PASS.

Next bounded integration: bind exact signed proposal to the native child invocation; verify native evidence and STOP before recording with existing ProjectVault; no new STOP or Vault. TheHands is only manual engineering transport, not an ORION runtime dependency.
