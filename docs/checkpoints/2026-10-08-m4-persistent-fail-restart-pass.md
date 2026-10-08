# M4 persistent FAIL/restart/repaired-proposal — physical PASS (2026-10-08)

Physical TheHands session `3627cfbeb425` PASS, engineering runner `f017fcc643b7e953a2b217435b7a3921f33b2722`.

Observed:
- `M4_RECOVERY> AUTHENTICATED_FAIL_PERSISTED_PASS`
- `M4_RECOVERY> FRESH_PROCESS_RECOVERED_FAIL_PASS`
- `M4_RECOVERY> FRESH_ADAPTER_REPAIR_PROPOSAL_ACCEPTED_PASS`
- `M4_RECOVERY> UNVERIFIED_PASS_DENIED_VAULT_FAIL_PRESERVED_PASS`
- `M4_RECOVERY> REAL_QWEN_AND_VERIFIED_REPAIR_PASS_NOT_YET_QUALIFIED`

The test launched two separate Python processes against one persistent disposable Vault. The adapter used deterministic JSON fixture input, not a real Qwen model. The independent PASS gate deliberately remained closed, so **no repair PASS was recorded**. Earlier M3.5 native STOP and Qwen parser regressions also passed.

Next: build an independent verifier capable of authenticating actual observed result bytes against a bounded signed proposal; keep self-reported executor PASS denied. Then test persistent FAIL -> fresh process -> real verified repair PASS. Only after that wire a local Qwen transport. Production executor remains disabled, external STOP and network isolation not qualified.
