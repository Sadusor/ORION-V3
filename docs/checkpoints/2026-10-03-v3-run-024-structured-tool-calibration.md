# V3-RUN-024 — OpenHands terminal calibration diagnosis

Status: **PHYSICAL FAIL — DIAGNOSTIC SUCCESS**

Remote staging SHA:
`4d3b5131d3db5ab1f66bbe295cca6f3a819812eb`

Named-task session:
`ecfe53fe1565`

Observed:
- V3 regression: **102 passed in 7.44s**
- pinned OpenHands SDK: **PASS**
- TerminalTool registered: **PASS**
- FileEditorTool registered: **PASS**
- donor-style default-tool registration: **PASS**
- Terminal-only agent policy: **PASS**
- disposable synthetic workspace: **PASS**
- OpenHands loaded one requested tool: **PASS**
- system prompt advertised: `terminal,finish,think`
- Terminal schema advertised: **PASS**
- agent errors: **0**
- ActionEvents: **0**
- Terminal actions: **0**

Raw agent reply:
```text
<invoke name="terminal">
<parameter name="command">Get-Content src\clamp.py</parameter>
</invoke>
```

Interpretation:
the model understood the requested tool action semantically, but the response
arrived as ordinary assistant text rather than a structured tool call.
OpenHands therefore had no ActionEvent to execute.

This disproves the hypothesis that the repeated zero-action result was caused
by FileEditorTool not being registered.

Current failure boundary:
`model/Ollama/LiteLLM structured tool-call transport/parsing`.

Next gate:
V3-RUN-025 calls Ollama's native `/api/chat` tools API directly with the same
Qwen3.6-35B model. If native Ollama returns structured `message.tool_calls`,
the defect is above Ollama in the LiteLLM/OpenHands transport path. If native
Ollama also returns text/no tool_calls, the defect is in the model/template/
Ollama path itself.
