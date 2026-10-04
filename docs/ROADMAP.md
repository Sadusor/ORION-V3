# ORION V3 Roadmap

All milestones are gated by physical evidence.

## Immediate owner-approved build — ORION Agent V0

Build the smallest ORION-native bounded agent loop before making any Agent V1 decision.

Sequence:

1. deterministic Agent V0 foundation gate;
2. Qwen structured-proposal adapter;
3. bounded test/build Hand;
4. reusable benchmark fixture;
5. A/B/C benchmark:
   - A: Qwen + deterministic Hands;
   - B: same Qwen + ORION Agent V0 + same Hands;
   - C: same Qwen + DeepSeek Harness under ORION isolation;
6. owner + assistant review results and brainstorm the next architecture.

Implementation status as of 2026-10-04:
- benchmark harness is coded but not physically run;
- A/B host-safe runners are ready behind the foundation gate;
- C runner is coded but fail-closed unless an outer disposable sandbox is explicitly present;
- resource telemetry captures Windows CPU/RAM and NVIDIA GPU/VRAM/power;
- the frozen fixture includes visible/hidden correctness tests and a harmless prompt-injection trap.

Keep future seams for Memory, Skills, Security Advisor, Sandbox and escalation, but do not implement those features into V0 unless the benchmark proves they are needed.

Google Mantis is the primary secure-coding/sandbox/verification donor. ButterClaw is the primary runtime-policy/process-monitor donor. Google mcp-security, Athena Investigation MCP and AgenticAnomaly remain optional security-tool/contract/red-team donors.

Canonical decision: `docs/decisions/0014-build-orion-native-agent-v0.md`.

Full donor analysis: `docs/reference/2026-10-04-agent-security-donor-analysis.md`.

## V3.0A — Donor contract probe — PASS
Physical PASS on 2026-10-04. Hostile scope rejection, exact frozen-plan hash approval, post-approval mutation denial, deterministic Hand receipt, exact artifact verification, replay protection, and no-network/model execution all passed. Evidence: `docs/evidence/2026-10-04-donor-contract-probe-pass.md`.


## V3.0 — Foundation Gate 1
Prove OpenJarvis can be the generic substrate without becoming an authority peer.
One operation: `filesystem.search`.

Exit criteria:
- ORION lease required;
- Jarvis fail-closed;
- native-agent/direct-tool bypass blocked;
- trusted scope cannot be model-overridden;
- evidence normalized by ORION;
- real Stop semantics understood;
- old ORION Remote untouched.

## V3.1 — Deterministic Hand migration
Adapt proven mechanics from old ORION behind stable names:
- filesystem.search
- filesystem.list
- filesystem.reveal
- project.publish

## V3.2 — Provider / governor integration
Use OpenJarvis engine/model registries where they survive policy tests.
Qwen 3.5 9B remains the leading lightweight governor candidate.
WORKSHOP remains a donor for provider discovery, roles, health, fallback and safe serialization.

## V3.2A — Phone UI alpha
After Proof V2 stabilizes the natural-language -> ORION contract boundary, build the new V3 phone/UI alpha before the broad Hands tournament. Target one interaction for low-risk requests, at most one confirmation for bounded writes, explicit confirmation for high-risk actions, auto-refresh, global STOP and inline evidence. Legacy Remote remains frozen fallback.


## V3.2B — Multi-lane local assistants
Keep the everyday Personal Assistant available while one or more project workflows are active.

Benchmark:
- one-model / two-context Personal + Project split;
- two-model split when specialization appears useful;
- concurrent latency, CPU, GPU, VRAM/RAM and task interference;
- per-lane state isolation, STOP/pause and provenance.

Role assignment remains benchmark-driven. Do not assume a second model is necessary; do not assume it is too expensive either.


## V3.3 — Browser Hand tournament
Control: Aegis containment evidence.
Challengers: PinchTab, CUA browser mode, specialist extraction donors where useful.

## V3.4 — Memory
Canonical Memory remains ORION-owned.
Primary internal donor: KnowledgeOS.
Challengers: agentmemory, TencentDB-Agent-Memory, OpenViking, memanto.

Personal-file learning begins here as retrieval, not weight training:
- approved project/file/browser/assistant exports;
- text + image/PDF/screenshot ingestion;
- provenance, hashes, scope and supersession;
- retrieval into replaceable local models;
- no automatic whole-PC scraping.

## V3.4A — Vision + personal-file benchmark
Physically qualify the selected Personal Assistant candidate on the exact local runtime for:
- screenshots;
- PDF pages / scanned material;
- visual grounding;
- provenance back to source;
- latency and VRAM impact.

Qwen remains a leading candidate, but vision is not considered proven until the installed package passes this gate.

## V3.5 — Computer Hand
Primary substrate candidate: CUA Driver.
Reasoning/perception: UI-TARS, UI-TARS Desktop, Qwen vision.
Human takeover/secrets donor: OpenBot.

## V3.6 — Coding Hands
Use adapters, not another coding agent.
Candidates: software-agent-sdk/OpenHands, Claude Code, ACP-compatible runtimes.

## V3.6A — Full-agent substrate tournament
Full agents remain fallback execution substrates, never ORION authority.

First-priority candidate: **DeepSeek Harness** (pinned review SHA `5badb15009ae1756c3afe0ae0cef1faafc290ccc`).

Compare against Qwen 9B + deterministic Hands and other qualified agent substrates on:
- task success and latency;
- CPU/GPU/VRAM/RAM;
- tool-call count and token cost;
- hostile scope widening;
- exact-approval binding;
- network denial;
- background-job/subagent containment;
- STOP/process-tree cleanup;
- evidence quality.

Initial DeepSeek Harness qualification should use its headless JSON runner, a disposable workspace, ORION monotonic tool guard, restricted tool set, bounded step/time budgets, and local/self-hosted model routing where physically proven.

## V3.7 — Android / device
Primary donor: Artemis.
Transport/client donors: KIRA and Orion-Copilot patterns.

## V3.8 — Connectors / workflows
Primary commodity integration donor: n8n.

## V3.9 — Learning / recipes
Adapt OpenJarvis SkillDiscovery only as a candidate generator.
Learning never grants authority.

## V3.9A — Optional personalized model adapter
After enough high-quality owner-approved traces exist, compare:
- memory/retrieval only;
- memory + detachable LoRA/QLoRA adapter.

Train only on curated manifests of corrected interpretations, accepted plans, terminology, workflows and selected visual examples where supported. Keep the base model immutable, version adapters, preserve provenance, exclude secrets by default, and require pre/post ORION regression gates before promotion.

## V3.10 — Voice / channels / final UI
Candidates: OpenJarvis desktop/channel infrastructure, whisper.cpp, EchoFetch, openWakeWord, Kokoro.

## V3.11 — Remote parity
Only after PC + phone parity is physically proven may legacy Remote be considered for retirement.