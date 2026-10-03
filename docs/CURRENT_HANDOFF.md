# ORION V3 — Current Handoff

Date: 2026-10-03

Read first:

`docs/checkpoints/2026-10-03-v3-run-021-027-openhands-investigation-handoff.md`

Then read:

- `docs/STATUS.md`
- `docs/ROADMAP.md`
- `docs/ORION_SYSTEM_MODEL.md`

## Current exact situation

The common ORION WorkPackage execution envelope was physically proven in
V3-RUN-020.

The current work is qualification of a mature semantic Coding Hand.

OpenHands Agent SDK is under investigation.

Physically proven healthy:
- Qwen3.6 native structured tool calling through Ollama;
- direct LiteLLM 1.93.0 structured tool calling;
- direct OpenHands `LLM.generate()` with resolved TerminalTool;
- the same wrapper with OpenHands security-risk schema injection;
- TerminalTool/FileEditorTool registration;
- real Agent system-prompt tool advertisement.

Physically failing:
- full OpenHands Agent/Conversation path produces textual tool syntax instead
  of a structured ActionEvent.

RUN-027's process-level FAIL was cleanup-only:
the actual security-OFF and security-ON LLM wrapper diagnostics both passed,
then Windows refused to delete a temp directory still held by the Terminal
executor.

## Next action

Do not swap models yet.

Audit the exact OpenHands Agent message/system-prompt/history preparation path.

Build one small comparison with:
- same Qwen3.6 model;
- same OpenHands LLM wrapper;
- same resolved TerminalTool;
- case A: known-good minimal direct messages;
- case B: exact messages prepared by the full Agent conversation.

Capture:
- serialized messages;
- full system prompt hash/text boundary;
- dynamic context;
- tool schema;
- native_tool_calling;
- final LiteLLM kwargs;
- raw response;
- OpenHands converted Message;
- response classification.

The first layer where case B changes native structured tool calling into textual
tool syntax is the defect boundary.

## Operator workflow

Use legacy ORION Remote:

`CHECK GITHUB -> APPROVE & RUN`

Do not ask the owner to paste PowerShell unless Remote cannot execute the gate.

Always inspect durable named-session JSON before accepting phone UI PASS/FAIL as
truth.


## Legacy Remote UI live-refresh note

A separate legacy Remote presentation regression was found on 2026-10-03:
the phone/operator status only appeared current after manual page refresh.

Canonical Remote checkpoint:

`Sadusor/Orion/docs/checkpoints/2026-10-03-live-status-auto-refresh-regression.md`

GitHub source fix:
- live refresh implementation commit:
  `ddc5bd41c197a91d5eb6f98208b4af136cd9362c`
- regression-probe commit:
  `85b762f01e655fa1223ab547f67dbb4d8512a9f0`
- Remote documentation checkpoint:
  `01d3a0b25fd75f6e8582e25209704c27a2bb4c6b`

The fix restores automatic polling using a non-overlapping self-scheduling
refresh loop, explicit browser no-store, and visibility/focus/pageshow kicks.

Important:
GitHub source change does not prove the currently running Remote process has
activated the fix. Self-update/restart the Remote onto the new branch SHA, then
physically verify that a named task changes RUNNING -> PASS/FAIL on the open
phone UI without pressing REFRESH UI.


## DeepSeek review #2 and RUN-028

DeepSeek's second review agrees with the current physical evidence:
- RUN-025 eliminated native Ollama tool-calling failure;
- RUN-026 eliminated direct LiteLLM tool-call loss;
- RUN-027 eliminated direct OpenHands `LLM.generate()`, actual TerminalTool
  schema, and security-risk schema injection.

The remaining fault boundary is the full OpenHands Agent/Conversation message
preparation/runtime path.

Pinned-source follow-up performed after the review:
- no literal `<invoke` string was found in the pinned SDK search;
- the stock `other` system-prompt snapshot contains no `<invoke>`,
  `<function=...>`, or XML tool protocol;
- `prepare_llm_messages()` simply converts the current conversation View's
  events to LLM Messages, optionally condenses, and appends additional messages;
- `LocalConversation.send_message()` eagerly initializes a normal Agent before
  appending the user message, creating the real SystemPromptEvent;
- `LocalConversation.close()` explicitly closes tool executors and is the
  correct cleanup boundary for the Windows temp-workspace lock seen in RUN-027.

Therefore RUN-028 is the current staged gate.

### V3-RUN-028

Exact V3 SHA:
`4d072b3936f682679b97e2ef3d97bfd4e2036f24`

Remote staging SHA:
`dee0156a2180cfa1fc7713597b0cc27b7e0b6c1e`

Script:
`scripts/v34_openhands_agent_message_isolation_bootstrap.ps1`

Purpose:
compare, with the same Qwen3.6 model and the same resolved TerminalTool:

A. known-good minimal direct Messages;

B. exact first-turn Messages produced by the real initialized OpenHands Agent
conversation via `prepare_llm_messages(conversation.state.view, ...)`.

The diagnostic does not call `conversation.run()` or `agent.step()`.

It captures:
- message count, role, length and SHA-256;
- whether each message contains `<invoke`, `<function=`, XML, or tool-related
  text;
- native_tool_calling;
- resolved tool names;
- structured tool-call count and response text for A and B.

If A passes and B fails, the same run removes the system message as Case C.
If Case C passes, the Agent system message is sufficient to change model
behavior.

