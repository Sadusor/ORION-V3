# V3-RUN-036T — Ollama lifecycle failure, benchmark not reached

Date: 2026-10-04

Status: **PHYSICAL FAIL — MIXED-TOOL CASE NOT EXECUTED**

Remote source SHA:
`3c0bd87ff6045c78d0c2fe4217cf2cd8f6cf28c0`

Session:
`25ae72026756`

Exact V3 gate before retry:
`6f52d926c27cdb20e77a3ee5c2206ae12607a69c`

## Durable failure

The gate reached the first Qwen/OpenHands conversation and failed in LiteLLM with:

`Ollama_chatException - [WinError 10061] No connection could be made because the target machine actively refused it`

OpenHands then raised:
`LLMServiceUnavailableError`
followed by:
`ConversationRunError`.

Therefore RUN-036T did **not** test:
- Qwen search-tool selection;
- the corrected cross-runtime adapter;
- STATUS_CASE;
- EDIT_CASE;
- DENIED_CASE.

## Cause

The mixed-tool benchmark assumed Ollama was already running.

Earlier physical gates such as RUN-035 contained a proven lifecycle helper that:
- probes `/api/tags`;
- finds `ollama.exe`;
- starts `ollama serve` headlessly when needed;
- waits for readiness;
- verifies the requested local model is installed.

That lifecycle guard was accidentally omitted when the mixed-tool benchmark was introduced.

## Promoted rule

Every local-model physical benchmark must own its Ollama lifecycle precondition.

A benchmark may not classify a model/runtime result until:
1. Ollama is reachable;
2. the exact requested model appears in the local model catalog.

## RUN-036U correction

RUN-036U reuses the proven RUN-035 lifecycle pattern:
- if Ollama is already ready, report `OLLAMA_SERVICE> ALREADY_READY`;
- otherwise start `ollama serve` with no visible console on Windows;
- wait up to 15 seconds for `/api/tags`;
- require exact `qwen3.6:35b-a3b` availability;
- only then run deterministic OpenJarvis control and the four mixed-tool cases.

The RUN-036S adapter fix remains intact:
- explicit allowlist forwards only filesystem.search business arguments;
- OpenHands internal `kind` cannot cross ORION authority;
- model may request `active_project` or `desktop`;
- lease authorizes only `active_project`;
- DENIED_CASE must therefore be rejected by ORION itself.

This failure is not evidence against Qwen, OpenHands, OpenJarvis, or the adapter fix.
