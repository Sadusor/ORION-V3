## CANONICAL ROADMAP POSITION — 2026-10-08 (supersedes conflicting older sections)

**M4 advisory council + Qwen synthesis: PHYSICAL PASS / FROZEN EXPERIMENTAL BASELINE.** Evidence session `e00f23a8b5c0`; exact tested ORION revision `d83b4c91c4254d78fdce2b75ced5155ab9724902`. Three successful Groq cloud reviews → local Qwen 9B nonthinking synthesis → saved advisory, with no execution or approval. [Full frozen checkpoint](checkpoints/2026-10-08-cloud-qwen-baseline-freeze-and-handoff.md).

**CURRENT NEXT MILESTONES (in order):**
1. ORION-native visible Qwen console, orderly medium-sized layout, no orphaned processes; test actual visibility.
2. Read-only saved-advisory import and deterministic schema/provenance/hash validation; bounded typed Proposal adapter with negative tests.
3. Connect only to existing ORION authorization, STOP, verifier, Vault STATE/JOURNAL in dry-run; model text cannot self-authorize or self-certify PASS.
4. Qualify Windows filesystem + network isolation and process-tree STOP physically. Existing network proof inconclusive; full combined gate not run.
5. Approved confined native Hand execution; independently verified evidence; deliberate FAIL → restart → Qwen repair → PASS → Vault persistence.
6. After proven, integrate Work UI/phone, Skills, Memory retrieval and model/provider swaps without modifying frozen components.

**Boundaries:** ORION native Work Hand is under `src/orion_v3/work_loop/`. The separate TheHands project is unrelated and must not be used as an ORION module, code dependency, execution substrate or engineering route. Historical references below document past experiments only. No edits to ORION V1 Remote, frozen Memory or production authority.

**Current exact phase:** after advisory synthesis PASS, **before** ORION-native authority/Hand/verification integration. This is not an end-to-end autonomous loop PASS.

---

# ORION V3 Roadmap

## CURRENT ACTIVE DIRECTION — 2026-10-08 (Decision 0019 supersedes older active-task wording)

**Priority:** prove Autonomous Work Loop V1 using **Qwen + ORION's own Work Hand**: Vault STATE -> Qwen bounded Proposal -> ORION GREEN/YELLOW/RED authorization -> ORION Work Hand -> independent evidence -> Vault STATE/JOURNAL. First prove safe dry-run integration, then physical bounded execution only after confinement qualification, then deliberate FAIL -> restart -> fresh Qwen -> repair -> PASS against the 15-condition acceptance contract.

**Current implementation:** existing `src/orion_v3/work_loop/` modules include coordinator, engine, Vault, authorization, STOP, verifier, simulated Hand and execution Protocol. The coordinator is simulation-only and its evidence is indeterminate; no real Work Hand is enabled. The 8-check Windows combined qualification is NOT RUN; filesystem partial PASS, network INCONCLUSIVE. Real execution DISABLED. GitHub offline coordinator workflow staged at commit `27aef8e7`, test result not yet verified. Separate experimental `engineering_cycle.py` is **not** the current autonomous loop and must not be wired in as an execution authority.

**Next bounded sequence:** (1) run/inspect existing ORION coordinator regression and evidence; (2) audit Qwen's existing ORION model interface and implement the narrowest model-output -> typed Proposal adapter, with offline rejection tests; (3) qualify existing ORION Work Hand sandbox/STOP/commit gates physically without weakening them; (4) prove the original FAIL/restart/repair/PASS milestone; (5) model swap, frozen Memory, Work Chat, Skills, cloud specialists, UI and phone supervision in that order.

**Boundary:** the separate TheHands project is historical remote-UX inspiration, **not** ORION's Hand, runner, dependency, test path or evidence schema. Do not modify or integrate it. Historic descriptions below are retained as records, not current instructions. No parallel authority, Vault, STOP, memory, or app. No changes to frozen modules or real execution authorization.

## ACTIVE ROADMAP UPDATE — 2026-10-08

This update supersedes the immediate sequence under the older Autonomous Work Loop V1 heading below. The earlier milestones remain historical context. Read AI_OPERATOR_BRIEF.md and AGENTS.md first.

**Verified starting point:** most recent checked TheHands result: 57 passed, 3 skipped; real execution disabled. This is not evidence of OS isolation. TheHands is the separate frozen Android-to-Windows engineering remote; only its designated GitCheck test-command interface may be changed for ORION testing.

