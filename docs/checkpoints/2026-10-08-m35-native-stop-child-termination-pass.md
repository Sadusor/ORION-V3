# M3.5 native child STOP termination — physical PASS (2026-10-08)

TheHands engineering evidence session: `f9b318711a94`, result PASS, runner commit `9d4186e09d4999c032b0cd21ab16013283fe7781`, ORION experimental source `0923b59b6e8b3db3bb62accdb4c8ca6a746de178`.

Observed markers:
- `M35_BOUND_CYCLE_RESULT> {'proposal_to_child': 'experimental_pass', 'exact_bytes': 'pass', 'vault': 'pass', 'production_stop': 'not_qualified'}`
- `M35_BATCH> PRE_CHILD DENIED_BEFORE_VAULT_PASS`
- `M35_BATCH> DURING_CHILD DENIED_BEFORE_VAULT_PASS`
- `M35_STOP_TREE> NATIVE_CHILD_TERMINATED_AFTER_LAUNCHER_KILL`
- `M35_BATCH> STOP_PROCESS_TREE_NATIVE_CHILD_TERMINATED_PASS`

Mechanism: experimental native probe holds its suspended AppContainer child after assignment to a kill-on-close Windows Job Object; a timed STOP callback kills the .NET launcher; coordinator reads the child's PID and uses Win32 WaitForSingleObject to confirm termination. This proves this specific bounded held-child test only. It is not evidence of arbitrary process-tree cleanup, external owner STOP integration, general filesystem/network isolation or production safety. STOP may not undo a completed write. Production executor stays disabled.

Next milestone: wire existing ORION STOP signal, test external cancellation and Vault commit seam; then bounded Qwen proposal + deliberate FAIL/restart/fresh-Qwen repair/PASS.
