# M4 Qwen proposal adapter — physical PASS (2026-10-08)

TheHands session `2c432df075e5` PASS; runner commit `78923970c9dff149001812a3e49b42479da88862`.

Observed:
- `M4_QWEN_ADAPTER> BOUNDED_GREEN_PASS`
- `M4_QWEN_ADAPTER> NINE_NEGATIVE_CASES_DENIED_PASS`
- `M4_QWEN_ADAPTER> NO_EXECUTION_NO_VAULT_MUTATION_PASS`
- `M35_STOP_TREE> NATIVE_CHILD_TERMINATED_AFTER_LAUNCHER_KILL`

The adapter parses bounded JSON and applies canonical project/task identity and ORION policy. The test uses deterministic offline model-output fixtures, **not an actual Qwen invocation**. No execution or Vault state mutation occurred. Production execution remains disabled; network isolation and external STOP integration unqualified.

Next: physically test authenticated FAIL persisted to Vault, process restart, fresh adapter instance, independently verified repaired PASS and rejection of stale/wrong-task evidence.
