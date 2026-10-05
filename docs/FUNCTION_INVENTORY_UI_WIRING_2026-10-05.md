# ORION V3 Function Inventory + STRATA UI Wiring Checklist — 2026-10-05

Status: **TOMORROW SOURCE OF TRUTH**  
Purpose: enumerate ORION functions/capabilities so the accepted PC/phone UI can be wired without forgetting features, inventing fake state, or rebuilding the engineering Remote.

## 0. How to read this inventory

Status labels:

- **LIVE-V3** — implemented in the current ORION-V3 product backend/shell.
- **UI-READY / BACKEND-REFUSES** — STRATA already has a route/state seam, but current V3 server deliberately returns refusal.
- **PROVEN-LEGACY** — real implementation exists in `Sadusor/OrionPrototypeWorking` and has relevant physical/prototype evidence; migrate the contract/mechanics, do not copy blindly.
- **LEGACY-IMPLEMENTED** — code exists in the working prototype but still needs a V3 contract/physical gate.
- **DONOR-READY** — donor code exists and is a candidate behind an ORION contract.
- **PLANNED** — architecture/contract exists but implementation is later.
- **LATER** — deliberately not tomorrow's scope.

Authority classes:

- **READ** — no side effect; still scoped/authenticated.
- **GREEN** — bounded benign action; explicit owner request may itself be authorization.
- **APPROVAL** — exact reviewed action/hash/plan requires trusted owner gesture.
- **YELLOW** — material external/write/sensitive action; compact confirmation and receipt.
- **RED** — destructive/system/security/credential/authority-changing; deny by default unless a separately qualified owner procedure exists.
- **STOP** — targeted cancellation/termination; must act on real owned execution, never merely change UI state.

No function is considered connected merely because a UI button exists.

---

# 1. Product runtime / transport / pairing

| Function | UI surface | Authority | Current source | Status | Evidence/result |
|---|---|---:|---|---|---|
| Runtime health | System / connection | READ | `GET /api/health` | LIVE-V3 | service/runtime truth |
| PC live status snapshot | all pages | READ | `GET /api/status` | LIVE-V3 | canonical snapshot |
| Phone pair | phone onboarding | auth | `POST /api/pair` | LIVE-V3 | memory-only device token |
| Forget/re-pair device | phone settings | auth | client token clear + pair | LIVE-V3 client seam | link becomes unpaired |
| Poll/reconnect/stale/offline | global shell | READ | `real-bridge.js` | LIVE-V3 | explicit link states |
| Header-authenticated stream/SSE | global shell | READ | planned transport seam | PLANNED | same snapshot events |
| Native PC CLOSE | PC top bar | STOP/lifecycle | WebView message → window close → lifecycle cleanup | LIVE-V3 code | must share STOP cleanup |
| START ORION | system lifecycle | owner-local | `START ORION.bat` / start script | LIVE-V3 code | backend + native UI |
| STOP ORION | system lifecycle | STOP | `STOP ORION.bat` / stop script | LIVE-V3 code | bounded cleanup |
| ZeroTier ownership | system lifecycle | lifecycle | start/stop scripts | LIVE-V3 code | close only if ORION-owned |
| Ollama ownership | System / Local Brain | lifecycle | start/stop scripts | LIVE-V3 code | start if needed; close only if ORION-owned |
| System update/restart | System | HIGH | `POST /api/system/update-restart` route exists | UI-READY / BACKEND-REFUSES | only after exact SHA PASS |

**Tomorrow Gate 0:** before wiring actions, do one bounded product-shell regression if still required for the latest CLOSE + Ollama lifecycle code. Do not redesign the UI.

---

# 2. Shared conversation / Local Brain

The accepted interaction is chat-first: the bottom **Ask ORION…** composer is the primary intent entry.

