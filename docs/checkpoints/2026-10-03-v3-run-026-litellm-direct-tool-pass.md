# V3-RUN-026 — direct LiteLLM structured tool-call calibration

Status: **PHYSICAL PASS**

Remote staging SHA:
`23c8f3f98b77d8a0255eed8b40efc51addb5b999`

Named-task session:
`f7069749811d`

Observed:
- V3 regression: **102 passed in 7.38s**
- pinned OpenHands SDK: **PASS**
- model: `ollama_chat/qwen3.6:35b-a3b`
- direct LiteLLM request: **PASS**
- finish reason: `tool_calls`
- direct tool call count: **1**
- assistant text length: **0**
- tool: `marker`
- exact arguments: **PASS**
- final status: **PASS**

This proves the structured tool call survives:
`Qwen3.6 -> Ollama -> LiteLLM 1.93.0`.

Combined with RUN-025, the current failure boundary is above raw LiteLLM:
the OpenHands SDK LLM wrapper/tool transformation or Agent prompt/history path.

Next gate:
V3-RUN-027 calls the pinned OpenHands `LLM.generate()` directly with the
resolved TerminalTool, first without and then with security-risk schema
injection, but without running the Agent loop.
