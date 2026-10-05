# ORION V3 Donor Code Audit — 2026-10-05

Status: **READ-ONLY CODE AUDIT / TOMORROW HANDOFF**  
Scope: ORION-V3 architecture + owner forks/donors.  
Runtime/product code changed by this audit: **NONE**.

## Purpose

This document records what was actually inspected in ORION V3 and the donor forks before the next product phase:

> connect the accepted STRATA PC/phone UI to real ORION functions one bounded capability at a time.

It is intentionally code-oriented. A repository appearing here does **not** make it ORION authority and does **not** authorize adoption.

The permanent authority hierarchy remains:

```text
OWNER
  ↓
ORION AUTHORITY
  ↓
reasoning substrate / providers / donors
  ↓
qualified deterministic Hands / adapters
  ↓
evidence
  ↓
ORION verifier + canonical Task/Event/Memory truth
```

Models reason. Donors provide replaceable mechanisms. ORION owns permissions, scope, approvals, STOP, evidence, canonical memory and promotion into protected state.

---

## 1. Current ORION-V3 code reality

At the time of this audit, ORION-V3's production Python backend is deliberately small:

- `src/orion_v3/product_server.py`
- `src/orion_v3/__init__.py`

The accepted STRATA product UI is under `ui/strata/`.
The native PC shell is under `desktop/ORION.UI/`.
The Android thin client is under `android/`.
Windows lifecycle/build/smoke scripts are under `scripts/`.

The product backend is **Phase A**:
- real health;
- real PC/phone pairing;
- real authenticated status;
- truthful project/provider/reviewer/memory-preview surfaces;
- unsupported action routes explicitly refuse rather than fake success.

The action route allowlist already exists in `ui/strata/bridge/routes.js`; most action routes are intentionally not connected yet. That is tomorrow's integration boundary.

The accepted product direction remains:
- native `ORION.exe` = PC console;
- Android app = thin paired client to the same PC authority/runtime;
- no browser dashboard as the product;
- TheHands remains a separate frozen engineering Remote;
- no Remote-parity rebuild inside ORION product UI.

---

## 2. OpenJarvis — substrate / registry / engine donor

Fork: `Sadusor/OpenJarvis`  
Pinned V3 candidate audited at: `309a4f1044ccfb2032264832a31fef2f1d314586`

### Actual useful code inspected

- `rust/crates/openjarvis-core/src/registry.rs`
  - thread-safe typed registry using `RwLock<HashMap<String, Arc<T>>>`;
  - registries for model, engine, agent, tool, memory, routing policy, benchmark, channel, learning and skill.
- `rust/crates/openjarvis-security/src/capabilities.rs`
  - capability vocabulary such as `file:read`, `file:write`, `network:fetch`, `code:execute`, `memory:read/write`, `channel:send`, `tool:invoke`, `schedule:create`, `system:admin`;
  - explicit grant/deny with resource patterns.
- `rust/crates/openjarvis-tools/src/executor.rs`
  - central tool dispatch;
  - capability check;
  - taint check;
  - tool-call start/end/timeout events;
  - normalized tool result.
- `rust/crates/openjarvis-learning/src/skill_discovery.rs`
  - mines recurring tool sequences from traces.
- engine/discovery code:
  - Ollama and other replaceable engines;
  - health/model discovery;
  - OpenAI-compatible engine abstraction.
- channel architecture:
  - transport-neutral channel interface;
  - registry discovery;
  - lifecycle/status/send/receive hooks;
  - EventBus integration.

### Critical ORION caveats

OpenJarvis' capability policy supports `default_deny=true`, but its default constructor is **default allow**. ORION-governed paths must therefore instantiate/configure it fail-closed.

The tool executor's timeout is not equivalent to ORION STOP. A timeout observation after synchronous execution is not proof that the underlying work was cancelled.

EventBus events are useful telemetry but never canonical ORION Task/Event truth.

Skill discovery is a **candidate generator only**. A discovered skill does not become trusted or executable until ORION qualifies it.

### Disposition

**PRIMARY substrate donor, not authority.**

Borrow:
- registries;
- engine discovery;
- replaceable tool/skill interfaces;
- narrow capability vocabulary;
- event adapters.

Keep above it:
- ORION Action Leases;
- project/scope binding;
- exact approval/hash binding;
- STOP;
- evidence normalization;
- Memory promotion.

---