| Semantic function | UI | Authority | Existing implementation | V3 status |
|---|---|---:|---|---|
| Ask ORION / submit goal | composer | request | legacy `start_local_brain_draft(goal, model)` | UI-READY / BACKEND-REFUSES |
| Draft structured action | Home/Personal lane | none yet | legacy draft schemas + Qwen | PROVEN-LEGACY |
| Stream draft/conclusion | Personal lane | READ | legacy live preview | PROVEN-LEGACY |
| Semantic quality verify | timeline Verify | ORION internal | legacy quality verifier | PROVEN-LEGACY |
| Deterministic preflight | timeline Preflight | ORION internal | legacy script/capability preflight | PROVEN-LEGACY |
| Revise rejected/blocked draft | approval/blocked card | request | `POST /api/local-hand/revise` | UI-READY / BACKEND-REFUSES |
| Model selection | AI / Personal lane | owner choice | legacy live Ollama catalog | LEGACY-IMPLEMENTED |
| FAST / THINKING mode | lane state | ORION scheduler | architecture approved | PLANNED backend truth |
| Post-run Local Brain review | result/timeline | reasoning only | legacy `_local_brain_review_after_run` | LEGACY-IMPLEMENTED |
| Shared conversation journal | Home / Work | canonical ORION state | contract direction | PLANNED |
| Turn IDs / conversation IDs | all reasoning | canonical ORION state | architecture direction | PLANNED |
| Personal lane context | Personal | context only | decision 0010 | PLANNED |
| Project lane context | Project | context only | decision 0010 | PLANNED |
| Context isolation between lanes/projects | all lanes | ORION policy | decisions/contracts | PLANNED |

### Tomorrow priority

**FIRST functional integration should be Local Brain Ask → draft → verifier → preflight → truthful UI state.**

Why first:
- it connects the central product interaction;
- Qwen 3.5 9B already won the local-manager benchmark;
- Ollama lifecycle is already part of ORION;
- it exercises state, lane, model, reasoning and approval UI without requiring external connectors.

No model receives execution authority from this wiring.

---

# 3. Deterministic Hands / capability registry

Target architecture:

```text
owner request
→ model interprets intent/parameters
→ ORION validates exact registered capability + scope
→ deterministic Hand executes
→ receipt/evidence
→ ORION verifies
```

## Registered / near-term capabilities

| Capability | Intended function | Authority | Existing source | Status |
|---|---|---:|---|---|
| `filesystem.search` | find files/text/symbol candidates inside approved scope | GREEN/READ | V3 roadmap/OpenJarvis donor | PLANNED V3.1 |
| `filesystem.list` | list directory/scope | GREEN/READ | roadmap | PLANNED V3.1 |
| `filesystem.reveal` | reveal/open a file/folder to owner | GREEN | roadmap | PLANNED V3.1 |
| `project.publish` / `publish_exact_artifact` | publish exact authorized bytes/path to exact Git repo/branch | GREEN when request exact | legacy capability registry | **PROVEN-LEGACY PHYSICAL PASS** |
| `open_web_url` | launch bounded URL | GREEN | legacy `capabilities_v1.py` | LEGACY-IMPLEMENTED/probed |
| `review.run_independent` | send exact prompt to selected reviewers | YELLOW cloud egress | reviewer contract | PLANNED typed capability |
| generated PowerShell | compatibility path for not-yet-registered mechanics | APPROVAL | legacy Local Hand | PROVEN-LEGACY |
| coding Hand | bounded edits/tests in ORION sandbox | APPROVAL/policy | OpenHands/software-agent-sdk/Claude/ACP | DONOR-READY |
| browser Hand | bounded read/interact | GREEN/YELLOW by action | Browser Hand contract | DONOR-READY |
| computer Hand | native GUI action | GREEN/YELLOW/RED | CUA/OpenBot/UI-TARS | DONOR-READY |
| Android Hand | phone/device actions | GREEN/YELLOW/RED | Artemis/KIRA | DONOR-READY |

### Capability registry fields ORION must own

Every reusable capability/skill eventually needs:
- stable id/version;
- code/content hash;
- provenance;
- risk class;
- allowed operations;
- allowed paths/project scopes;
- network policy;
- secret requirements;
- confirmation class;
- sandbox requirement;
- time/resource budgets;
- evidence requirements;
- qualification status;
- disabled/revoked state.

OpenJarvis/CLI-Anything provide implementation patterns; ORION owns the contract.

---

# 4. PowerShell / approval path

| Function | UI route/state | Authority | Existing source | Status |
|---|---|---:|---|---|
| display proposed script | approval card | READ | STRATA state contract | UI ready |
| exact script hash | approval card | ORION internal | legacy Local Brain | PROVEN-LEGACY |
| Approve & Run | `POST /api/local-hand/run` | APPROVAL + trusted click | legacy `start_local_hand` | UI-READY / BACKEND-REFUSES |
| mutation-after-approval denial | approval gate | ORION | donor contract probe | PHYSICAL PASS contract |
| process output stream | action/result | READ | legacy session supervisor | PROVEN-LEGACY |
| exit code | result | READ | legacy session supervisor | PROVEN-LEGACY |
| semantic completion review | result | ORION verifier | legacy | LEGACY-IMPLEMENTED |
| exact targeted Stop | `POST /api/local-hand/stop` | STOP | legacy | UI-READY / BACKEND-REFUSES |
| manual arbitrary script | engineering only | owner/manual | TheHands / legacy manual lane | **DO NOT PORT TO PRODUCT UI** |