**A. Authority + Vault transaction gate (current):** retain existing work_loop modules and test contracts. First prove a successful independent read observation cannot promote execution PASS or change STATE/JOURNAL. Next test replay, contradictory executor evidence, STOP during verification, interrupted recovery, and file changes between verification and commit. Extend existing Vault and authorization contracts only where needed. Freeze interfaces after evidence, not threat-model testing.

**B. Donor review and Windows isolation spike (parallel):** inspect source, revision and license of Codex Windows sandbox, agentbox, dsh-sandbox, Windows API examples and existing ORION donors before adapting. Evaluate restricted execution identities, ACLs, AppContainer and disposable sandbox approaches. Job Objects control process lifetime but not filesystem or network access. Physical tests must prove OS denial of unauthorized file access and network connections. No untrusted real execution before isolation proof.

**C. First physical operation:** prefer one approved Git patch in a disposable worktree, bound to exact project/task, source revision, patch bytes, paths, nonce and expiry. Independently verify results and prevent unauthorized canonical commits. Git patch checking alone does not establish isolation, atomicity or rollback. If Git complexity blocks a small first proof, use an append-one-line disposable protocol fixture instead. STOP does not undo physical changes. Crashes never automatically re-execute.

**D. Adversarial qualification gate:** malicious receipts, replay, unrelated side effects, STOP during execution/verification, file replacement, crash/restart and OS-level isolation must pass before adding a second operation. Record exact physical evidence and skipped cases.

**E. Product integration after proof:** integrate Qwen/replacement model proposals, existing frozen Memory read-only, existing PC/Android ORION product shells, connectors, Work Chat, truthful evidence/STOP, deterministic Git/search/repo-map skills, cloud specialists, headless supervision and benchmarks in that order where dependencies permit. Do not rebuild proven UI or TheHands. Preserve the Personal Assistant alongside Work.

**Corrections to the external review:** hard links share file identity; Job Objects do not sandbox network/filesystem; an unanchored journal hash chain does not defeat privileged rewrite; workspace snapshots cannot prove absence of all other effects; verify-to-commit checks alone do not eliminate races against concurrent writers.

**Next bounded action:** test successful read observation non-promotion, then audit Vault commit/STOP seam and donor implementations. Keep execution disabled.

---

## PRIORITY — Autonomous Work Loop V1 (owner-locked 2026-10-07)

This supersedes the previous immediate connectors/UI sequence as the current build priority. Connector/UI work remains valid recorded work and resumes after the autonomous loop foundation is physically proven.

### Locked principles

- ORION owns authority, state transitions, STOP and verification; models never become authority.
- The project folder is the **Vault**. `STATE.md` is its canonical current-state/front-page file.
- Qwen/replacement local models reason and propose; deterministic ORION code authorizes.
- The Work Hand executes only inside a physically proven confined workspace before autonomous writes are enabled.
- Real authenticated evidence determines PASS/FAIL; model claims never do.
- Existing ORION STOP remains authoritative.
- GREEN work proceeds without owner approval; YELLOW waits for the owner; RED/frozen operations are denied before Hands.
- Continuity belongs to ORION/Vault, not to Qwen.
- Round-3 architecture is a direction/principle set, not a component contract. The physical loop may falsify future component hypotheses.
- Build the smallest next proof: physical PASS -> freeze -> extend. Do not pre-build speculative stores/frameworks.

### Milestone 0 — Audit + donor reuse map (CURRENT PRIORITY)

Before coding, inspect the actual ORION-V3, TheHands and donor code and classify each needed capability:

`EXISTS / PARTIAL / MISSING / REUSE`

Audit at minimum: project state/Vault candidates, Qwen invocation, TheHands invocation, evidence, STOP, GREEN/YELLOW/RED checks, frozen-path enforcement, Git, owner-input hook, status/events and workspace confinement.

Donor-first rule: reuse or adapt proven code/patterns before creating new components. Current high-value donor targets are recorded in `docs/AUTONOMOUS_WORK_LOOP_V1_2026-10-07.md` and `docs/DONORS.md`.

### Milestone 1 — Minimal Vault

Create one disposable Work project:

```text
<work-project>/
  STATE.md
  JOURNAL.md
  repo/
```

`STATE.md` contains current project state only: objective, checkpoint/current task, last verified result, next action, blocked state, active project constraints and frozen boundaries. It must not become a shadow Memory.