## 3. Jev Harness + OpenMuse — proposal/evidence/approval semantics

Forks:
- `Sadusor/jev-harness`
- `Sadusor/openmuse`

### Jev Harness actual code/topics found

- proposal-review fixtures for:
  - injection attempts;
  - missing evidence;
  - off-scope edits;
  - ambiguous proposals;
  - clean bounded edits.
- provenance-rich routing/evaluation runs.
- proposal-review tests and evidence replay tests.

### OpenMuse actual code inspected

- `apps/server/src/jev/service.ts`
  - generation/revision tracking;
  - compare-and-swap updates;
  - stale/superseded choices rejected;
  - one visible selection cannot silently become another;
  - source/evidence references hashed.
- `apps/server/src/jev/tools.ts`
  - strict schemas;
  - comparisons must be grounded in source text already read by the server;
  - user-choice presentation itself performs no external action.
- `apps/server/src/actions.ts`
  - action proposals;
  - idempotency keys / SHA-based stable operation identity;
  - preparation/execution separation.
- computer/browser/task surfaces:
  - persistent browser;
  - optional isolated workspace;
  - task progress;
  - pause/resume/cancel/retry;
  - saved command receipts;
  - human takeover.

### ORION pattern already accepted by physical donor-contract probe

- approval binds to an exact frozen proposal hash;
- stale/changed proposal cannot reuse old approval;
- operation IDs/idempotency prevent blind replay;
- uncertain external effects remain uncertain instead of being retried as if nothing happened;
- persisted receipts;
- bounded execution output/time;
- evidence must exist before grounded comparisons/claims.

### Disposition

**HIGH priority contract donor.**  
Do not import OpenMuse/CopilotKit as authority. Reuse the concurrency, frozen-proposal, receipt and grounded-evidence patterns.

---

## 4. CLI-Anything — deterministic Hands

Fork: `Sadusor/CLI-Anything`

### Actual code shape

The repository repeatedly implements GUI/software harnesses in the shape:

```text
<software>/agent-harness/cli_anything/<tool>/
  core/
  *_cli.py
  session/state
  backend adapter
  tests/
  SKILL.md
```

Examples inspected in the tree include QGIS, 3MF, AdGuard Home and many others.

### Strong reusable patterns

- one logical operation per command;
- real backend invocation rather than fake reimplementation;
- JSON/machine-readable output plus human output;
- inspect before mutate;
- session/state;
- explicit return codes;
- final artifact verification;
- preview/live-preview/trajectory loops;
- immutable preview bundles;
- `manifest.json`, compact `summary.json`, append-only `trajectory.json`;
- E2E verification of the real artifact, not just process exit.

### Disposition

**HIGH priority Hand-shape donor.**  
Ideal model: ORION authorizes one typed operation; deterministic adapter executes; receipt/evidence returns to ORION.

---

## 5. Octop — policy/plugin/ACP/remote patterns

Fork: `Sadusor/Octop`

### Actual relevant code found

- HITL approval card and policy picker;
- security/tool-management UI and APIs;
- plugin market/registry;
- ACP adapters/surfaces;
- browser workspace and stream controls;
- remote browser state/control hooks;
- expert/tool panels.

### Useful

- deny/allow tool controls;
- command guards;
- filesystem/security policy patterns;
- plugins/skills;
- ACP integration;
- remote/browser operator UX.

### Reject as authority

Do not import:
- agent-team autonomy as ORION state;
- in-memory agent messages as canonical Task truth;
- donor-side approval as sufficient authorization.

### Disposition

**MEDIUM/HIGH security + plugin + ACP donor.**

---

## 6. KnowledgeOS — primary internal Memory donor

Fork: `Sadusor/KnowledgeOS`

### Actual code inspected

- `app/core/evidence.py`
  - immutable `Evidence`;
  - evidence type/source/confidence/origin/metadata;
  - explicit rule: evidence is factual observation; interpretation is separate.
- `app/core/evidence_repository.py`
  - persistence abstraction for evidence.
- `app/services/search_trace.py`
  - immutable per-candidate trace;
  - keyword/semantic/hybrid/rerank scores;
  - diversity/backfill/final-rank visibility.
- `app/services/memory_retrieval_service.py`
  - deterministic structured MemoryRequest execution;
  - bounded candidate expansion;
  - filters for types/tags/time ranges/capture time;
  - deterministic ALL/ANY matching and ordering.
