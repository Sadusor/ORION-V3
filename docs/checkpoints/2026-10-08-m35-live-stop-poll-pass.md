# M3.5 live-poll STOP experiment — PASS (2026-10-08)

Physical TheHands evidence: `cf3a999d47d1`, result PASS, engineering runner commit `5e8546c3951c722b28b34238427dd4bf6ec06d19`.

Observed:
- `M35_BOUND_CYCLE_RESULT> {'proposal_to_child': 'experimental_pass', 'exact_bytes': 'pass', 'vault': 'pass', 'production_stop': 'not_qualified'}`
- `M35_BATCH> PRE_CHILD DENIED_BEFORE_VAULT_PASS`
- `M35_BATCH> DURING_CHILD DENIED_BEFORE_VAULT_PASS`
- `M35_BATCH> PRE_CHILD_AND_LIVE_POLL_NEGATIVES_PASS`

Earlier post-child/pre-Vault STOP boundary proof: session `817b8fb27743`. Live polling was added in ORION commit `f5c5c3f3911811f943277af9bc69fc5f316356cc`; the new test uses deterministic callback STOP after second invocation. It proves a bounded cancellation path through the launcher but **does not** establish external operator STOP, termination of native descendants, or absence of orphaned processes. Physical operation may have occurred before cancellation; no rollback claim. Network isolation remains inconclusive. Production executor remains disabled.

Next gate: externally signaled STOP, native process-tree cleanup and no execution:pass, then FAIL/restart/repair/PASS with Qwen.
