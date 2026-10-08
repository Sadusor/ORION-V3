# M3.5 batched STOP-boundary evidence — 2026-10-08

Physical session: TheHands `817b8fb27743`, PASS, engineering runner commit `639b896c4c42eec279676914cb83de80265160fc`.

Observed:
- `M35_BOUND_CYCLE_RESULT> {'proposal_to_child': 'experimental_pass', 'exact_bytes': 'pass', 'vault': 'pass', 'production_stop': 'not_qualified'}`
- `M35_BATCH> PRE_CHILD DENIED_BEFORE_VAULT_PASS`
- `M35_BATCH> POST_CHILD_PRE_VAULT DENIED_BEFORE_VAULT_PASS`
- `M35_BATCH> STOP_BOUNDARY_NEGATIVES_PASS`

The STOP tests use a deterministic callback that switches at a selected check, not an external live STOP signal. POST_CHILD denial means the physical disposable write may already have happened; it does not undo the write. The experimental coordinator is not qualified for live process cancellation, network isolation, or production STOP. Keep production execution disabled.

Next: bounded live STOP signal during a deliberately slow disposable child; prove child termination, absence of execution:pass, and clean recovery. Then proceed toward Qwen-driven FAIL/restart/repair/PASS.