- tree also contains:
  - image metadata collector;
  - deterministic memory interpreter;
  - memory pipeline;
  - retrieval attribution evaluation;
  - counterfactual retrieval evaluation.

### Disposition

**PRIMARY internal memory/retrieval donor.**

Best fit for:
- provenance-backed retrieval;
- traceable ranking;
- image/file metadata;
- deterministic request/filter layer.

Canonical durable Memory still belongs to ORION.

---

## 7. agentmemory — consolidation / hybrid / temporal challenger

Fork: `Sadusor/agentmemory`

Actual code found:
- `src/functions/consolidate.ts`;
- consolidation pipeline;
- graph import/retrieval;
- temporal graph;
- working memory;
- hybrid search;
- project-scope and consolidation tests.

### Disposition

**MEMORY challenger/donor**, especially:
- consolidation;
- hybrid lexical/vector/graph retrieval;
- temporal relationships;
- working-memory mechanics.

Do not let consolidation silently overwrite provenance or canonical facts.

---

## 8. TencentDB-Agent-Memory — scalable memory/knowledge backend donor

Fork: `Sadusor/TencentDB-Agent-Memory`

Actual structure:
- `MemoryCore/`;
- `MemoryKnowledge/`;
- `MemoryPanel/`;
- `MemoryProxy/`;
- capture/recall hooks;
- memory/conversation search tools;
- migration/export tooling;
- local Mongo/SQLite/vector benchmarks;
- plugin adapters.

### Disposition

**Backend/scale challenger.**  
Useful for large memory corpora and knowledge/code organization. Not canonical ORION schema or trust authority.

---

## 9. OpenViking — hierarchical memory/context reference

Fork: `Sadusor/OpenViking`

Actual code/tree includes:
- memory plugins;
- experience-memory skills;
- memory organization benchmarks;
- long-memory evaluations;
- retrieval/BM25 benchmarks;
- trajectory-to-memory tooling;
- context/resource organization.

### Disposition

**REFERENCE + benchmark donor.**  
Use L0/L1/L2-style hierarchical context ideas where they improve retrieval, but keep ORION provenance/authority model and verify license/dependency surface before code reuse.

---

## 10. memanto / codebase-memory-mcp / Graft / Aider

### memanto — `Sadusor/memanto`

Found:
- adversarial memory resilience benchmark;
- temporal memory showdown;
- framework adapters/integrations.

Use mainly for **memory falsification and temporal-evaluation ideas**.

### codebase-memory-mcp — `Sadusor/codebase-memory-mcp`

Found:
- code graph/index product;
- graph UI;
- project/graph APIs;
- index resource-limit documentation.

Use as a **code-memory/graph challenger**, not canonical memory.

### Graft — `Sadusor/Graft`

Actual code:
- multi-language graph extraction;
- incremental refresh;
- LSP enrichment;
- graph relations/scopes;
- context build/check;
- repository context files.

Use for **Project Coordinator code context**.

### Aider — `Sadusor/aider`

Actual:
- `aider/repomap.py`;
- repo/context handling;
- repo-map tests.

Use compact repo-map ideas for **bounded code context**, not editing authority.

---

## 11. CUA — computer-use driver and benchmark

Fork: `Sadusor/cua`

Actual monorepo surfaces include:
- `cua-driver`;
- typed SDK/MCP compatibility;
- cross-platform computer operation;
- browser/native app control;
- screenshots/streaming;
- Spaces;
- `cua-bench`;
- trajectory/evaluation tooling;
- release/preflight/security tests.

### Disposition

**PRIMARY Computer Hand substrate candidate.**

ORION must wrap it with:
- Action Lease;
- exact target/scope;
- bounded actions;
- evidence/verification;
- Stop targeting the actual owned run;
- human-takeover ownership when applicable.

---

## 12. Artemis — Android/device Hand

Fork: `Sadusor/artemis`

Actual code found:
- Android ADB driver;
- hierarchy/input/recorder;
- device controller;
- action manifest/spec/types/executor;
- ADB actuator;
- device lock/pool;
- screenshots/history;
- planner/operator/checker/explorer modules;
- pre-execution safety validator;
- physical-action and remote-ADB tests.

### Disposition

**PRIMARY Android/device donor.**

Likely reuse:
- deterministic device/action layer;
- screen/hierarchy capture;
- device locks;
- action manifest;
- verification helpers.

