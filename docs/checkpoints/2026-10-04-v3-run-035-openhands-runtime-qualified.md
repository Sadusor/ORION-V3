# V3-RUN-035 — compact OpenHands Agent runtime qualified

Date: 2026-10-04

Status: **PHYSICAL PASS**

Remote source SHA:
`ba07c7f82c6cbd9ef4d0962038742f523dffc237`

Session:
`2d9baf57bc54`

Exact V3 SHA:
`82673b5eb993a42158f4537f7cdf93298e8e6b2f`

## Physical evidence

- Remote single-focus/live-refresh probe: PASS
- exact V3 SHA: PASS
- authoring preflight: PASS
- PowerShell syntax preflight: PASS
- V3 regression: **127 passed in 9.81s**
- pinned OpenHands SDK: PASS

OpenHands/Qwen:
- execution status: `ConversationExecutionStatus.FINISHED`
- tool trace: `file_editor, file_editor, terminal`
- FinishTool: not used, advisory only
- real Terminal observation: PASS
- exact changed path: PASS
- candidate Git HEAD unchanged: PASS
- exact expected source: PASS
- independent deterministic functional check: PASS
- exact candidate raw SHA-256 captured

ORION boundary:
- exact candidate bytes frozen as FILE REPLACE: PASS
- candidate execution authority: NONE
- review/decision/action chain: PASS
- WorkPackage execution envelope: PASS
- deterministic verifier: PASS
- source repository unchanged: PASS
- execution cleanup: PASS

Final marker:
`OPENHANDS_AGENT_RUNTIME_QUALIFIED> PASS`

## Decision

OpenHands Agent is now qualified as **one optional runtime candidate** inside
ORION when:
- ORION supplies the compact prompt;
- ORION controls which tools are exposed;
- ORION retains authority/evidence/verification;
- the Agent operates in a disposable workspace.

Stop isolated OpenHands-agent benchmarking.

Next benchmark target:
**ORION Operator Benchmark**, where the same Qwen operator sees a normalized
mixed toolbox from OpenHands, OpenJarvis and ORION-native capabilities.

The separately discovered PATCH replay/raw-byte verifier portability issue
remains an ORION-core task and must not be conflated with Agent quality.
