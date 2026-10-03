# ORION V3 — OpenHands semantic Coding Hand investigation handoff

Date: 2026-10-03

Status: **INVESTIGATION ACTIVE — fault boundary narrowed to OpenHands Agent prompt/history path**

This checkpoint supersedes earlier provisional interpretations that treated zero
ActionEvents as direct evidence that a Qwen model could not serve as a Coding Hand.
Later physical calibration proved that Qwen3.6, Ollama, LiteLLM, and the OpenHands
LLM wrapper can all preserve native structured tool calls. The remaining suspect
is the OpenHands Agent-generated prompt/history/step path.

## Frozen architecture boundary

ORION remains the authority. A mature coding agent is only a candidate semantic
Coding Hand.

Allowed benchmark pattern:

`bounded task -> disposable exact-SHA worktree -> untrusted agent candidate ->
Git diff -> immutable WorkPackage -> review -> ORION decision -> current Attempt
lease -> proven RUN-020 executor -> verifier -> evidence/result -> cleanup`

The agent does not own canonical state, Memory, approvals, leases, Stop, merge,
push, commit, or arbitrary host authority.

## Proven base before this investigation

- RUN-014 semantic governor: physical PASS.
- RUN-015 canonical state/Memory: physical PASS.
- RUN-016 Event Exchange: physical PASS.
- RUN-017 named-task Remote transport: physical PASS.
- RUN-018 WorkPackage candidate artifact path: physical PASS.
- RUN-019 durable Attempt ownership / generation fencing: physical PASS.
- RUN-020 common WorkPackage execution envelope: physical PASS.

RUN-020 remains the trusted execution boundary.

## RUN-021 — first OpenHands semantic Coding Hand benchmark

Goal:
real OpenHands Agent SDK loop + local Qwen3.5-9B + FileEditorTool only in an
expendable candidate worktree, then freeze the resulting Git patch into a
WorkPackage and execute it only through RUN-020.

### Attempt 1

Session: `9f02171bc6a4`

Failure:
benchmark harness called nonexistent `LocalConversation.get_messages()` after
`conversation.run()`.

Classification:
`HARNESS_API_MISMATCH`.

Agent/model/execution-envelope result: **NOT SCORED**.

Fix:
use pinned SDK utility
`get_agent_final_response(conversation.state.events)`.

### Attempt 2

Session: `81d811ce1315`

Observed:
- OpenHands loop ran.
- FileEditor-only policy held.
- Terminal authority: NONE.
- Qwen3.5-9B available.
- ActionEvents: 0.
- changed paths: none.

The run used `ollama/qwen3.5:9b`.

Pinned donor evidence showed local tool-calling examples use
`ollama_chat/<model>` and reasoning disabled.

Classification at the time:
`LOCAL_PROVIDER_CONFIGURATION_MISMATCH`.

Model result: **NOT SCORED**.

### Corrected Qwen3.5-9B runs

Remote source SHA:
`1bb19c948fc54a3480404918de7cf577146ad29e`

Sessions included:
- `a731a30495a8`
- `e1568ea6468c`

Configuration:
- `ollama_chat/qwen3.5:9b`
- `reasoning_effort="none"`
- FileEditorTool only
- no TerminalTool

Both produced:
- real OpenHands loop
- 0 ActionEvents
- 0 file changes

This was initially recorded as
`OpenHands + Qwen3.5-9B = benchmark FAIL`.

**Reclassification after RUN-024/025/026/027:**
this remains a physical failure of the complete OpenHands Agent-loop pairing,
but it is **not sufficient evidence that Qwen3.5-9B itself lacks tool-calling
capability**. The Agent prompt/history path is now the leading failure boundary.
Do not use these runs as a final model-quality ranking.

## Remote duplicate-run issue discovered during RUN-021

Two identical sessions were launched ~0.4 seconds apart for the same
`(source_sha, task_id)`.

Root cause:
`SessionSupervisor.start_powershell` lacked single-flight protection.

Fix:
an active identical `source_sha + task_id` now returns the existing session
instead of spawning a second process. Different tasks remain able to run in
parallel.

A regression was added to the multisession dispatch probe.

## RUN-022 — Qwen2.5-32B

Session:
`a11f5224268b`

Result:
**NOT TESTED**.

Reason:
`qwen2.5:32b` was not present in the live Ollama inventory, so the run stopped
before OpenHands.

Do not count this as a model or framework failure.

The benchmark was improved so a missing model prints the installed Ollama model
inventory.

## RUN-023 — Qwen3.6-35B-A3B semantic Coding Hand

Session:
`d28e5147ff8c`

