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
