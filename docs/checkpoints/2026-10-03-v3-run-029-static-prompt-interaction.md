# V3-RUN-029 — OpenHands static prompt interaction diagnosis

Date: 2026-10-03

Status: **PHYSICAL PASS — DIAGNOSTIC COMPLETE**

Remote source SHA:
`5f484c81ab923865e3021be57580ecd61be57dcd`

Named-task session:
`a3dd91b76edc`

Exact V3 SHA:
`8035cc70949cd373551738f36870c83dd8e987af`

## Regression / harness

- V3 regression: PASS
- pinned OpenHands SDK: PASS
- native_tool_calling: True
- Agent tools: `finish,terminal,think`

## Call-context confound eliminated

Minimal request, no call context:
- structured Terminal tool call: PASS

Minimal request, with conversation call context:
- structured Terminal tool call: PASS

Therefore `call_context` does not explain RUN-028.

## Full system prompt without call context

System length:
`15240`

System SHA-256:
`015c0664e6654f82b102391fce65e1ce3899919d7fe17c159afe77074a01fd02`

Observed:
- tool calls: 0
- assistant text: plain prose + fenced PowerShell
- structured tool call: FAIL

Therefore the Agent system message is independently sufficient to change
Qwen3.6 from native structured tool use to plain text for this calibration.

## Static prompt section bisect

Rendered top-level sections:
1. SOUL
2. ROLE
3. MEMORY
4. EFFICIENCY
5. FILE_SYSTEM_GUIDELINES
6. CODE_QUALITY
7. VERSION_CONTROL
8. PULL_REQUESTS
9. PROBLEM_SOLVING_WORKFLOW
10. SELF_DOCUMENTATION
11. SECURITY
12. SECURITY_RISK_ASSESSMENT
13. EXTERNAL_SERVICES
14. ENVIRONMENT_SETUP
15. TROUBLESHOOTING
16. PROCESS_MANAGEMENT

First 8 sections:
- length: 5523
- structured Terminal tool call: PASS

Last 8 sections:
- length: 9715
- structured Terminal tool call: PASS

Combined full prompt:
- length: 15240
- structured Terminal tool call: FAIL

Diagnostic:
`STATIC_PROMPT_INTERACTION_OR_LENGTH_EFFECT`

This disproves the current hypothesis that one of the two top-level halves is
independently sufficient to break native tool use.

## Current fault boundary

Healthy:
- Qwen3.6 native Ollama tools;
- LiteLLM native tool preservation;
- OpenHands LLM wrapper;
- real TerminalTool schema;
- security-risk schema injection;
- call_context;
- either half of the default OpenHands static system prompt.

Failing:
- the full default static OpenHands Agent system prompt.

Current unresolved alternatives:
1. prompt-length effect;
2. cumulative instruction-density effect;
3. interaction between sections that live in different halves;
4. deterministic threshold in Qwen/Ollama behavior under the full system prompt.

## Next gate

RUN-030 should distinguish length from semantics with the same model/tool:
- known-good half prompt;
- the same half padded to full-system character/token scale with neutral text;
- full original prompt;
- original prompt reduced incrementally / prefix accumulation to locate the
  first failing size;
- confirm the boundary with a second equivalent-length neutral control.

Do not swap models before this is resolved.