Do **not** give Artemis Planner/Operator ORION authority.

---

## 13. PinchTab — browser-control challenger

Fork: `Sadusor/pinchtab`

Actual code:
- navigation/action CLI;
- DOM/a11y inspection;
- recording;
- browser state/storage;
- network route controls;
- bridge/daemon;
- MCP;
- extensive security tests/configuration.

Security posture is intentionally local-first and treats remote operator APIs as privileged.

### Disposition

**STRONG browser Hand challenger.**

Best ideas:
- semantic/a11y references;
- persistent browser runtime;
- compact DOM/state inspection;
- explicit network/security configuration.

ORION still owns domain grants, credential policy and action authorization.

---

## 14. OpenBot — fail-closed gateway + human takeover + secrets

Fork: `Sadusor/OpenBot`

Actual relevant code:
- `agent-computer/src/authorisation.ts`;
- `control.ts`;
- `egress.ts`;
- live page/viewer/shell/workspace;
- server computer `gateway.ts`;
- `policy.ts` / policy store / dry-run;
- snapshot store;
- supervisor;
- credentials;
- audit.

Strong documented/code patterns:
- every computer/file/MCP action goes through one gateway;
- decision/audit recorded before action;
- missing/broken policy fails closed;
- human “take the wheel” control ownership;
- agent actions refused while human owns control;
- secret value never enters transcript;
- encrypted credentials;
- governed MCP;
- skills are instructions, not capabilities.

### Disposition

**HIGH priority security/operator donor** for:
- human takeover;
- secret entry;
- audit-before-act;
- fail-closed gateway;
- governed connector/tool grants.

---

## 15. OpenHands + software-agent-sdk — coding executor donors

Forks:
- `Sadusor/OpenHands`
- `Sadusor/software-agent-sdk`

### OpenHands code surface found

- agent-server runtime/sandbox APIs;
- conversation sessions;
- Git/file service;
- tool visualizers for Bash/file editor/search/task;
- profiles/models;
- sandbox service;
- file uploads/workspace browsing.

### software-agent-sdk code surface found

- generated/open API contracts;
- runtime transport;
- file/tool/sub-agent clients;
- workspace/session tests;
- examples for custom tools, planning, delegation.

### Disposition

Use as **coding Hands/adapters**, preferably through the smallest stable runtime/API seam.  
They never promote their own changes to protected project state.

---

## 16. Claude Code + ACP + Python SDK

Forks:
- `Sadusor/claude-code`
- `Sadusor/agent-client-protocol`
- `Sadusor/python-sdk`

### Actual useful code

Claude Code:
- hooks and command validation examples;
- project instruction / AGENTS-style integration.

ACP:
- versioned protocol schema;
- sessions;
- tool calls;
- terminal;
- file system;
- cancellation;
- plans;
- elicitation;
- authentication;
- extensibility.

Python SDK:
- agent/client connections and routers;
- HTTP and WebSocket clients;
- session state;
- tool-call helpers;
- protocol negotiation tests.

### Disposition

**Interchange layer for external coding agents**, not ORION authority.  
ACP is especially valuable as a replaceable coding-agent transport so ORION does not hard-wire one coding vendor.

---

## 17. OpenSandbox — disposable coding boundary

Fork: `Sadusor/OpenSandbox`

Actual code/tree:
- sandbox create/list/kill/exec;
- file operations;
- snapshots;
- credential vault;
- network egress;
- diagnostics;
- SDK/server;
- process-session and runtime update tests.

### Disposition

**STRONG sandbox donor** for V3 coding mode:
- disposable workspace;
- resource/process boundary;
- controlled egress;
- file transfer;
- snapshots.

ORION remains owner of sandbox lifecycle, network policy and promotion.

---

## 18. DeepSeek Harness — full-agent benchmark candidate

Fork: `Sadusor/deepseek-harness`

The tree contains extensive runtime work around:
- tool schemas;
- long-running tools;
- scope/runtime design;
- subprocess seams;
- Windows filesystem/process primitives;
- durable JSONL/session restore;
- headless direct-core entry points;
- canonical tool-output contracts.

### Disposition

**Benchmark/optional agent substrate**, not default ORION coding path.  
Use only inside ORION-owned sandbox/lease and compare against cheaper Qwen + deterministic Hands.

---

## 19. UI-TARS / UI-TARS Desktop — GUI grounding