TheHands remains the engineering Manual PowerShell surface. ORION product should not recreate it.

---

# 5. Project / repository functions

| Function | UI | Authority | Existing source | Status |
|---|---|---:|---|---|
| list project links | Work / Connectors | READ | `GET /api/project-links` | LIVE-V3 |
| show active project | Work | READ | status snapshot | LIVE-V3 |
| refresh links | Work | command | route exists | UI-READY / BACKEND-REFUSES |
| activate existing project | Work | GREEN | route exists + legacy `set_active_project_link` | UI-READY / BACKEND-REFUSES |
| create project link | later settings | YELLOW | legacy `create_project_link` | LEGACY-IMPLEMENTED; not STRATA route |
| clone + link project | later settings | YELLOW/network | legacy `clone_and_link_project` | LEGACY-IMPLEMENTED; not STRATA route |
| validate link identity | backend | ORION internal | legacy commit/scope hash checks | PROVEN-LEGACY |
| project scope containment | backend | ORION policy | legacy capability target validation | PROVEN-LEGACY |
| repo-map/code context | Project lane | READ | Graft/Aider | DONOR-READY |
| Work Exchange latest | Work | READ | `GET /api/work-exchange/latest` | LIVE-V3 route, currently not_connected |
| exact artifact promotion | Work/result | GREEN/APPROVAL by scope | legacy registered capability | PROVEN-LEGACY |

Tomorrow: wire **existing project activation/refresh**, not clone/create, before adding new project-management UI.

---

# 6. GitHub exact-SHA coding loop

Already represented in STRATA state and routes.

| Function | Route | Authority | Existing source | Status |
|---|---|---:|---|---|
| GitHub Check | `POST /api/github/check` | GREEN/READ network | legacy `check()` | UI-READY / BACKEND-REFUSES |
| Sync checkout | `POST /api/github/sync` | bounded write | legacy `sync_checkout()` | UI-READY / BACKEND-REFUSES |
| Enter coding mode | `POST /api/mode/enter` | owner | legacy | UI-READY / BACKEND-REFUSES |
| Pause | `POST /api/mode/pause` | owner | legacy | UI-READY / BACKEND-REFUSES |
| Resume | `POST /api/mode/resume` | owner | legacy | UI-READY / BACKEND-REFUSES |
| Exit | `POST /api/mode/exit` | owner | legacy | UI-READY / BACKEND-REFUSES |
| Approve exact pending SHA + Run | `POST /api/run/start` | APPROVAL/trusted click | legacy `start()` | UI-READY / BACKEND-REFUSES |
| Stop exact-SHA run | `POST /api/run/stop` | STOP | legacy `stop()` | UI-READY / BACKEND-REFUSES |
| publish evidence | result | backend | legacy result branch/evidence | PROVEN-LEGACY |

Important: this is a **project/coding function**, not the ORION product's identity. Do not turn the new UI back into an engineering dashboard.

---

# 7. Work Queue / background sessions

The UI already has a Background lane and session model.

| Function | UI | Authority | Existing source | Status |
|---|---|---:|---|---|
| task catalog | Work | READ | legacy `dispatch_runtime.task_catalog` | LEGACY-IMPLEMENTED |
| start bounded task/session | `POST /api/session/start` | command/approval per task | legacy dispatch runtime | UI-READY / BACKEND-REFUSES |
| list sessions | Background | READ | legacy | state seam exists |
| session state | Background | READ | legacy session supervisor | state seam exists |
| live output/tail | Background/detail | READ | legacy `tail()` | LEGACY-IMPLEMENTED |
| targeted session stop | `POST /api/session/stop` | STOP | legacy | UI-READY / BACKEND-REFUSES |
| stop all ORION-owned execution | global STOP | STOP | architecture requirement | PLANNED unified command |
| resume/recover after ORION restart | Background | ORION lifecycle | legacy recovery patterns | PLANNED V3 |

