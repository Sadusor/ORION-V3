# M3.5 experimental chain PASS — 2026-10-08

Physical evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/70b90bcad3fb.json
TheHands manual transport source commit: `c5f72104c42b5f6d8f5f53942c32f220073cb24c`.

Results: existing offline regression 28/28 PASS; fixed-action preflight 1/1 PASS; signed plan PASS; native AppContainer fixed-action child PASS; inside write ALLOW, outside read/write DENY, outside sentinel unchanged, profile cleanup PASS. New `m35_experimental_cycle.py` executed signed authorization preflight -> native fixed fixture -> native marker/evidence checks -> existing ProjectVault `record_verified_result` -> STATE/JOURNAL readback, with `M35_CYCLE> VAULT_RECORDED_PASS`.

Boundary: signed proposal workspace is NOT the native fixture workspace. The native child is not cryptographically bound to the signed action, so Vault evidence here attests to the separate native fixture only; it must NOT be treated as verified execution of the proposal's target file. STOP callback in physical run was `lambda: False`, not authoritative. Network isolation, descendants, cross-process STOP/commit remain unqualified. Production Work Hand disabled.

Next: correct evidence semantics to avoid confusing fixture PASS with proposal execution PASS; implement exact signed proposal-to-native-child binding and physical STOP denial tests before any promotion. Do not modify frozen Remote V1 or treat TheHands as ORION runtime component.