Forks:
- `Sadusor/UI-TARS`
- `Sadusor/UI-TARS-desktop`

Actual code found:
- action parser;
- desktop operator/prompts;
- browser/screen IPC;
- screen recording;
- remote operators/proxy;
- computer-use UI.

### Disposition

**Vision/grounding donor/benchmark.**  
Use to interpret UI state or propose actions; never let grounding results become permission.

---

## 20. KIRA + Orion-Copilot — phone/device/voice donors

### KIRA — `Sadusor/kira`

Actual code found:
- `ActionControlLease.kt`;
- `UiControlLease.kt`;
- endpoint routing;
- PC vision codec;
- UI grounding;
- screen observation/capture;
- screen verification;
- Android accessibility action gateway;
- Hands controller;
- learned routines;
- voice coordinator;
- STT session ownership;
- direct mic lease;
- TTS/STT engines;
- phone-local runtime.

This is particularly valuable for:
- phone lease semantics;
- voice/mic ownership;
- screen evidence;
- thin-client routing.

### Orion-Copilot — `Sadusor/Orion-Copilot`

Contains the older Android/remote project documentation and app patterns.

### Disposition

Use transport/client/lease lessons.  
PC ORION remains authority; phone is never independent authority.

---

## 21. n8n — workflow/connector donor

Fork: `Sadusor/n8n`

Actual tree includes:
- workflow engine;
- OAuth/node integrations;
- credential/secrets controls;
- workflow safety;
- code-execution/sandbox security rules.

### Disposition

**Commodity connector/workflow runtime candidate.**

ORION should expose connector contracts such as:
- connector discovery/status;
- bounded read;
- bounded write;
- explicit account/scope;
- evidence/receipt;
- Stop/cancellation where meaningful.

n8n nodes/workflows never become ORION policy or authority.

---

## 22. Browser extraction donors

### Firecrawl — `Sadusor/firecrawl`

Found:
- crawl;
- scrape;
- search;
- extract;
- PDF/HTML native processing;
- OpenAPI surface.

Use for structured read/extract jobs when a full interactive browser is unnecessary.

### Scrapling — `Sadusor/Scrapling`

Found:
- requests fetcher;
- Chrome fetcher;
- stealth Chrome;
- sessions;
- parser/selectors;
- dynamic/static extraction.

Use as a lightweight local extraction challenger.

### browser-use — `Sadusor/browser-use`

Found:
- browser agent loop;
- browser/session manager;
- DOM extraction;
- watchdogs for permissions, security, downloads, popups, screenshots, crash/state.

Previous ORION audit rejected its default permission boundary for adoption.  
Still useful as a **pattern donor/challenger**, not an authority/executor without a stricter ORION wrapper.

---

## 23. WORKSHOP — provider/model routing donor

Forks:
- `Sadusor/WORKSHOP`
- `Sadusor/WORKSHOP-NEXT`

Actual code found:
- provider bootstrap;
- Ollama;
- FreeLLMAPI;
- model registry/router;
- tool policy/parser/executor/idempotency;
- reviewer models;
- model role config;
- fallback-attempt UI.

### Disposition

**PRIMARY provider/catalog/routing donor.**

Borrow:
- discovery;
- health;
- model roles;
- fallback bookkeeping;
- safe provider serialization.

ORION owns:
- data classification;
- provider authorization;
- cost/free policy;
- final routing decision.

---

## 24. Voice/audio donors

### whisper.cpp — `Sadusor/whisper.cpp`
Local STT, streaming/VAD/server/bindings.

### Kokoro — `Sadusor/kokoro`
Local TTS model/pipeline and voices.

### openWakeWord — `Sadusor/openWakeWord`
Wake word, streaming example, VAD and custom model training.

### EchoFetch — `Sadusor/EchoFetch`
Android local Whisper JNI/engine, audio decoder, transcription repository/workers and URL/media extraction.

### Disposition

Future voice stack:
```text
mic lease
→ local capture
→ VAD/wake gate where enabled
→ whisper.cpp STT
→ shared ORION turn journal
→ ORION response
→ phone/native TTS first, Kokoro optional
```

Voice does not bypass normal action authorization.

---

## 25. Evaluation donors

### LLMRouterBench — `Sadusor/LLMRouterBench`
Multiple routing baselines and evaluation tooling.

