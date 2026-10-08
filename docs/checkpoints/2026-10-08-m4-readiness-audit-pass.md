# M4 readiness audit — physical PASS (2026-10-08)

TheHands physical evidence `1718f859b538` (PASS), runner source `df94dc8a459d6571430b5e5488d7bcf04506f3db`.

Observed `M4_READINESS> READ_ONLY_AUDIT_PASS`, source-present checks for Vault, coordinator, engine, STOP, bounded native coordinator and native probe. Earlier signed native and STOP regressions passed in same batch, including `M35_STOP_TREE> NATIVE_CHILD_TERMINATED_AFTER_LAUNCHER_KILL`.

Explicit unqualified gates from the evidence:
- `M4_READINESS> REAL_QWEN_ADAPTER_NOT_QUALIFIED`
- `M4_READINESS> FAIL_RESTART_REPAIR_PASS_NOT_QUALIFIED`
- `M4_READINESS> PRODUCTION_EXECUTION_DISABLED`
- `QUALIFICATION> NATIVE_FIXED_ACTION_ONLY; STOP_VAULT_BINDING_NOT_QUALIFIED; NETWORK_INCONCLUSIVE`

Next engineering deliverable: a bounded, replaceable Qwen proposal adapter with strict schema and read-only deterministic fixtures; then a persistent Vault failure/restart/repaired proposal demonstration; only afterward qualify execution binding. Never modify frozen V1 Remote or independent TheHands runtime.
