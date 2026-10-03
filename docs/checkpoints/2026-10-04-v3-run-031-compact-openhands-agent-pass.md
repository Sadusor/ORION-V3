# V3-RUN-031 — compact ORION prompt restores full OpenHands Agent path

Date: 2026-10-04

Status: **PHYSICAL PASS**

Remote source SHA:
`31220ab3ca0d3e639f4a1308f2ee0118963a245a`

Named-task session:
`4a651a566a36`

Exact V3 SHA:
`06f2bca1ea5ebc84533b89cf4066e5156dd016a3`

## Regression / transport

- Remote UI session-focus/live-refresh probe: PASS
- V3 exact SHA: PASS
- authoring preflight: PASS
- PowerShell syntax preflight: PASS
- V3 regression: **113 passed in 9.19s**
- pinned OpenHands SDK:
  `856d99d48e4b11c70c5f1cab21e7830570dbc324`

## Compact prompt

Configured compact ORION prompt length:
`460`

Observed Agent system prompt length:
`460`

Exact inline prompt equality:
`CUSTOM_SYSTEM_PROMPT_EXACT> PASS`

Therefore the full Agent was physically running the ORION-owned compact prompt,
not the stock OpenHands prompt.

## Real full Agent loop

Model:
`ollama_chat/qwen3.6:35b-a3b`

Tool set:
- TerminalTool
- FinishTool

Observed:
- wall time: `40.996s`
- ActionEvents: 2
- Terminal ActionEvents: 1
- ObservationEvents: 2
- AgentErrorEvents: 0

Exact Terminal action:

`Write-Output ORION_COMPACT_AGENT_CALIBRATION`

Terminal observation contained:

`ORION_COMPACT_AGENT_CALIBRATION`

The next Agent action was the real FinishTool.

Physical markers:
- `REAL_AGENT_STRUCTURED_TERMINAL_ACTION> PASS`
- `EXPECTED_TERMINAL_COMMAND> PASS`
- `EXPECTED_TERMINAL_OBSERVATION> PASS`
- `OPENHANDS_COMPACT_AGENT_PATH> PASS`

Diagnosis:
`COMPACT_ORION_PROMPT_RESTORES_FULL_AGENT_TOOL_PATH`

## Architectural consequence

Stop debugging the stock OpenHands 15k system prompt.

OpenHands Agent/Conversation machinery remains a viable optional operator runtime
when ORION supplies the compact role prompt.

The donor remains below ORION authority:
- OpenHands proposes/executes only exposed tools inside the candidate workspace;
- ORION owns capability scope, approval, Task/Attempt truth, WorkPackages,
  execution authority, evidence and verification.

This result does **not** mean OpenHands becomes ORION's control plane.

## Next gate

V3-RUN-032 should repeat the bounded semantic coding task with:
- compact ORION prompt;
- FileEditorTool + TerminalTool;
- disposable exact-SHA candidate workspace;
- no push/merge/commit authority;
- deterministic changed-path and functional checks;
- resulting diff frozen as a WorkPackage;
- final application only through the already-proven RUN-020 execution envelope.

If this passes, stop treating OpenHands as an isolated benchmark target and move
to the broader ORION mixed-tool Operator Benchmark.