Rule: project/background work must not block Personal Assistant responsiveness.

---

# 8. Providers / Local models / Cloud AI Council

## Provider catalog/vault

| Function | UI | Authority | Existing source | Status |
|---|---|---:|---|---|
| list providers | AI / Connectors | READ | `GET /api/providers` | LIVE-V3 (empty today) |
| discover local Ollama models | AI | READ | legacy Reviewer Connector/OpenJarvis | LEGACY-IMPLEMENTED |
| provider health/test | `POST /api/providers/test` | READ/network | legacy Provider Vault | UI-READY / BACKEND-REFUSES |
| enable/disable provider | `POST /api/providers/enabled` | owner config | legacy | UI-READY / BACKEND-REFUSES |
| save provider | future settings | YELLOW secret config | legacy DPAPI vault | not STRATA allowlisted |
| delete provider | future settings | YELLOW | legacy | not STRATA allowlisted |
| raw key retrieval | none | forbidden | contract | **MUST NEVER EXIST** |
| model roles/router | backend | ORION policy | WORKSHOP/OpenJarvis | DONOR-READY |

## Reviewer / cloud council

| Function | UI | Authority | Existing source | Status |
|---|---|---:|---|---|
| latest reviewer state | AI / Specialists | READ | `GET /api/reviewers/latest` | LIVE-V3 (empty today) |
| refresh reviewer catalog | route | READ/network | legacy | UI-READY / BACKEND-REFUSES |
| select reviewers | Specialists | owner selection | STRATA/Product | UI model ready |
| run independent review | future registered route | YELLOW cloud egress | legacy `ReviewerConnector.start` | LEGACY-IMPLEMENTED; intentionally not route-allowlisted |
| stream independent outputs | Specialists | READ | legacy | LEGACY-IMPLEMENTED |
| stop reviewer run | `POST /api/reviewers/stop` | STOP | legacy | UI-READY / BACKEND-REFUSES |
| usage/allowance | reviewer cards | READ | legacy | LEGACY-IMPLEMENTED |
| synthesize reviews | Project/AI | reasoning only | future ORION/model | PLANNED |

Rules:
- same exact prompt to independent reviewers;
- one reviewer does not see another before completion;
- unknown quota/cost stays unknown;
- reviewer advice never grants execution authority;
- cloud egress remains explicit policy/owner decision.

---

# 9. Memory / learning / Memory Explorer

## Memory write boundary

```text
Hand/model/source
→ MemoryCandidate
→ ORION decision: PROMOTE / REJECT / DEFER
→ canonical append/supersede record
```

| Function | UI | Authority | Source | Status |
|---|---|---:|---|---|
| list candidate memories | Memory | READ | `GET /api/memory/candidates` | LIVE-V3 (preview) |
| submit candidate | backend / future import | no authority | legacy `submit_memory_candidate` | LEGACY-IMPLEMENTED; not STRATA route |
| retrieve/search Memory | Memory / Ask context | READ | KnowledgeOS + legacy BM25 | DONOR/LEGACY ready |
| retrieval trace | Memory detail | READ | KnowledgeOS SearchTrace | DONOR-READY |
| provenance drilldown | Memory detail | READ | ORION contracts | PROVEN architecture |
| promote candidate | Memory | ORION memory gate | contract | PLANNED |
| reject candidate | Memory | ORION memory gate | contract | PLANNED |
| defer candidate | Memory | ORION memory gate | contract | PLANNED |
| supersede/correct | Memory | ORION memory gate | contract | PLANNED append-oriented |
| forget/delete source | Memory | owner + provenance cascade | architecture | PLANNED |
| ingest selected file/folder/project | Memory | owner-scoped | decision 0010 | PLANNED |
| image/PDF metadata | Memory | READ | KnowledgeOS/vision | DONOR-READY |
| code graph context | Project/Memory | READ | Graft/Aider/codebase-memory | DONOR-READY |
| hybrid/graph/temporal consolidation | backend | derived only | agentmemory/Tencent/OpenViking | DONOR-READY |
| Memory Explorer snapshot | Memory constellation | READ/derived | legacy contract | PROVEN contract / later product wiring |
| LoRA/QLoRA personalization | AI/System | explicit owner training | roadmap | LATER |

Never:
- train on whole PC automatically;
- store credentials in Memory;
- let external page/file text become authority;
- silently overwrite canonical memory.

---

# 10. Connectors / workflows

