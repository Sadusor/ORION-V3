# V3-RUN-030 — OpenHands prompt density / interaction boundary

Date: 2026-10-03

Status: **PHYSICAL PASS — DIAGNOSTIC COMPLETE**

Remote source SHA:
`6404824f0ab328c20e5a3d0cf2c770974eb03db5`

Named-task session:
`4053a0f41bb6`

Exact V3 SHA:
`8469426defd54ce91637f6dfda5eeec59232d75a`

## Baseline

- model: `ollama_chat/qwen3.6:35b-a3b`
- native_tool_calling: True
- full OpenHands system prompt length: 15240 chars
- full prompt SHA-256:
  `015c0664e6654f82b102391fce65e1ce3899919d7fe17c159afe77074a01fd02`

Minimal control:
- structured Terminal tool call: PASS

Full original OpenHands prompt:
- structured tool call: FAIL
- model returned explanatory/plain text instead.

## Length control

A neutral system prompt with exactly 15240 characters produced a structured
Terminal tool call: **PASS**.

Therefore raw character length alone is not sufficient to explain the failure.

## Order controls

Same exact OpenHands sections with the two halves swapped:
- structured tool call: FAIL

Same exact OpenHands sections fully reversed:
- structured tool call: FAIL

Therefore the original section order is not necessary for the failure.

## Prefix boundary

Original-order prefixes:

- 8 sections / 5523 chars: PASS
- 9 sections / 7020 chars: PASS
- 10 sections / 8127 chars: PASS
- 11 sections / 10623 chars: PASS
- 12 sections / 12344 chars: PASS
- 13 sections / 13321 chars: FAIL

The section added at the first failing boundary was:

`EXTERNAL_SERVICES`

But:
- `EXTERNAL_SERVICES` alone: PASS
- prior passing prefix + neutral text replacing `EXTERNAL_SERVICES` at the
  same character length: FAIL

Therefore `EXTERNAL_SERVICES` is not independently the culprit.

## Diagnosis

RUN-030 emitted:

`MIXED_LENGTH_AND_SEMANTIC_INTERACTION`

Best current interpretation:
the stock OpenHands prompt crosses a cumulative instruction-density / semantic
interaction threshold for this local Qwen3.6 tool-calling path. It is not a
simple raw-length limit, not one bad section, and not original section order.

## Architectural consequence

Further microscopic bisecting of the stock 15k OpenHands prompt has diminishing
value for ORION.

Pinned OpenHands `AgentBase` explicitly supports an inline
`system_prompt: str | None`. When supplied, `static_system_message` returns
that text verbatim instead of assembling the built-in default prompt.

This is an appropriate integration boundary for ORION:
- keep OpenHands Agent/Conversation/tool mechanics;
- give the candidate Coding Hand a compact ORION-owned role prompt;
- keep authority, policy, approvals, execution envelope, verification, and
  evidence in ORION rather than duplicating them in a 15k agent prompt.

## Next gate

RUN-031:
full real OpenHands Agent/Conversation loop with the same Qwen3.6 model and
TerminalTool, but with a compact inline ORION-owned system prompt.

Success condition:
- real Agent loop runs;
- real Terminal ActionEvent emitted;
- exact expected command executes in a disposable workspace;
- expected observation received;
- no host/repo authority is granted;
- conversation/tool executors close cleanly.

If RUN-031 passes, return to the FileEditor semantic coding benchmark using the
same compact bounded-agent prompt rather than the stock OpenHands prompt.
