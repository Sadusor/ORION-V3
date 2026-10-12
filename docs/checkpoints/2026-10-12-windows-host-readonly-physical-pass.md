# Windows host read-only probe — 2026-10-12

TheHands physical evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/32be2e1c8a30.json

- SECONDARY_LOGON: Running
- CHECKNETISOLATION_PRESENT: True
- POWERSHELL_PRESENT: True
- APP_CONTAINER_FILESYSTEM_DENIAL: NOT_TESTED
- APP_CONTAINER_NETWORK_DENIAL: NOT_TESTED
- PROCESS_TREE_STOP: NOT_TESTED
- GENERATED_CODE_EXECUTION: DISABLED
- HOST_PROBE: PASS_READ_ONLY_NOT_QUALIFIED

This does not prove an AppContainer token, sandbox isolation, filesystem denial, network denial, or STOP behavior. No generated code executed.
Next: inspect existing Windows isolation fixture/test harness and run trusted-fixture containment tests without changing frozen modules.
