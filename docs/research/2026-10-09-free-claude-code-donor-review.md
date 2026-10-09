# Donor review: Free Claude Code (2026-10-09)

Source: https://github.com/Alishahryar1/free-claude-code (inspected main README, LICENSE, pyproject.toml and source).
Status: donor evaluation only; not installed, imported, or executed.

## Verified code
- Provider-agnostic catalog: `src/free_claude_code/config/provider_catalog.py` separates provider IDs, credential names, base URLs and capabilities from adapter factories. Concrete provider folders include Groq, Gemini, DeepSeek, OpenRouter and others.
- `src/free_claude_code/providers/open_router/client.py` adapts OpenRouter on its shared OpenAI-compatible chat abstraction, rather than implementing HTTP per provider.
- `src/free_claude_code/providers/failure_policy.py` canonicalizes auth, permission, rate limit, overload, context-window and transient provider failures.
- `src/free_claude_code/providers/continuation.py` tracks whether a partially streamed response can safely be resumed/handed off based on native reasoning, signatures, content and tool state.
- Tests include `smoke/product/test_model_fallback_product_live.py` and `smoke/product/test_openrouter_free_cli_product_live.py`.
- README *claims* 59 providers, 11 coding harnesses, fallback support and very large monthly free quotas. These are upstream claims; do not count as our verified capacity.

## License / deployment fit
- `LICENSE` and `pyproject.toml` declare **AGPL-3.0-only**, and Python **3.14.7** pinned. Full runtime has a broad dependency set (FastAPI, httpx, OpenAI SDK, various messaging/cloud packages), and a proxy/server model.
- Do NOT copy AGPL code into ORION without explicit license assessment; prefer describing behaviors and writing independently tested original code.
- Do NOT install the project or its Windows install.ps1 on the user's PC, change provider credentials, or attach it to the frozen V1 Remote.
- This is **not** an appropriate direct replacement for ORION's authority-controlled native Work Hand or frozen ReviewerConnector.
- Optional later benchmark as an isolated service only if provider breadth outweighs its idle resource cost, operations complexity, and licensing obligations.

## Priority for ORION
1. Independently implement strict failure categories, bounded retries and *explicit* failover selection (no silent substitution of council family or reviewer slots); capture evidence for each attempt.
2. Preserve STOP, owner approval, provenance, per-slot independence and cost ceilings.
3. Keep provider catalog separate from HTTP transport, vault storage, and council policy.
4. Reject in-progress automatic handoff of partial reasoning or tool calls; our present proposal-only text route doesn't need streaming recovery.
5. Benchmark against Hermes MIT donor. Existing Groq/Gemini provider path stays untouched.

This is a source review, not a claim of integrated or physically tested donor behavior.
