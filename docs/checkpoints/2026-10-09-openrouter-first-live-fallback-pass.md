# OpenRouter-first live fallback — physical PASS (2026-10-09)

Owner-approved TheHands PowerShell 1 physical session: `afcbd4201c30`; result PASS.
This is evidence transport only; TheHands is a separate product and not ORION's native Work Hand.

## Observed bounded live sequence
1. OpenRouter free catalog: 15 candidate models.
2. OpenRouter `google/gemma-4-26b-a4b-it:free`: RATE_LIMIT.
3. OpenRouter `google/gemma-4-31b-it:free`: RATE_LIMIT.
4. Existing private Groq connector `openai/gpt-oss-120b`: PASS, response length 1027 characters.
5. Script returned `ORION_CATALOG> PASS_READ_ONLY`.

The OpenRouter API key was present in the owner Windows user environment and was read by the launcher; neither key nor model response was printed. The selected OpenRouter models had explicit zero pricing in the catalog. There was no model-generated code execution, owner approval, or native Hand execution.

## Claim limits
Proven: live free-first attempt order; categorized RATE_LIMIT outcomes; successful Groq fallback in this single owner-approved run. Not proven: successful OpenRouter inference, Gemini recovery, durable health/cooldown across runs, four distinct model-family live council, automatic production fallback orchestration, native Windows confinement, STOP during blocking request, autonomous build loop.

## Next
1. Integrate verified free-first candidate planning, health cooldown and fallback into the four-slot council with independent families; test offline and then owner-approved live.
2. Record model identity, bounded retries, response hashes, independent reviews, failure categories and checkpoint evidence without secrets.
3. Advance the tiny SQLite tracker proposal and owner-review gate before any generated patch execution.
4. Keep GitHub Actions push-triggered testing disabled on the active branch; physical tests require owner action.
