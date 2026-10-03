# V3-RUN-028 — OpenHands Agent message isolation

Date: 2026-10-03

Status: **PHYSICAL FAIL — DIAGNOSTIC SUCCESS**

Remote source SHA:
`dee0156a2180cfa1fc7713597b0cc27b7e0b6c1e`

Named-task session:
`789be97afc8b`

Exact V3 SHA:
`4d072b3936f682679b97e2ef3d97bfd4e2036f24`

Observed:
- authoring preflight: PASS;
- PowerShell syntax preflight: PASS;
- V3 regression: **104 passed in 8.41s**;
- pinned OpenHands SDK: PASS;
- native_tool_calling: True;
- Agent tools: `finish,terminal,think`.

## Exact prepared messages

The real initialized Agent first-turn context contained two messages.

System message:
- role: system
- length: 15240
- SHA-256:
  `015c0664e6654f82b102391fce65e1ce3899919d7fe17c159afe77074a01fd02`
- literal `<invoke`: false
- literal `<function=`: false
- literal XML keyword: false

User message:
- length: 125
- SHA-256:
  `1bc9d05981d94e3a56448a4c6778510de075e90d3aa08c7f55fa01228eba66c2`

## Case A — minimal direct message

Observed:
- structured tool calls: 1
- assistant text length: 0
- tool: terminal
- structured tool call: **PASS**

## Case B — exact Agent-prepared messages

Observed:
- structured tool calls: 0
- assistant text length: 60
- response:

```text
```powershell
Write-Output ORION_AGENT_MESSAGE_ISOLATION
```
```

- structured tool call: **FAIL**

## Case C — Agent-prepared history without system message

Observed:
- structured tool calls: 1
- assistant text length: 0
- tool: terminal
- structured tool call: **PASS**

Diagnostic emitted:

`AGENT_SYSTEM_MESSAGE_CHANGES_TOOL_CALL_BEHAVIOR`

## Interpretation

The exact Agent-prepared first-turn context reproduces the failure without
running `Agent.step()`.

Removing the system message restores native structured tool calling.

This sharply narrows the fault boundary to the Agent system-message path rather
than:
- Ollama;
- LiteLLM;
- OpenHands LLM wrapper;
- tool registration;
- TerminalTool schema;
- security-risk schema;
- Agent response dispatch;
- tool execution.

One remaining confound must be eliminated before claiming the system message is
*sufficient by itself*: Case B used the conversation `call_context`, while
Case A/C did not. RUN-029 will test minimal+call_context and
full-system-without-call_context explicitly.

## Pinned-source audit after RUN-028

At OpenHands donor commit
`856d99d48e4b11c70c5f1cab21e7830570dbc324`:

- no literal `<invoke` string was found in the indexed SDK source;
- the stock `other` prompt snapshot contains no literal `<invoke>`,
  `<function=...>`, or XML tool protocol;
- `prepare_llm_messages()` simply converts the current conversation View's
  events to LLM Messages, optionally condenses, and appends additional
  messages;
- regular `LocalConversation.send_message()` eagerly initializes the Agent,
  so the captured SystemPromptEvent is the real first-turn Agent prompt;
- `LocalConversation.close()` explicitly closes tool executors and is the
  correct Windows cleanup boundary.

Therefore the prior hypothesis that OpenHands literally teaches the model an
`<invoke>` syntax in its stock prompt is not supported by the pinned source.

## Next gate

RUN-029:
1. eliminate `call_context` as the last confound;
2. isolate static vs dynamic system-prompt content;
3. if static content independently reproduces failure, bisect the actual
   rendered OpenHands static sections to find the smallest failing group;
4. if neither half fails while full static does, classify as a prompt
   interaction/length effect rather than a single bad section.
