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
- Agent V0 benchmark harness: GITHUB-CODED / PHYSICAL RUN RESTAGED (`Sadusor/Orion@agent/coding-mode-github-loop-v0`, staged SHA `9a6a5fc216b6`)

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
Benchmark routing lesson 2026-10-04: first physical attempt at `23543a9444e5` did NOT execute the benchmark. Remote prioritized the stale single named task `orion-agent-v0-cloud-council` from `REMOTE_TASKS.json`; that task failed because no configured-free cloud reviewer was available. This is not an Agent V0 benchmark failure. `REMOTE_TASKS.json` is now replaced with the single benchmark task `orion-agent-v0-ab-benchmark`, which invokes the committed `CURRENT_TASK.ps1` in the approved exact-SHA worktree.

Benchmark physical attempt 2026-10-04 at `9a6a5fc216b6`: routing was correct and benchmark compile/Ollama readiness passed, but execution stopped before scoring because the task expected model name `qwen3.5-9b-orion` while the physical Ollama catalog reports the intended ORION model as `qwen35-9b-orion:latest`. This is an environment-name mismatch, not an A/B result. Resolver now accepts the ORION aliases and still avoids silently selecting vanilla `qwen3.5:9b`. Restaged at `c6f175738593`.


## Benchmark 2 — Intelligence Architecture Tournament (2026-10-04)

Status: **GITHUB-CODED / FOUNDATION PHYSICAL PROOF STAGED / SCORED CLOUD RUN NOT STARTED**

Implementation:
- repo/branch: `Sadusor/Orion@agent/coding-mode-github-loop-v0`
- staged exact SHA: `3fb9a3cf7ed9458d18959b07874e0cd484e3ab43`
- program: `spikes/coding_mode_github_loop/benchmark_v1/benchmark2.py`

Frozen candidate matrix:
- A = one configured-free cloud model + deterministic Hands;
- B = same cloud model + ORION Agent V0 + bounded Hands;
- C = three-AI council + deterministic Hands;
- D = same three-AI council + ORION Agent V0 + bounded Hands.

Owner-requested council protocol is coded:
- Round 0: three independent proposals from the same frozen context;
- Cross-review Round 1: each AI receives all three Round-0 answers and must identify problems in all proposals, including its own, before revising;
- Cross-review Round 2: each AI receives all three Round-1 answers and repeats adversarial review/revision;
- within-round inputs are frozen so no reviewer gains order advantage;
- ORION uses deterministic visible evidence for arbitration; no LLM judge;
- hidden tests remain evaluator-only and are never fed back;
- scored council runs require exactly three distinct configured-free cloud reviewers and fail closed otherwise.

Synthetic PayDay fixture includes a misleading deprecated implementation, API/UI compatibility requirements, hidden salary edge cases, repository prompt injection, protected files, path-traversal rejection, and a planted fake secret. Only three approved source files are writable.

Local pre-push program self-test: PASS:
- expected broken baseline confirmed;
- reference visible tests PASS;
- reference hidden tests PASS;
- secret removed from model context;
- prompt-injection trap present;
- protected-file and traversal writes rejected;
- council topology = 3 models + 2 cross-review rounds.

The staged Remote task is intentionally foundation-only and makes **zero cloud calls**. It compiles the exact committed program and runs its self-test on the physical target. Scored A/B/C/D execution is a later gate.

Benchmark 1 note: the alias-fixed Agent mechanics run at `c6f175738593` was not yet physically scored before Benchmark 2 program construction was staged; do not treat it as completed evidence.


Benchmark 1 evidence recovery note 2026-10-04: owner reports the alias-fixed physical run at `c6f175738593` showed PASS on the phone, but the GitHub results branch contains no published session/result for that SHA; its head still ends with the earlier `9a6a5fc216b6` pre-score model-name failure. Do not infer A/B winner from the UI PASS alone. A read-only recovery task is staged at `Sadusor/Orion@2e761eb5c61f46ed1db994dc97c7be7daba30f12` to read the already-saved local `agent-v0-ab-latest.json` and publish compact A/B scores/telemetry without rerunning models or using cloud calls.


Benchmark 1 evidence recovery 2026-10-04: read-only recovery session `209973ead547` at SHA `2e761eb5c61f4` FAILED because `%LOCALAPPDATA%\Orion\benchmarks\agent-v0-ab-latest.json` was missing. Combined with the absence of any published session for `c6f175738593`, the prior green phone PASS is not accepted as Benchmark-1 evidence; it is consistent with the known stale-status class. Benchmark 1 is restaged for an actual physical rerun at `Sadusor/Orion@6d0c93f87c1e6878f744679ca241160ac179b272`, with A/B summary fields explicitly emitted into the published session output.


Candidate C preparation staged 2026-10-04:
- exact ORION staging SHA: `85a3f7bf566f1db47480417466191c7047a12001`
- task: `orion-candidate-c-prepare`
- pinned Harness fork: `Sadusor/deepseek-harness@5badb15009ae1756c3afe0ae0cef1faafc290ccc`
- private portable Node pin: `22.19.0`
- private pnpm pin: `11.7.0`
- install scope: `%LOCALAPPDATA%\Orion\benchmarks\candidate-c` plus ORION private toolchain cache
- setup performs exact-SHA fetch, frozen-lockfile install, source build, headless CLI smoke, Ollama/Qwen availability check, and reports Docker/Windows Sandbox/WSL availability.
- setup makes zero model/cloud-AI calls and performs no system-wide install.
- DeepSeek Harness scored Candidate C remains NOT RUN.
- outer sandbox qualification remains PENDING; the prep task only reports available isolation candidates and does not silently enable/install a VM/container product.


Remote task catalog correction 2026-10-04: prior staging repeatedly replaced `REMOTE_TASKS.json` with a single task, hiding earlier GitCheck tasks from the current UI even though their commits remained in Git history. Corrected at `Sadusor/Orion@c6ff50e677de216f0fa82c8dedfa47ffc15ffa25` by restoring a multi-task exact-SHA catalog with dedicated commands for Benchmark 1 A/B, Candidate C DeepSeek Harness preparation, and Benchmark 2 foundation. With multiple tasks, the primary Approve & Run button intentionally does not guess; select the intended item under Available tasks. Existing running exact-SHA sessions remain isolated from this branch update.