Model:
`qwen3.6:35b-a3b`

Observed:
- V3 regression: PASS.
- model available: PASS.
- FileEditor-only policy: PASS.
- exact-SHA candidate worktree: PASS.
- real OpenHands Agent loop: PASS.
- ActionEvents: 0.
- changed paths: none.

At this point the repeated zero-action result across models triggered a deeper
calibration instead of more model swapping.

**Reclassification after later gates:**
this is a physical failure of the OpenHands Agent-loop path, not evidence that
Qwen3.6 cannot produce structured tool calls.

## DeepSeek review #1

Useful recommendation:
stop model swapping and run a donor-faithful Terminal-only calibration with raw
event inspection.

Incorrect claim:
DeepSeek suggested FileEditorTool was likely not registered because
`register_default_tools()` had not been called.

Pinned SDK source disproved that:
`FileEditorTool` and `TerminalTool` call `register_tool(...)` automatically
when their definition modules are imported. The donor's default preset also
states tools auto-register on import.

The useful isolation experiment was retained; the incorrect registration theory
was not adopted.

## RUN-024 — donor-faithful OpenHands Terminal calibration

First attempt:
session `f9b29bf3e8c1`.

Failure:
bootstrap invoked `--package openhands-tools` from the ORION-V3 uv workspace
instead of the pinned OpenHands SDK workspace.

Classification:
`HARNESS_WORKSPACE_MISMATCH`.
Diagnostic not reached.

Corrected attempt:
session `ecfe53fe1565`.

Observed:
- OpenHands SDK v1.49.2.
- TerminalTool registered: PASS.
- FileEditorTool registered: PASS.
- default-tool registration path executed.
- one Terminal tool loaded.
- system prompt advertised: `terminal,finish,think`.
- Terminal schema advertised: PASS.
- AgentErrorEvents: 0.
- ActionEvents: 0.
- Terminal actions: 0.

Raw assistant message:

```text
<invoke name="terminal">
<parameter name="command">Get-Content src\clamp.py</parameter>
</invoke>
```

Interpretation:
Qwen understood the desired tool operation semantically, but the OpenHands
Agent path received it as ordinary assistant text rather than a structured
tool call. No ActionEvent could be executed.

This physically disproved the unregistered-tool hypothesis.

## RUN-025 — native Ollama tool-call calibration

Remote source SHA:
`f4a2c7c4cebadb8e618070d34a7bf25f502d0b04`

Session:
`4250ab265c82`

Status:
**PHYSICAL PASS**.

Model:
`qwen3.6:35b-a3b`

Native Ollama `/api/chat` response contained:

- `message.tool_calls`: 1
- assistant content length: 0
- function: `marker`
- arguments:
  `{"text":"ORION_NATIVE_TOOL_CALIBRATION"}`

Conclusion:
Qwen3.6 and the installed Ollama model/template can produce real structured tool
calls.

## RUN-026 — direct LiteLLM tool-call calibration

Remote source SHA:
`23c8f3f98b77d8a0255eed8b40efc51addb5b999`

Session:
`f7069749811d`

Status:
**PHYSICAL PASS**.

Path:
`Qwen3.6 -> LiteLLM 1.93.0 -> Ollama`

Observed:
- `finish_reason="tool_calls"`
- direct tool call count: 1
- assistant text length: 0
- function: `marker`
- exact arguments: PASS

Conclusion:
raw LiteLLM preserves native structured tool calling correctly.

## RUN-027 — direct OpenHands LLM wrapper calibration

Purpose:
bypass the Agent loop while using the pinned OpenHands `LLM.generate()` wrapper
and the actual resolved TerminalTool schema.

Two cases:
1. `add_security_risk_prediction=False`
2. `add_security_risk_prediction=True`

### First attempt

Session:
`10bb0d8a9216`

Failure:
the harness accessed `agent.tools_map` before Agent initialization.

Classification:
`HARNESS_AGENT_INIT_DEPENDENCY`.
Diagnostic not reached.

R2 fix:
resolve the actual tool directly with
`TerminalTool.create(conversation.state)[0]` and never call the Agent loop.

### R2 physical result

Remote source SHA:
`208a9e183f7c4c6e7f158076130d15a4e9842be1`

Session:
`331806d502d4`

Phone/durable session result:
FAIL, but the diagnostic itself succeeded before cleanup.

Observed:

