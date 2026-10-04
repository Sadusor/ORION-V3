# ORION V3 Status

Updated: 2026-10-04

## Stage

ORION Agent V0 bounded-loop foundation build.

ORION-V3 is a completely separate repository from the proven ORION implementation.

## Current claims

- Evidence Pack concurrency repair: PASS (`aee352d7f379`)
- Local Model Tournament Reasoning V2: PASS (`2e43a124646f`) — Qwen 3.5 9B ORION won FAST and THINKING
- E2E Authority Proof V1: PASS (prepare `71c7f7cbccb3`, execute `9c623d9e5be6`)
- Donor contract probe: PASS (session `92c002cdf162`)
- architecture: DOCUMENTED
- OpenJarvis substrate: CANDIDATE, not adopted
- Authority Boundary V0: DRAFT
- Gate-1 runtime: NOT TESTED
- old ORION Remote: frozen external fallback; untouched
- Agent V0 benchmark harness: GITHUB-CODED / NOT PHYSICALLY RUN (`Sadusor/Orion@agent/coding-mode-github-loop-v0`, head `ac0f68270fe7`)

## Pinned OpenJarvis donor

`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

## Current bounded task

**Physically qualify the first ORION Agent V0 foundation before adding Qwen to the loop.**

Owner approved building a small ORION-native agent with explicit future seams, then benchmarking it before deciding the next architecture.

Current implementation in `Sadusor/Orion` is GITHUB-CODED / UNVERIFIED and contains:

- strict structured proposals;
- one-action-at-a-time loop;
- frozen task-scoped Hand registry;
- task-state binding;
- idempotency guard;
- hash-chained Journal;
- bounded observations;
- model/tool/time/rejection budgets;
- external Stop hook;
- reserved interfaces for later Memory, Skills, Security Advisor, Sandbox and escalation.

The first target-machine gate is deterministic and intentionally excludes Qwen/cloud/network. After it passes, run the now-coded local Qwen JSON adapter and bounded coding/test capability, then execute the frozen benchmark.

Benchmark implementation now includes:
- A: one-shot same-Qwen deterministic control with a bounded patch manifest;
- B: same Qwen through ORION Agent V0 with bounded list/read/write/test Hands;
- C: same Qwen through DeepSeek Harness headless JSON using its OpenAI-compatible self-hosted route; C refuses normal-host execution and requires the outer disposable sandbox;
- frozen multi-file persistence/configuration fixture with visible and hidden tests;
- harmless repository prompt-injection trap;
- Windows CPU/RAM plus NVIDIA GPU/VRAM/power sampling;
- one warm-up plus three scored A/B repetitions with rotated order.


A/B/C:

- A: Qwen + deterministic Hands;
- B: same Qwen + ORION Agent V0 + same Hands;
- C: same Qwen + DeepSeek Harness under ORION isolation.

Google Mantis is now the primary secure-coding/sandbox/verification donor; ButterClaw is the primary runtime-policy/process-monitor donor.

Canonical decision: `docs/decisions/0014-build-orion-native-agent-v0.md`.

Detailed donor record: `docs/reference/2026-10-04-agent-security-donor-analysis.md`.

## Newly documented owner direction

- Multi-lane assistant architecture: Personal/Desktop Assistant remains available while project/coding workflows run.
- One physical model with isolated contexts or two different local models are both allowed; role assignment will be benchmark-driven.
- Add a post-tournament concurrency benchmark instead of assuming small local models are a resource bottleneck.
- Personal learning starts with ORION-owned retrieval over approved files, downloads, exports, screenshots and project data.
- Optional later LoRA/QLoRA personalization uses curated owner-approved examples; base model remains immutable and adapters remain replaceable.
- Vision is a first-class Personal Assistant requirement, but must be physically proven on the exact installed model/runtime.
- No automatic whole-PC scraping or automatic training from credentials/private data.

## Gate-1 attacks

1. no lease;
2. forged lease;
3. expired lease;
4. wrong operation or scope;
5. native Jarvis agent direct invocation;
6. side-effect tool outside ORION profile;
7. Jarvis policy accidentally open-by-default;
8. Jarvis capability widening while ORION denies;
9. model attempts to inject trusted roots;
10. blocking operation plus Stop;
11. donor telemetry mistaken for canonical state.

## Protected fallback

- repo: `Sadusor/Orion`
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`