# Side Ideas — AI Self-Dialogue and Claude Code Mods
Date: 2026-10-08
Status: RESEARCH BACKLOG — not approved for implementation
Scope: ORION V3; no changes to frozen Remote V1 or production modules.

## Idea A — Qwen 9B self-dialogue
Run two logically separate conversations against the same locally loaded Qwen 9B model, sequentially to minimize resource usage. Roles: proposer, critic, reviser. Optionally run 2–3 bounded rounds. Maintain separate contexts and log prompts, outputs, tokens, latency and resource usage. Never mistake agreement for independent verification: identical model weights may repeat identical errors.

## Idea B — Evidence-grounded self-improvement
Feed verified test failures and retrieved provenance-backed ORION memories into subsequent attempts. This improves workflow performance without changing model weights. Memory promotion/supersession stays behind existing canonical authority gates; dialogue never writes canonical memory directly.

## Idea C — Multi-model discussion
Use a replaceable conversation coordinator for Qwen, Claude, DeepSeek and other available providers. Explicit role separation, bounded budget and turns, complete transcripts, human approval for actions. ORION owns policy, routing and final acceptance; Hands only executes authorized scoped operations. No autonomous peer approval.

## Idea D — Model routing
Deterministic low-cost routing: simple operations use Qwen 9B + Hands; harder reasoning escalates to cloud providers; high-risk changes demand independent evidence. Compare cost, CPU/GPU load, wall time and task accuracy. No model may raise its own permissions.

## Idea E — Mod and dashboard donor research
Review Claude Code Mods, event interfaces, multi-session communication and Flightdeck-style execution dashboards for reusable patterns. Treat mods as potentially privileged local code; audit permissions, dependencies, licensing and security before reuse. Preserve ORION-owned PC/Android UI and replaceable architecture.

## Benchmark proposal
Same real ORION tasks across:
1. Single-pass Qwen 9B.
2. Qwen proposer→critic→revision (max 2 critique rounds).
3. Qwen self-dialogue + read-only verified memory + independently executed tests.
Measure task success, test pass rate, false confidence, latency, tokens, CPU/GPU, memory and power where available. Compare against baseline and stop if costs outweigh gains.

## Non-negotiable safeguards
- Optional side experiments only; not active roadmap commitments.
- No changes to frozen V1 Remote or currently proven modules.
- Separate module, feature flag, bounded turns, timeout, token/energy budget, global STOP.
- Read-only discussion mode; scoped approval and deterministic verification for execution.
- Canonical memory is provenance-backed and cannot be promoted by model consensus.
- Preserve transcripts and evidence; report PASS/FAIL honestly.
- Do not call this model training or claim that repeated self-talk increases intrinsic intelligence.

## Decision gate
Only propose integration after reproducible benchmark improvements and security review. Otherwise retain as research notes.