The **Connectors** page should present real capabilities, not imply connection from a card.

General connector contract to implement:

```text
descriptor()
health/status()
accounts/scopes()
read(request)
propose_write(request)
execute_approved_write(frozen_contract)
receipt()
stop/cancel() if meaningful
```

Every connector must expose:
- stable connector ID/version;
- provider/service;
- connection state;
- account identity without secret leakage;
- authorized scopes;
- data classes;
- READ/WRITE/EXTERNAL-SIDE-EFFECT risk class;
- rate/cost policy;
- operation/idempotency ID;
- evidence/receipt;
- uncertain-outcome state;
- revocation/disconnect.

## Planned connector families

| Connector | Function set | Donor | Priority |
|---|---|---|---|
| GitHub/source | read/check/sync/publish exact artifact | existing ORION | NOW |
| Local Ollama | list/health/generate/cancel where real | OpenJarvis/legacy | NOW |
| Cloud reviewers | model list/test/run/stop/usage | legacy + WORKSHOP | NOW |
| Email | search/read/draft/send | n8n/OpenMuse pattern | AFTER core |
| Calendar | list/create/update/delete with exact review | OpenMuse/n8n | AFTER core |
| Workflow engine | trigger/status/cancel/receipt | n8n | AFTER connector contract |
| Files/cloud storage | list/read/write bounded | OpenBot/n8n | later |
| Browser read/extract | navigate/extract/cite | PinchTab/Firecrawl/Scrapling | after core |
| Computer | inspect/action/live/takeover | CUA/OpenBot | later gate |
| Android/device | inspect/action/verify | Artemis/KIRA | later gate |

---

# 11. Browser functions

The validated Browser Hand contract distinguishes read-only from side effects.

## Read-only first surface

- `navigate(url)`;
- `wait(condition/time)`;
- `extract_text(selector/ref)`;
- `extract_attr(selector/ref, attr)`;
- screenshot;
- final URL;
- visited URLs;
- network-scope evidence.

Authority:
- domain/origin comes from ORION PermissionGrant;
- page content tagged `external_untrusted`;
- no credentials/personal profile in first surface.

## Later interactive browser functions

- click;
- type;
- form submit;
- download/upload;
- authenticated session;
- human takeover.

These require separate YELLOW/RED contracts and evidence.

Donor tournament:
- PinchTab;
- CUA browser mode;
- historical Aegis contract;
- Firecrawl/Scrapling for read/extract only.

---

# 12. Computer / desktop functions

Future `Computer Hand` semantic surface:

- list monitors/windows;
- screenshot/observe;
- focus/open/close app;
- click/type/key;
- read visible UI state;
- verify screen/result;
- live view;
- request human takeover;
- release human control;
- Stop owned action/session.

Donors:
- CUA Driver for operation;
- OpenBot for control ownership/takeover/secrets;
- UI-TARS for grounding;
- CLI-Anything for app-specific deterministic alternatives.

Rule: prefer deterministic app/CLI Hand over pixel GUI automation when both can satisfy the task.

---

# 13. Phone / Android/device functions

Product phone app itself remains a thin client to PC ORION.

Separate future Android Hand functions:
- device discovery/health;
- screen hierarchy;
- screenshot;
- tap/swipe/type/back/home;
- app launch;
- verification/checkpoint;
- device lock;
- record/replay evidence;
- targeted Stop.

Donors:
- Artemis;
- KIRA.

Phone product capabilities later:
- push approval notification;
- push-to-talk;
- status/events;
- PC live view;
- owner takeover/control where separately authorized.

The phone never mints authority by being connected.

---

# 14. PC Live View / media plane

Planned separately from command/state transport.

Functions:
- enumerate display/window source later;
- start view-only capture;
- stop capture;
- adaptive FPS/quality;
- LIVE badge and timer;
- permission timeout/extend;
- visibility/ownership state.

Rules:
- viewing is **not** computer-control authorization;
- media plane separate from command plane;
- privacy indicator visible on PC;
- low idle/battery consumption.

Candidate capture donors/patterns:
- Windows.Graphics.Capture / windows-capture;
- DXcam fallback;
- OpenBot/CUA screen streaming ideas.

---

# 15. Voice functions

Future voice semantic surface:
- acquire mic lease;
- start push-to-talk;
- stop/cancel capture;
- VAD;
- STT;
- append transcript as normal ORION turn;
- TTS response;
- release mic lease;
- optional wake word later.

