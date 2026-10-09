# Hermes OpenRouter extraction decision (2026-10-09)

Inspected `Sadusor/hermes-agent/LICENSE` (MIT; copyright Nous Research 2025), `plugins/model-providers/openrouter/__init__.py` and `agent/provider_registry.py`.

Hermes' OpenRouter profile is not a standalone HTTP adapter. It imports Hermes' `agent.portal_tags`, `agent.transports.codex`, `providers` registry and `ProviderProfile`; model fetch delegates to inherited implementation. Directly copying this profile would drag in Hermes agent dependencies and violate ORION's small replaceable substrate goal.

Reusable concrete patterns:
- Canonical OpenRouter endpoint `https://openrouter.ai/api/v1`, models endpoint `/models`, key identifier `OPENROUTER_API_KEY`.
- Keep provider endpoint routing explicit rather than silently changing model variants.
- Scoped provider registry with reserved builtin names; only needed when more than one independent adapter exists.
- Preserve attribution of provider and model; keep model catalog separate from invocation.
- Any substantial copied code must retain MIT copyright and permission notice.

Decision: implement a tiny ORION-native stdlib HTTP adapter in a separate module, inspired by these patterns but not copying Hermes code; inject credential at call time from existing DPAPI vault only. Do not alter original `ReviewerConnector` or vault. No automatic execution of returned text.

Next: offline mock HTTP tests, then read-only credential-presence diagnostics on owner PC, then bounded live inference only on owner-run test.
