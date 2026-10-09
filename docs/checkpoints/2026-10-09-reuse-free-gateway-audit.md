# 2026-10-09 — Reuse the existing free-model gateway for ORION Council

## Audit finding
The existing ORION two-model advisory path is `multi_ai_existing_reviewer.py` using the donor ReviewerConnector, with explicit reviewer IDs, independent proposals, cross-reviews, and owner approval withheld. `live_two_cloud_architecture_demo.py` already exercises that path. `openrouter_vault_bridge.py` and `openrouter_text_adapter.py` provide an OpenRouter transport behind an injected vault. `free_provider_router.py` already implements deterministic bounded candidate selection.

The live four-family prototype independently builds a candidate list and handles fallbacks. It is **not** the proven gateway and should not become a second production router. Its collision diagnostics remain preserved, but are not the delivery priority.

## Immediate delivery
1. Fail closed for non-`:free` OpenRouter model IDs in the HTTP adapter (commit c7e2032), and test rejection before any network call (commit dc4ff73).
2. Physically validate the existing gateway, OpenRouter vault bridge, free-provider router, and two-model council offline. Do not trigger live calls automatically.
3. Extend the existing council interface to four distinct model families using the existing gateway and router; preserve original proposals, critiques, failures, and hashes. Fail closed if four independent families are unavailable.
4. Obtain an owner-approved plan digest before any ORION-native Hands execution. TheHands remains a separate manual test transport only.

## Safety and limits
- A `:free` suffix does not prove live callability or available quota. Never silently route to paid models.
- Check OpenRouter account-side spending controls separately; a model-ID restriction alone does not prove account-level zero spend.
- Existing Groq/Gemini provider free entitlements must be confirmed; catalog `available` alone is insufficient.
- Frozen ORION V1 Remote and Memory remain untouched. No GitHub Actions automatic triggers.
- The existing native Windows execution confinement must pass before any generated code runs.

## Status
Gateway reuse architecture audited in source. Free-only transport code committed; physical validation pending. Four-family council and native Hands execution remain unproven.