`JOURNAL.md` is append-only narrative/evidence references. Reusable durable lessons remain candidates for the existing frozen ORION Memory pipeline rather than a second memory system.

### Milestone 2 — Confined Work Hand

Find and physically test the smallest existing confinement mechanism compatible with Windows + TheHands. Audit in this order:

1. existing TheHands confinement/path enforcement;
2. existing donor/runtime confinement that fits the machine and workflow;
3. WSL2 / Windows Sandbox / restricted-user or ACL approaches where appropriate;
4. custom sandbox only if simpler existing mechanisms fail.

Hard gate: autonomous writes do not begin until the Hand is proven unable to write outside its assigned workspace. If confinement is not ready, the loop remains read-only/dry-run.

### Milestone 3 — Tiny autonomous loop

Implement the smallest loop:

`STATE -> Qwen -> ORION check -> Hands -> authenticated evidence -> STATE`

No new Memory, evidence DB, event bus, workflow DSL, Council framework, polished Work UI or notification taxonomy.

The loop must have a hook for a new owner instruction at the start of each cycle so later Work Chat integration does not require redesign.

### Milestone 4 — First physical qualification: FAIL across restart

One qualification path must prove all of the following:

1. owner says `Continue` once;
2. ORION reads the correct STATE;
3. Qwen proposes one bounded task;
4. ORION classifies from concrete properties;
5. GREEN runs without owner approval inside the confined workspace;
6. real evidence authenticates a deliberate FAIL;
7. kill/restart ORION before repair;
8. fresh Qwen receives STATE + authenticated failure with no owner reminder;
9. Qwen proposes a bounded repair;
10. Hands executes; real evidence authenticates PASS;
11. ORION updates STATE and appends JOURNAL;
12. a YELLOW operation waits for owner;
13. a frozen/RED write is denied before Hands;
14. existing ORION STOP halts the loop;
15. the owner can watch the real cycle live from one simple terminal view.

PASS is all-or-nothing. Record separately what this milestone did **not** prove.

### Milestone 5 — Model replacement

Before adding enrichment, replace Qwen with another protocol-compatible local model and prove continuation from the same Vault/evidence. This tests that continuity belongs to ORION, not Qwen.

### Milestone 6 — Existing Memory integration

Add retrieval from the already-frozen ORION Memory as context enrichment only. Vault remains project truth; Memory remains reusable durable knowledge. Do not reopen Memory V1/V1.1.

### Milestone 7 — Separate Work Chat

Reuse ORION's existing chat infrastructure for a project-scoped Work thread. Normal Chat remains independently usable while Work runs. Do not create a permanent file-based second chat system.

### Milestone 8 — Qualified Skills

Add skills only after the core loop is proven. First candidates:

1. repository/code search and compact code map;
2. documentation/research retrieval;
3. Git/project inspection.

Qwen may request; ORION authorizes; Skills return data and never gain authority.

### Milestone 9 — Cloud specialists / Council

Add replaceable cloud specialists only after the local loop is qualified. Start small (Architect + Adversarial) and reuse existing provider infrastructure.

### Milestone 10 — Work observability/UI

Build the real Work UI around observed needs and real backend events. Target surfaces: Work Chat, Activity, Plan, Council, Files/Vault, Evidence. No fake thinking/progress.

### Milestone 11 — Headless + notifications

Same loop with UI attached or detached. Add minimal owner notifications for decisions/blocked/unrecoverable/denied states; routine GREEN work stays quiet.

### Milestone 12 — Phone supervision

Project status, Work Chat, Activity, Council summary, evidence details, decisions, Pause/Resume and global STOP. Phone is supervision, not a mini IDE.

### Milestone 13 — Extended qualification + freeze

Qualify longer continuity, model/provider replacement, YELLOW/RED, confinement attacks, detach/attach, Pause/Resume, STOP and truthful evidence. Then freeze **Autonomous Work Loop V1**.

### Milestone 14 — Use it to help build ORION

Only after qualification, give the frozen loop one small non-protected ORION roadmap task. Self-development never unlocks ORION authority, STOP, evidence verification, frozen Memory, frozen Hands core or the confinement boundary.

### First-milestone claim discipline

A first PASS proves only the bounded claim tested. It does not prove multi-day/multi-project autonomy, general model independence, long-running stability, full skill/council correctness or self-development safety. Each next claim requires its own physical gate.


## Previous priority — Connectors + ORION product UI (preserved / deferred)



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

