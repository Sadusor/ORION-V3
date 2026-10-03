# V3-RUN-025 — native Ollama structured tool-call calibration

Status: **PHYSICAL PASS**

Remote staging SHA:
`f4a2c7c4cebadb8e618070d34a7bf25f502d0b04`

Named-task session:
`4250ab265c82`

Observed:
- Remote UI session-focus probe: PASS
- V3 regression: **102 passed in 7.38s**
- native Ollama request: PASS
- model: `qwen3.6:35b-a3b`
- native tool call count: **1**
- assistant text length: **0**
- tool name: `marker`
- tool arguments: `{"text":"ORION_NATIVE_TOOL_CALIBRATION"}`
- native structured tool call: **PASS**
- final status: **PASS**

The native response contained a real structured `message.tool_calls` entry.

This physically proves:
- Qwen3.6-35B can perform structured tool calling;
- the installed Ollama model/template can expose that structure correctly;
- the earlier OpenHands plain-text `<invoke ...>` response is not caused by
  fundamental model incapability or Ollama native tool support.

Current fault boundary:
`LiteLLM/OpenHands transport or parsing above Ollama`.

Next isolation:
run the same one-tool request directly through the LiteLLM layer used by the
pinned OpenHands SDK, without the OpenHands Agent/Conversation loop.
