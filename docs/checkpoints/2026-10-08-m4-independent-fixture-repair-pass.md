# M4 independent fixture recovery PASS — 2026-10-08

Physical TheHands evidence session `de43c0d874cd` PASS; engineering runner `14d25a51bebe81bfdd2b8237e791e239a0aee5bf`.

Observed:
- `M4_RECOVERY> AUTHENTICATED_FAIL_PERSISTED_PASS`
- `M4_RECOVERY> FRESH_PROCESS_RECOVERED_FAIL_PASS`
- `M4_RECOVERY> FRESH_ADAPTER_REPAIR_PROPOSAL_ACCEPTED_PASS`
- `M4_RECOVERY> UNVERIFIED_PASS_DENIED_VAULT_FAIL_PRESERVED_PASS`
- `M4_RECOVERY> WRONG_BYTES_REJECTED_FAIL_PRESERVED_PASS`
- `M4_RECOVERY> STOP_BLOCKED_VERIFIER_PASS`
- `M4_RECOVERY> INDEPENDENT_FIXTURE_BYTES_VERIFIED_AND_VAULT_PASS`
- `M4_RECOVERY> REAL_QWEN_AND_NATIVE_REPAIR_EXECUTION_NOT_YET_QUALIFIED`

Scope: two separate Python processes, persistent disposable Vault, deterministic proposal fixture and direct test setup of repaired file bytes. Trusted fixture verifier checks exact bytes and records test:pass, bypassing no production engine gate because it is explicitly experimental and restricted to test fixture. **This is not real Qwen inference or native repair execution.** Existing production evidence gate remains closed; network and external STOP qualification pending.

Next: add local Qwen transport behind replaceable adapter; obtain actual bounded proposal without giving model execution authority. Test real model output and rejection cases before wiring native execution.
