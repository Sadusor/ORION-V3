# Free cloud budget monitor — implementation plan

Owner requirement: know when free tokens/requests are nearly exhausted before a multi-AI council stalls.

Implemented offline classification: `src/orion_v3/work_loop/free_quota_monitor.py` and 12 regression tests. No live provider quota API integration yet. States: UNKNOWN (default if provider exposes no remaining quota), AVAILABLE (verified positive remaining), LOW (verified <=15% token allowance), EXHAUSTED (verified zero tokens/requests), COOLDOWN (rate-limited). Do not interpret HTTP 429 as a known token balance; a provider may rate-limit for different reasons.

Next integration:
1. OpenRouter: inspect actual documented account/key credits, model-level free request limits and response usage metadata. Keep credit balance separate from free-model request quotas. Never call paid models to test quotas.
2. Groq and Gemini: inspect documented response usage and provider rate-limit headers/API. Do not invent reset times or quotas if absent. Avoid leaking API keys, headers, response text, or account metadata.
3. Record safe per-call provider/model, prompt/completion/total tokens when supplied, 429 category, verified remaining requests/tokens and reset timestamp when supplied, timestamp, source. Missing fields stay null/UNKNOWN.
4. Router must prefer healthy models with sufficient known quota, use cooldown after 429, bounded retry/fallback, preserve four-family independence. UNKNOWN may be attempted within a bounded budget, never shown as unlimited.
5. UI later: provider/model, state, remaining only when verified, usage per day, cooldown countdown only when reset is verified, next fallback and confidence/source. Display no fabricated percentages.
6. Run 12 offline tests via owner-approved physical test launcher; do not trigger automatic GitHub Actions.

This monitor is a replaceable sidecar; frozen ORION V1 Remote, Memory and authority untouched. TheHands is a separate owner-controlled evidence transport only.
