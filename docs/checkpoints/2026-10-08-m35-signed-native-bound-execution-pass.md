# M3.5 experimental signed-to-native execution PASS — 2026-10-08

Evidence: TheHands powershell-1 session `172a0ab4b254`, result PASS, runner commit `0105eb9dcd2324d7fcd03b197d27914b60787808`, ORION commit `f16befbf59f70443a96cceb3acde8a6e6b5872c9`.

Physical observed markers:
- 28 existing regressions PASS; preflight 1 PASS; commit denial 2 PASS; binding 2 PASS; negative STOP 3 PASS.
- `M35_BOUND_ACTION> PASS_EXACT_BYTES_AT_AUTHORIZED_TARGET`
- `M35_BOUND_CYCLE> AUTHORIZED_TARGET_AND_BYTES_INDEPENDENTLY_VERIFIED`
- `M35_BOUND_CYCLE> VAULT_EXECUTION_RECORDED_PASS`
- `M35_BOUND_CYCLE_RESULT> {'proposal_to_child': 'experimental_pass', 'exact_bytes': 'pass', 'vault': 'pass', 'production_stop': 'not_qualified'}`

This is the **first bounded experimental integration** of signed proposal, strict disposable E: target, AppContainer child, independently checked file bytes, and Vault execution record. No general-purpose model-selected shell command is enabled.

Limits: STOP callback in this physical run is `lambda: False`, not a live operator STOP. No continuous child cancellation or cross-process STOP qualification. Network isolation remains inconclusive. Native child accepts a strict path and expected SHA256 supplied by the trusted coordinator; it does not independently verify HMAC. This is not production-ready. Frozen ORION V1 and TheHands runtime are not part of ORION's execution substrate.

Next: test actual STOP signaling during child execution and commit, fail closed, without changing frozen modules or expanding sandbox scope.