```text
SECURITY_OFF_TOOL_CALL_COUNT> 1
SECURITY_OFF_TEXT_LENGTH> 0
SECURITY_OFF_TOOL_NAME> terminal
SECURITY_OFF_STRUCTURED_TOOL_CALL> PASS

SECURITY_ON_TOOL_CALL_COUNT> 1
SECURITY_ON_TEXT_LENGTH> 0
SECURITY_ON_TOOL_NAME> terminal
SECURITY_ON_STRUCTURED_TOOL_CALL> PASS
```

Therefore the pinned OpenHands `LLM.generate()` wrapper successfully preserves
structured Terminal tool calls both without and with the exact security-risk
schema injection used by the Agent.

The process returned FAIL only because Windows could not delete the temporary
workspace:

`PermissionError / WinError 32`

The Terminal executor still held a handle to the temp directory during
`TemporaryDirectory.__exit__`.

Classification:
- diagnostic: **PASS**
- wrapper tool calling: **PASS**
- security schema: **PASS**
- harness cleanup: **FAIL**
- Agent loop: **NOT RUN**

This failure must not be interpreted as an LLM/tool-call failure.

## Current evidence chain

Physically proven healthy:

1. `Qwen3.6 -> Ollama native tools`: PASS.
2. `Qwen3.6 -> LiteLLM 1.93.0 -> Ollama`: PASS.
3. `Qwen3.6 -> OpenHands LLM.generate() -> resolved TerminalTool`: PASS.
4. same OpenHands wrapper with security-risk schema injection: PASS.
5. Terminal/FileEditor registration: PASS.
6. Terminal schema advertisement in the real Agent conversation: PASS.

Physically failing:

`Qwen3.6 -> full OpenHands Agent/Conversation step`

In the full Agent path the model produced plain assistant text in an
`<invoke ...>` format and OpenHands created 0 ActionEvents.

## Current fault boundary

The leading suspect is now the OpenHands **Agent-generated messages / system
prompt / history / preparation path before LLM.generate()**, not:

- Qwen3.6 fundamental capability;
- Ollama native tool calling;
- LiteLLM native tool preservation;
- tool registration;
- TerminalTool resolution;
- OpenHands LLM wrapper;
- security-risk schema injection;
- ORION execution containment.

Likely next isolation should compare the exact messages generated by the Agent
(`prepare_llm_messages(state.view, ...)`) with a minimal direct
`LLM.generate()` request while holding the same resolved tools constant.

The objective is to identify what changes the model from native structured
`tool_calls` to textual `<invoke ...>`.

## Important clue

The pinned OpenHands SDK contains a non-native function-calling fallback in:

`openhands-sdk/openhands/sdk/llm/mixins/non_native_fc.py`

Its prompt-mocked canonical syntax is:

```text
<function=tool_name>
<parameter=name>value</parameter>
</function>
```

But RUN-024's model emitted:

```text
<invoke name="terminal">
<parameter name="command">...</parameter>
</invoke>
```

That syntax does not match the OpenHands fallback parser's canonical
`<function=...>` form.

However, the direct OpenHands LLM wrapper in RUN-027 had
`native_tool_calling=True` and returned native structured tool calls, so the
remaining question is what the full Agent's generated prompt/history does to
the model's response behavior.

## Cleanup lesson from RUN-027

When a calibration creates a TerminalTool/TerminalExecutor on Windows, close or
dispose the executor/session before leaving the temporary directory. Do not let
temp-folder cleanup determine diagnostic PASS/FAIL after the diagnostic result
has already been collected.

Promote this into the next harness so physical status matches diagnostic truth.

## Do not do next

Do not:
- swap more models yet;
- blame Qwen3.5 or Qwen3.6 as incapable based on the earlier zero-action Agent runs;
- re-debug tool registration;
- re-debug raw Ollama or raw LiteLLM;
- weaken ORION authority;
- give OpenHands the real repository;
- bypass WorkPackage / Attempt / exact-SHA verification;
- connect a model directly to arbitrary host authority.

## Recommended next step

Ask an independent reviewer to audit the **Agent message/prompt construction
path**, then build one small physical comparison:

`same Qwen3.6 + same OpenHands LLM + same resolved TerminalTool`

A. minimal direct messages that already PASS.

B. exact Agent-prepared messages from the RUN-024 conversation.

Compare:
- serialized messages;
- system prompt text;
- dynamic context;
- tool schemas;
- native_tool_calling value;
- call kwargs;
- response type/tool_calls/content.

The first differing layer that converts native tool behavior into textual
`<invoke ...>` is the bug boundary.

## Remote execution rule

Continue using:

`CHECK GITHUB -> APPROVE & RUN`

Do not ask the human to paste PowerShell manually unless Remote cannot perform
the operation.

Always inspect the durable named-task session JSON before treating the phone
label as authoritative.