Donors:
- KIRA lease/session patterns;
- whisper.cpp STT;
- openWakeWord;
- Kokoro;
- phone native TTS first;
- EchoFetch audio pipeline ideas.

Voice input is just another owner channel. It does not bypass policy.

---

# 16. Evidence / verification / audit functions

These are core product functions, not optional diagnostics.

For every execution ORION needs:

- operation/task/attempt ID;
- actor/initiator;
- project/scope;
- frozen request/plan hash where applicable;
- authorization/lease reference;
- start time;
- exact executor/Hand;
- process/session identity;
- output/exit;
- artifacts + hashes;
- external-effect evidence;
- verifier result;
- outcome:
  - confirmed;
  - failed;
  - refused/blocked;
  - stopped;
  - unverifiable;
  - uncertain;
- cleanup evidence;
- provenance pointer.

UI functions:
- result card;
- evidence ladder;
- evidence detail;
- copy/export evidence;
- show uncertainty honestly.

Donor patterns:
- CLI-Anything trajectories/manifests;
- OpenMuse receipts/idempotency;
- OpenBot audit-before-act;
- KnowledgeOS provenance/search trace.

---

# 17. STOP / pause / control ownership

STOP is a cross-cutting ORION function.

Required targets:
- Local Hand PowerShell;
- exact-SHA run;
- background session;
- reviewer run;
- Browser Hand;
- Computer Hand;
- Android Hand;
- provider request where upstream cancellation exists;
- all ORION-owned active execution for global STOP.

Semantics:
1. UI sends a target, not a cosmetic state change.
2. ORION marks cancellation intent.
3. no new actions scheduled in stopped scope.
4. adapter targets real process/session/device/browser.
5. evidence records requested/acknowledged/terminated/unresolved.
6. grants/leases expire/revoke where appropriate.
7. late results cannot advance task state.
8. unknown external effect remains unknown.

Human takeover is a separate control lease:
- autonomous Computer/Browser actions are refused while owner has control;
- return of control is explicit and audited.

---

# 18. Skills / learned routines

Future Skill Registry functions:
- list;
- inspect;
- create candidate from successful trace;
- qualify;
- enable;
- disable;
- version;
- revoke;
- test;
- evidence history.

Donors:
- OpenJarvis SkillDiscovery;
- CLI-Anything skills;
- KIRA learned routines;
- OpenSandbox skill registry.

A skill is instructions/implementation, **not authority**.

Lifecycle:

```text
successful observed workflow
→ candidate skill
→ deterministic/adversarial qualification
→ owner/ORION promotion
→ bounded versioned capability
```

---

# 19. STRATA route inventory — exact current allowlist

## Reads — already accepted by UI

- `GET /api/status`
- `GET /api/project-links`
- `GET /api/work-exchange/latest`
- `GET /api/memory/candidates`
- `GET /api/reviewers/latest`
- `GET /api/providers`

## Auth

- `POST /api/pair`

## Local Brain / approval

- `POST /api/local-hand/draft`
- `POST /api/local-hand/revise`
- `POST /api/local-hand/run`

## Targeted STOP

- `POST /api/local-hand/stop`
- `POST /api/manual/stop`
- `POST /api/run/stop`
- `POST /api/session/stop`
- `POST /api/reviewers/stop`

## Project/GitHub/mode/session commands

- `POST /api/github/check`
- `POST /api/github/sync`
- `POST /api/mode/enter`
- `POST /api/mode/pause`
- `POST /api/mode/resume`
- `POST /api/mode/exit`
- `POST /api/session/start`
- `POST /api/project-links/refresh`
- `POST /api/project-links/activate`
- `POST /api/reviewers/catalog/refresh`
- `POST /api/providers/test`
- `POST /api/providers/enabled`

## High impact

- `POST /api/system/update-restart`

## Deliberately NOT exposed in STRATA today

- `/api/manual/run`
- `/api/reviewers/run`
- `/api/project-links/clone`
- `/api/project-links/create`
- `/api/providers/save`
- `/api/providers/delete`
- `/api/generate`
- `/api/tags`
- `/api/memory/candidate` write
- extra `/api/session/*`

This deliberate small allowlist is good. Add a route only when a product screen genuinely needs it and its ORION contract is ready.

---

# 20. UI pages → function groups

## Home

