# ORION V3 Roadmap

All milestones are gated by physical evidence.

## Immediate owner-approved build — Connectors + ORION product UI

Owner-locked sequence as of 2026-10-05:

1. use `Sadusor/TheHands-` as the primary manual engineering Remote;
2. keep the older Remote frozen as emergency fallback only;
3. build the connector layer/seams;
4. build the separate STRATA/Claude-inspired ORION UI for PC and phone;
5. connect those product UIs to ORION/backend/connectors only after the surfaces are ready;
6. physically qualify each connected capability without modifying the frozen fallback.

Do **not** rebuild engineering-Remote parity inside the ORION product UI. The product UI and TheHands have different jobs and may coexist.

The Agent V0 / DeepSeek Harness benchmark work remains valid recorded evidence and may continue as a separate architecture benchmark lane; it is no longer the immediate product-build sequence.

Canonical current decision: `docs/decisions/0016-thehands-primary-engineering-remote.md`.
Decision 0015 remains historical/current only for the product-UI separation and fallback freeze.

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

## V3.2A — Product UI foundation

Build the new ORION product UI as two coordinated surfaces:
- PC UI;
- phone UI.

Both follow the STRATA/Claude design direction and consume ORION-owned state. Neither is a rebuild of V1 Remote. V1 remains frozen and may only be used as the proven external development/control path while these surfaces are built.

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

Current memory sequence after adversarial review:
1. Conversation Recall V1 — frozen PASS.
2. Memory Candidate Queue V1 — frozen PASS.
3. Canonical Memory Review + Promotion V1 — frozen physical PASS.
4. Canonical Memory Retrieval Foundation V1 — exact scope, retrieval-time admission,
   append-only supersession representation, explicit budget/fusion contract.
5. Canonical Memory Retrieval integration — owner-approved durable context and
   Conversation Recall remain separate labeled blocks; conflicts never silently resolve.
6. Automatic Candidate Detection — candidates only, never automatic promotion.
7. Consolidation / L0-L1-L2 / duplicate handling.
8. Hybrid/vector/graph evaluation only if a retrieval benchmark proves BM25 insufficient.

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
Current product priority. Build connector contracts/seams before wiring the new PC/phone UI. Primary commodity integration donor: n8n. Connector implementations remain replaceable and do not gain ORION authority.

## V3.9 — Learning / recipes
Adapt OpenJarvis SkillDiscovery only as a candidate generator.
Learning never grants authority.

## V3.9A — Optional personalized model adapter
After enough high-quality owner-approved traces exist, compare:
- memory/retrieval only;
- memory + detachable LoRA/QLoRA adapter.

**Primary training/post-training donor candidate: Soup.** Evaluate it as a convenience/training substrate only; it never owns ORION memory, authority or runtime truth. Its low-VRAM layer-streaming path is promising but remains NOT TESTED by ORION and must be pinned/re-benchmarked before use.

First adapter gate:
- start with roughly 200-500 highly reviewed, provenance-backed behavior examples rather than a noisy bulk dump;
- train behavior/routing patterns, not canonical ORION memory;
- compare a small base model, the same model + adapter, and the current Qwen 3.5 9B governor baseline;
- measure intent/tool accuracy, unsafe false negatives, unnecessary approvals, scope/STOP compliance, hallucinated-success rate, latency, CPU/GPU/VRAM/RAM and power where practical;
- require held-out traces and full pre/post ORION regression gates before promotion.

Train only on curated manifests of corrected interpretations, accepted plans, terminology, workflows and selected visual examples where supported. Keep the base model immutable, version adapters, preserve provenance, exclude secrets by default, and require pre/post ORION regression gates before promotion.

Security note: Soup Wall is a separate donor for deterministic shadow-first action filtering, replay/policy regression and MCP/subagent/egress controls. Any such layer may only **narrow** ORION authorization; it may never grant authority or replace ORION approval/STOP/evidence semantics.

Detailed review: `docs/reference/2026-10-05-soup-training-and-soup-wall-donor-review.md`.

## V3.10 — Voice / channels / final UI
Candidates: OpenJarvis desktop/channel infrastructure, whisper.cpp, EchoFetch, openWakeWord, Kokoro.

The final PC and phone interfaces are ORION product surfaces, not Remote V2.

## V3.11 — V1 Remote protection
V1 Remote remains frozen and outside the product-UI build lane. It continues as the dedicated engineering Remote even after the ORION product UI is launched. No parity migration or retirement milestone is active. Any future change to that rule requires a new explicit owner directive.

## V3.2B — Intelligence Architecture Tournament

After the Agent mechanics gate, compare reasoning tier × execution tier using the frozen synthetic PayDay fixture:

| Candidate | Reasoning | Execution |
|---|---|---|
| A | one configured-free cloud model | deterministic Hands |
| B | same cloud model | ORION Agent V0 |
| C | three-model adversarial council | deterministic Hands |
| D | same council | ORION Agent V0 |

Council V0 is fixed at three models: independent first proposals followed by exactly two frozen cross-review rounds where every model sees all previous-round answers and objections. ORION, not an LLM judge, arbitrates using visible deterministic evidence. Hidden evaluator tests are never feedback.

Run one unscored warm-up and three scored repetitions initially; only extend close finalists. Safety violations disqualify before correctness/efficiency comparisons.