### Ai-Benchmark-v4 — `Sadusor/Ai-Benchmark-v4`
Local model benchmark script/lab.

### cua-bench
Bundled in the CUA monorepo; computer-use tasks, trajectories and reward/evaluator infrastructure.

### KiraPhoneBench — `Sadusor/KiraPhoneBench`
Phone/device evaluation donor.

### Disposition

Measurement only. Benchmarks do not define ORION authority.

---

## 26. Research/audit-only donors

### Buzz — `Sadusor/buzz`
Contains agent/ACP/permission and benchmark infrastructure. Keep as research/reference unless a bounded ORION need appears.

### OBLITERATUS — `Sadusor/OBLITERATUS`
Model surgery/abliteration/evaluation/checkpoint work. Research/benchmark only; not an ORION runtime dependency.

---

## 27. Donor references not resolved as installed forks in this audit

- **Aegis** — historical Browser Hand B2 physical evidence exists in the working-prototype docs, but no current installed fork named Aegis was resolved by GitHub connector search.
- **PizzaBot** — roadmap/reference donor, no installed fork resolved in this audit.

This is not evidence that the repositories do not exist elsewhere. It means only that this audit did not resolve them among the currently visible installed repositories.

---

## 28. Proven legacy ORION code that should be treated as a donor to V3

Repository inspected: `Sadusor/OrionPrototypeWorking`

This is especially important because V3 should migrate already-proven ORION mechanics rather than re-inventing them.

### Real prototype functions found in `spikes/coding_mode_github_loop/server.py`

Project/source:
- create/clone/validate/refresh project links;
- activate project;
- scope checks;
- GitHub Check/Sync/Run/Stop;
- exact-SHA execution;
- update/restart handoff.

Local Brain:
- Ollama discovery/autostart;
- structured draft schemas;
- draft/revision;
- semantic quality verifier;
- preflight;
- workspace snapshot/relevance selection;
- post-run review.

Hands:
- generated PowerShell lane;
- registered capability lane;
- manual lane;
- Stop;
- evidence generation;
- result publication;
- Work Exchange.

Sessions/background:
- dispatch task/session start/stop/list;
- session supervisor with process ownership and stop-all.

Providers/reviewers:
- DPAPI provider vault;
- provider test/enable/delete/save;
- reviewer model discovery;
- independent reviewer run/stop;
- streaming evidence;
- usage/allowance capture.

Memory:
- memory candidate submission/list;
- Work Exchange read.

### Registered capability code

`capabilities.py`:
- canonical action hashing;
- exact artifact publication;
- repository/branch/origin proof;
- path containment;
- remote SHA verification.

`capabilities_v1.py`:
- web URL normalization;
- browser executable resolution;
- bounded `open_web_url`.

`dispatch_runtime.py`:
- task catalog;
- start;
- get/list;
- stop;
- result publishing.

`session_supervisor.py`:
- PowerShell execution session;
- live output pump;
- get/list/tail/alive;
- targeted stop;
- stop-all.

### Prototype contracts worth carrying forward

- Browser Hand contract: deterministic lifecycle, domain grant compilation, external-untrusted tagging, no credentials in first surface, truthful Stop, evidence-based verification.
- Memory Write contract: Hands report candidates; ORION alone promotes/rejects/defers; append/supersede rather than silent overwrite.
- Memory Explorer: derived/rebuildable graph, evidence refs on every edge, current/history separation.
- Reasoning Provider contract: same local/cloud request/result shape; cloud authorization; unknown cost remains unknown.
- Provider Vault: DPAPI CurrentUser; raw secrets never returned.
- Reviewer Connector: identical independent prompt, independent raw outputs, explicit cloud egress, late results cannot advance stopped run.
- Capability Registry: model chooses typed capability/parameters; ORION owns deterministic mechanics; explicit human request can authorize the exact benign bounded capability.

---

## 29. Donor selection rule for tomorrow and beyond

Do not select a donor because its README looks impressive.

For each ORION function:
1. state the ORION-owned contract;
2. identify risk class and authority boundary;
3. identify evidence and Stop semantics;
4. compare internal/proven ORION code first;
5. compare donor implementations;
6. choose the smallest replaceable mechanism;
7. physically falsify it;
8. freeze it after PASS.

The goal is not “one framework that does everything.”

The goal is:

```text
stable ORION contracts
+ replaceable best-in-class parts
+ deterministic evidence
+ owner control
```