Must eventually expose:
- Ask ORION;
- current lane/state;
- current task/timeline;
- approval card;
- result/evidence;
- project context;
- global/targeted Stop when applicable.

## Work

Must expose:
- project selection;
- Work Queue;
- task/session status;
- exact-SHA project work where relevant;
- background sessions;
- evidence/results.

Do not expose arbitrary engineering shell controls.

## AI

Must expose:
- Local Brain model/status/mode;
- cloud reviewer/provider availability;
- independent reviewer runs;
- usage/allowance;
- no invented “free” claims.

## Memory

Must expose:
- candidate preview;
- retrieval/search;
- provenance;
- promotion state;
- Memory Explorer later;
- current/history/supersession.

## Connectors

Must expose:
- real connection state;
- scopes/account;
- read/write capability;
- risk;
- health;
- last receipt;
- no authority implied by “connected”.

## System

Must expose:
- runtime health;
- PC/phone pairing;
- Ollama/engine state;
- substrate/version;
- lifecycle;
- evidence diagnostics;
- global STOP;
- update/restart only after qualification.

---

# 21. Tomorrow's wiring order

Do not try to connect everything in one change.

## Gate 0 — preserve the shell

- confirm current main is clean;
- build/start current ORION product once if needed;
- verify native PC + phone still use the accepted STRATA shell;
- verify latest CLOSE/Ollama ownership behavior if it has not yet been physically requalified;
- freeze appearance again.

## Slice 1 — Local Brain

Connect:
1. Ollama/model discovery;
2. `Ask ORION` → draft;
3. streaming/conclusion;
4. semantic verifier;
5. deterministic preflight;
6. Personal lane state;
7. blocked/revise state;
8. no execution yet unless typed capability is already proven.

Physical proof from both PC and phone.

## Slice 2 — first deterministic functions

Connect:
- project link refresh/activate;
- `filesystem.search`;
- `filesystem.list`;
- `filesystem.reveal`;
- proven `publish_exact_artifact/project.publish`;
- bounded `open_web_url` only if its contract is accepted for V3.

Prefer registered capabilities over generated shell.

## Slice 3 — project/work state

Connect:
- Work Exchange;
- task catalog;
- background sessions;
- targeted Stop;
- exact-SHA GitHub lane where useful.

Keep this subordinate to the chat-first product.

## Slice 4 — AI Council / providers

Connect:
- local model catalog;
- provider metadata;
- provider test/enable;
- reviewer catalog;
- independent review capability;
- streaming result/evidence;
- STOP.

Provider secret management may get a separate settings surface; do not leak raw credentials into STRATA state.

## Slice 5 — Memory read/retrieval

Connect:
- candidate list;
- KnowledgeOS-style retrieval request;
- provenance;
- retrieval trace;
- project/personal scope.

Do **not** auto-promote memory yet.

## Slice 6 — connector framework

Create stable connector descriptor/health/read/write/receipt interface, then adapt:
- GitHub/source;
- calendar/email;
- workflows;
- browser read/extract.

## Later gated slices

- Memory promotion/consolidation;
- browser interaction;
- Computer Hand;
- Android Hand;
- Live View;
- voice;
- learned skills;
- personal fine-tuning.

---

# 22. Definition of “connected” for every function

A function is not DONE because the backend route returns HTTP 200.

It is connected only when:

1. UI action maps to one registered typed route/capability.
2. backend authenticates caller/channel.
3. project/lane/conversation scope is bound.
4. ORION risk/permission policy runs.
5. approval semantics are correct.
6. execution target is replaceable and bounded.
7. Stop semantics are defined if work can remain active.
8. result is normalized into canonical ORION state.
9. evidence/receipt exists.
10. UI shows only backend-owned truth.
11. PC physical test passes.
12. phone physical test passes.
13. regression test protects the contract.
14. working slice is frozen before the next expansion.

---

# 23. The short version to remember tomorrow

```text
UI is ready.
Authority model is ready.
Most action routes are intentionally disconnected.

Tomorrow:
  1. connect Qwen/Ollama Local Brain to Ask ORION;
  2. connect verifier + preflight;
  3. connect proven deterministic capabilities;
  4. connect Work Queue/project state;
  5. connect providers/reviewers;
  6. connect Memory retrieval;
  7. then build external connectors.

Never:
  - turn STRATA into TheHands;
  - give a model authority;
  - fake a connected capability;
  - let a donor own canonical state;
  - trade deterministic mechanics for agent improvisation.
```
