# M4 cloud callback boundary — physical PASS, provider reuse pending

Physical TheHands session `23531a601091` PASS; runner `639fb7798ecc43de5c1e4f6522c2277027201f11`.

Observed: `M4_CLOUD> INJECTED_CODER_PROPOSAL_POLICY_PASS`, `M4_CLOUD> INDEPENDENT_REVIEWER_ADVISORY_PASS`, `M4_CLOUD> THREE_CLOUD_ATTACKS_DENIED_PASS`, `M4_CLOUD> NO_EXECUTION_NO_VAULT_MUTATION_PASS`. The test explicitly reports `REAL_PROVIDER_CONNECTION_NOT_YET_QUALIFIED`.

Owner confirms cloud API connections already exist in ORION V3. **Do not recreate credentials, providers, or API configuration.** Find and reuse the canonical connection implementation, including any branch-specific or runtime-only modules, before connecting this callback seam. The current work-loop branch contains `modules/local_brain.py` (loopback Ollama) and `work_loop/model_proposal.py` (earlier canonical-scope parser), so reconcile with those existing modules rather than proliferating parsers.

Provider discovery is incomplete, not evidence that connections do not exist. Do not claim real cloud calls or end-to-end autonomy until observed. TheHands remains an engineering test remote only; production execution disabled; network isolation and external STOP unqualified.
