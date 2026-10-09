# Groq and Gemini donor connector verification gate

The physically tested OpenRouter family preflight is frozen. Its most recent session 2809df8f7d93 passed, but confirmed only one responsive family (Nemotron Super); Gemma was rate-limited and Nemotron Nano returned malformed output.

The existing donor catalog's `available` field indicates a configured or listed candidate, not proven no-cost entitlement. Do not silently upgrade it to `free=True`. No donor connector modifications, no automatic cloud calls, and no generated code execution.

Next steps: (1) inspect existing donor provider configuration and free-tier metadata read-only, without displaying secrets; (2) require explicit provider-specific evidence of no-cost eligibility; (3) only then authorize a bounded, owner-triggered live probe; (4) retain four distinct model-family requirement before council execution. Do not infer availability from the catalog or count two models of the same family as independent families.

No owner approval of the task tracker design has been granted. TheHands remains separate physical test transport; V1 Remote and Memory remain frozen.
