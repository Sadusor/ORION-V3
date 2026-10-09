# Donor audit — multi-cloud routing, 2026-10-09
Status: SOURCE REVIEW; no code imported or deployed.

## Physical discovery evidence
TheHands session 8fa28e1fe998 PASS: eight offline tests; public OpenRouter catalog yielded 210 recognized-family entries and seven `:free` candidates. This is PUBLIC listing, not proof that user's API key is configured or that inference succeeds.

## Inspected owned forks
1. **Sadusor/hermes-agent** — strongest Python donor. Examined `agent/provider_registry.py`, `hermes_cli/provider_catalog.py`, and `plugins/model-providers/openrouter/__init__.py`. Has provider registry with per-scope maps and snapshot/restore, a unified provider descriptor, and explicit OpenRouter provider profile including model/endpoint handling. Reuse *ideas and narrowly extracted tested functions* only after license and dependency audit. Do not embed Hermes agent loop or replace ORION's authority.
2. **Sadusor/bifrost** — substantial Go multi-provider gateway with cross-provider tests (`core/providers/`, `core/internal/llmtests/`). Candidate for future optional sidecar, not a lightweight Python drop-in. Avoid adding Go daemon/idle consumption before benchmarks.
3. **Sadusor/LLMRouterBench** — model routing/benchmark donor, not a production credentials adapter. Useful for objective quality/latency/cost evaluation patterns.
4. **Sadusor/ORION-AI-BRIDGE**, **Sadusor/AiHub** — GitHub repositories currently empty; cannot donate working code.
5. Existing ORION `ReviewerConnector` + DPAPI `ProviderVault` — retain as proven Groq/Gemini path. Do not overwrite or replace.

## Recommendation
- Preserve existing ORION connector, vault, owner approval and STOP.
- Borrow Hermes' canonical provider-descriptor + scoped registration concept only if actual multi-provider expansion requires it; otherwise build a minimal OpenRouter adapter behind existing ORION interface.
- Reuse Hermes OpenRouter request-shaping and error-handling patterns selectively after full source/license review, not by importing a complex agent.
- Evaluate Bifrost later only if native adapters become costly or reliability warrants a gateway.
- Implement durable per-slot checkpoints and family independence without duplicating credentials or authority systems.
- Before any live inference: confirm whether OpenRouter key is already in ORION's protected vault (presence only, never print), validate adapter offline, then owner-triggered bounded live test.

## Important limitation
No donor implementation has been copied or integrated. This review establishes actual repository/source locations and architectural fit; license, full dependency and exact reusable code extraction remain open.