The harness explicitly calls `conversation.close()` in `finally` before the
temporary workspace exits, preventing the RUN-027 WinError 32 cleanup mistake.

Do not swap models before RUN-028 evidence is inspected.


## RUN-028 physical result and RUN-029 staged

RUN-028 Remote session:
`789be97afc8b`

RUN-028 was a **diagnostic success despite process FAIL**.

Physical evidence:
- minimal direct user message -> structured Terminal tool call PASS;
- exact Agent-prepared first-turn messages -> 0 structured tool calls and plain
  fenced PowerShell text;
- removing the Agent system message -> structured Terminal tool call PASS.

The real prepared system message was 15240 characters and contained no literal
`<invoke`, no literal `<function=`, and no XML keyword.

Canonical checkpoint:
`docs/checkpoints/2026-10-03-v3-run-028-agent-system-message-isolation.md`

Precision note:
RUN-028 Case B also supplied the conversation `call_context`, while the
minimal/no-system controls did not. The system message is the leading boundary,
but RUN-029 explicitly eliminates that last confound before declaring it
sufficient by itself.

### V3-RUN-029

Exact V3 SHA:
`8035cc70949cd373551738f36870c83dd8e987af`

Remote staging SHA:
`5f484c81ab923865e3021be57580ecd61be57dcd`

RUN-029:
1. proves whether `call_context` alone affects native tool calling;
2. tests the full Agent system message without `call_context`;
3. isolates static vs dynamic system-message blocks;
4. if one static block independently fails, recursively bisects rendered
   top-level OpenHands sections;
5. confirms whether a single section is sufficient and whether removing it
   restores tool calling.

RUN-029 changes diagnostic status semantics:
a successfully completed diagnostic returns process PASS even when it proves
`OPENHANDS_AGENT_SYSTEM_PATH> FAIL`. Harness/control failures still return
process FAIL.


## RUN-029 physical PASS and RUN-030 staged

RUN-029 Remote session:
`a3dd91b76edc`

RUN-029 is a **physical diagnostic PASS**.

Proven:
- minimal request without call_context -> structured Terminal call PASS;
- minimal request with call_context -> structured Terminal call PASS;
- full 15240-character Agent system message without call_context -> structured
  tool call FAIL;
- first 8 rendered static prompt sections (5523 chars) -> PASS;
- last 8 rendered static prompt sections (9715 chars) -> PASS;
- full 16-section prompt -> FAIL.

Therefore:
- call_context is eliminated;
- the full Agent system message is independently sufficient to suppress native
  Qwen tool calling in this calibration;
- neither top-level prompt half is independently sufficient;
- current classification is
  `STATIC_PROMPT_INTERACTION_OR_LENGTH_EFFECT`.

Canonical checkpoint:
`docs/checkpoints/2026-10-03-v3-run-029-static-prompt-interaction.md`

### V3-RUN-030

Exact V3 SHA:
`8469426defd54ce91637f6dfda5eeec59232d75a`

Remote staging SHA:
`6404824f0ab328c20e5a3d0cf2c770974eb03db5`

RUN-030 keeps the same Qwen3.6 model and resolved TerminalTool and compares:
- full original prompt;
- same exact sections with halves swapped;
- same exact sections fully reversed;
- neutral system text at the same character length;
- incremental original-order prefixes from section 8 onward.

At the first failing prefix it additionally tests:
- the newly-added boundary section alone;
- the prior passing prefix plus neutral text replacing that section at the same
  character length.

This separates:
- raw prompt length/instruction-density effects;
- section-order interactions;
- cumulative semantic interactions at a specific boundary.

Diagnostic success returns process PASS even when
`OPENHANDS_AGENT_SYSTEM_PATH> FAIL`.


## DeepSeek operator architecture review and RUN-031 staged

Independent review checkpoint:
`docs/checkpoints/2026-10-04-deepseek-operator-architecture-review.md`

Accepted:
- model proposals remain outside authority;
- Hands may be exposed as tool-shaped interfaces;
- OpenHands/OpenJarvis are donors, not authority peers;
- cloud AIs may be probabilistic capabilities;
- phone approval binds to exact immutable WorkPackage state;
- the real target is an ORION Operator Benchmark.

Correction:
ORION will use a two-lane operator model.

Lane A:
`Qwen Intent/entities -> deterministic resolver -> capability`
for routine known operations.

Lane B:
Qwen receives a task-scoped allowed tool catalog and may select the next tool
for novel/multi-step work, but ORION validates/authorizes every call and the
model cannot widen its own capability set.

This distinguishes:
- model-owned proposal/planning loop;
- ORION-owned authority/execution loop.

### V3-RUN-031

Exact V3 SHA:
`06f2bca1ea5ebc84533b89cf4066e5156dd016a3`

Remote staging SHA:
`31220ab3ca0d3e639f4a1308f2ee0118963a245a`

Purpose:
physically test the full real OpenHands Agent/Conversation loop with Qwen3.6,
TerminalTool and a compact ORION-owned inline system prompt.

PASS requires:
- exact inline ORION system prompt observed;
- real Agent loop runs;
- structured Terminal ActionEvent emitted;
- exact expected harmless command executed;
- expected observation received;
- clean conversation/tool shutdown.

Decision after RUN-031:
- PASS -> keep selected OpenHands Agent machinery as an optional operator runtime
  and immediately re-test FileEditor+Terminal on the bounded coding fixture;
- FAIL -> stop debugging OpenHands Agent orchestration and integrate its useful
  tools directly behind ORION's own operator loop.
