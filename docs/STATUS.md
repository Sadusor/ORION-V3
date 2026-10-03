# ORION V3 Status

Updated: 2026-10-03

## Stage

**Gate 1 COMPLETE — architecture frozen around ORION Core + Capability Registry + canonical Memory; capability inventory is the next priority.**

ORION-V3 is a separate repository from the proven legacy ORION implementation.

## Gate-1 claims

- OpenJarvis substrate: **ADOPTED AS REPLACEABLE SUBSTRATE**
- ORION remains sole authority: **PHYSICALLY PROVEN for Gate-1 scope**
- Authority Boundary V0: **PHYSICAL PASS**
- ORION authority unit contract: **AUTOMATED PASS (16/16)**
- real pinned OpenJarvis + Windows integration: **PHYSICAL PASS**
- native Jarvis bypass falsifier: **PHYSICAL PASS**
- Jarvis policy widening falsifier: **PHYSICAL PASS**
- timeout != Stop falsifier: **PHYSICAL PASS**
- ORION-owned killable worker Stop: **PHYSICAL PASS**

## Gate-1 evidence identity

ORION-V3 tested SHA:
`dc13d5caddf2489879b2d300addaa5419b3d5975`

OpenJarvis:
`Sadusor/OpenJarvis@309a4f1044ccfb2032264832a31fef2f1d314586`

Legacy ORION Remote transport task:
`df4ef699706ede0ce6d9de34eaeb74b84213a116`

Legacy Remote transport record:
`attempt 399`

That number is **not an ORION-V3 attempt count**. It is retained only to locate the external transport evidence.

## ORION-V3 run numbering

ORION-V3 has its own sequence beginning with:

`V3-RUN-001`

Legacy ORION Remote attempt counters are never counted as V3 development runs.

## V3.1 architecture correction

Active branch:
`agent/v3.1-openjarvis-tools`

A parallel `orion_v3.hands` design was drafted on an obsolete branch but rejected **before physical execution** because it duplicated the substrate we had just adopted.

The active architecture is:

```text
OWNER
  -> ORION authority / Action Lease / trusted bindings / evidence / Stop truth
      -> OpenJarvis ToolRegistry + ToolExecutor
          -> existing OpenJarvis tool
             OR smallest OpenJarvis-native extension for a demonstrated gap
```

There is no second ORION tool/Hand registry.

## V3.1 donor inventory

At pinned OpenJarvis revision `309a4f1044ccfb2032264832a31fef2f1d314586`:

- `file_read`: **REUSE DONOR BUILT-IN**
- `file_write`: **REUSE DONOR BUILT-IN**
- browser/web/shell/patch/memory tools: **INVENTORY/QUALIFY BEFORE CUSTOM CODE**
- exact-basename local `filesystem.search`: no dedicated built-in found, therefore one minimal custom **OpenJarvis-registered** extension is justified.

The extension:
- subclasses OpenJarvis `BaseTool`;
- registers in OpenJarvis `ToolRegistry`;
- executes through OpenJarvis `ToolExecutor`;
- receives ORION lease and trusted roots out of band;
- does not expose absolute trusted roots to the model;
- returns structured data that ORION converts into canonical `EvidenceEnvelope`.

## Current priority

Earlier `Next physical run` notes below are historical unless explicitly marked current.

Current sequence after the 2026-10-03 architecture freeze:
1. inventory proven capabilities in legacy ORION Remote, V3, OpenJarvis and native Windows/PowerShell;
2. define the semantic Capability contract;
3. batch-register/harvest the first capability pack;
4. benchmark Qwen3.5-9B on typed intent/parameter routing;
5. bring canonical Memory and the local append-only AI/Hand exchange forward;
6. automate the cloud-AI Coding Factory around existing Coding Hands;
7. add Whole-PC Computer Hand escalation later.

See `docs/ORION_SYSTEM_MODEL.md`.

## Protected fallback

Legacy ORION remains available as the proven external transport/fallback.

Frozen fallback:
- repo: `Sadusor/Orion`
- branch: `checkpoint/2026-10-01-orion-remote-project-link`
- SHA: `327d32f714129ca633517a8f4158cd84820c1504`

Do not retire it until later V3 parity gates physically pass.


## V3-RUN-003 preflight result

Status: **FAIL — expected safety blockers found before launch**

Observed:
- pinned desktop frontend found;
- real OpenJarvis desktop inference source: `ollama`;
- real desktop source is confirmed, so stock launch would auto-start its own Jarvis backend;
- Node: `v24.19.0` PASS;
- global npm: `11.17.0`, below pinned desktop requirement `>=11.19 <12`.

Decision:
- do not modify/delete the user's real OpenJarvis inference configuration;
- do not globally upgrade npm just for this experiment;
- launch the desktop under a V3-isolated HOME with no inference source;
- use pinned npm `11.19.0` locally via `npx`.

Next run: `V3-RUN-004` isolated desktop launch.


## V3-RUN-004 correction

Remote transport reported PASS, but the owner observed **no visible desktop window**.

What V3-RUN-004 genuinely proved:
- V3-isolated OpenJarvis HOME created;
- user's real `~/.openjarvis` left untouched;
- pinned npm `11.19.0` usable locally;
- `npm ci` completed;
- local Tauri CLI present;
- sandbox had no confirmed inference source;
- standalone Jarvis/Ollama autostart was prevented by the sandbox.

What it did **not** prove:
- that a real OpenJarvis top-level desktop window appeared.

The prior `DESKTOP_UI_PROCESS=RUNNING` marker referred only to the hidden Tauri launcher process and is not accepted as UI evidence.

Next run:
`V3-RUN-005` requires Windows to report an actual visible top-level window with title matching `OpenJarvis` before PASS.


## V3-RUN-005 desktop visibility result

Status: **FAIL — donor dev-mode watcher bug identified**

The frontend itself started successfully:
- Vite 8.3.0 ready on localhost:5173.

The failure was:
`EBUSY: resource busy or locked`

Vite attempted to watch a Rust build DLL under:
`frontend/src-tauri/target/debug/deps/`

while Cargo was compiling the Tauri desktop. Windows locked the DLL and Vite's watcher crashed, causing Tauri's `beforeDevCommand` to exit non-zero before a visible window appeared.

This is not an ORION authority failure and not a Rust compiler failure.

V3 fix:
- keep the pinned donor tracked source untouched;
- create a temporary untracked V3 Vite config;
- import the donor's real `vite.config.ts`;
- add `server.watch.ignored = ['**/src-tauri/target/**']`;
- launch Tauri using that override;
- PASS only if Windows reports a visible OpenJarvis top-level window.

Next run:
`V3-RUN-006`.


## V3-RUN-007 selective OpenJarvis integration

Status: **PHYSICAL PASS**

Exact observed results:
- V3 regression: **19 passed in 0.06s**
- OpenJarvis WorkflowEngine: **EXECUTION PASS**
- autonomous agent loop in workflow path: **NONE**
- ORION Action Lease: **ENFORCED**
- ORION workflow evidence adapter: **PASS**
- stock donor WorkflowStepResult metadata: **DROPPED**
- decision: **adopt WorkflowEngine mechanics only with ORION evidence adapter**

Low-consumption local helper probe:
- model: `qwen3.5:9b`
- OpenJarvis agent: `SimpleAgent`
- turns: **1**
- tool calls: **0**
- route result: **FILE_SEARCH**
- prompt tokens: **130**
- completion tokens: **3**
- total tokens: **133**
- latency: **4572.7 ms**
- low-consumption router candidate: **PASS**

Architectural decision:
- deterministic ORION workflows remain preferred and require no inference;
- OpenJarvis `SimpleAgent` is retained only as a candidate bounded one-shot
  classifier/router/planner where deterministic routing is insufficient;
- multi-turn OpenJarvis agents are not the default ORION execution path;
- donor workflow telemetry is useful, but canonical evidence remains ORION-owned.

Next priority: **Hand qualification and replacement tournament**. Reuse donor Hands only where
they satisfy ORION scope/evidence/Stop contracts and actually outperform alternatives.


## V3-RUN-008 OpenHands Hands-only qualification

Status: **PHYSICAL PASS**

Pinned donor:
`Sadusor/software-agent-sdk@856d99d48e4b11c70c5f1cab21e7830570dbc324`

No OpenHands agent loop was run.

FileEditor Hand:
- allowed targeted `str_replace`: **PASS**
- edit outside explicit file allowlist: **DENIED**
- before/after structured edit evidence: **PASS**
- undo edit: **PASS**
- source audit: `workspace_root` is **NOT** a security boundary;
  ORION trusted bindings / exact edit allowlists remain required.

Windows Terminal Hand:
- PowerShell command execution: **PASS**
- interrupt: **PASS**
- spawned child process physically absent after interrupt: **PASS**
- Stop candidate: **PASS for tested child-process scope**

Important cost/runtime finding:
installing the OpenHands tools package pulls a large dependency surface
(browser-use, LiteLLM, MCP, cloud-provider SDKs, telemetry and related packages).
Therefore OpenHands tools should not become an always-loaded ORION core dependency.

Decision:
- **FileEditor mechanics: STRONG CODING HAND CANDIDATE**
- **Windows Terminal mechanics: STRONG CODING/COMMAND HAND CANDIDATE**
- **OpenHands autonomous agent: NOT REQUIRED for these capabilities**
- integrate as an **on-demand isolated specialist Hand backend** behind ORION authority,
  rather than embedding the full SDK stack into the ORION control-plane process.

Next falsifier:
prove ORION can launch the pinned OpenHands Hand backend on demand, pass only
ORION-authorized logical operations/trusted bindings, receive structured evidence,
and terminate the backend cleanly without granting it general control-plane authority.

## 2026-10-03 architecture freeze — supersedes primitive-Hand next steps

A major project clarification is now authoritative.

ORION is not one agent.

Shared ORION Core owns Memory, Task/Event state, semantic capabilities,
deterministic policy, authority, evidence, verification, Stop and continuity.

Distinct execution concepts:
- **Lightweight assistant:** Qwen semantic intent -> ORION policy -> known
  capability/workflow -> fast proven Hand.
- **Coding Factory:** cloud architect/reviewer workflow -> Qwen coordinator
  where useful -> existing/qualified Coding Hands -> tests/diff/evidence.
- **Whole-PC Computer Hand:** explicit escalation for novel GUI work only.
- **ORION interface:** ORION-owned Jarvis-style product experience; not a donor
  agent and not the Coding Factory.

Qwen rule:
- Qwen decides semantic intent/entities/ambiguity.
- ORION deterministically selects capability implementation, authority, risk,
  approval and scope.
- Qwen does not write arbitrary PowerShell as the normal path.

Capability Registry rule:
- semantic/policy registry, not a second low-level tool registry;
- known operations map to vetted implementations;
- direct unambiguous user requests should not trigger redundant approvals for
  routine bounded actions;
- implementation validates before effects and ORION verifies evidence after.

Memory/local exchange:
- Memory is an early core problem because long-running model/chat context is not
  reliable enough for ORION continuity;
- GitHub remains source control;
- future live AI<->PC transport should use local canonical Task/Event state plus
  an append-only event log for PROPOSAL/REVIEW/DECISION/ACTION/EVIDENCE/RESULT.

OpenMuse audit:
- strong donor for durable worker/task patterns, SQL leases, checkpoints,
  pause/resume/cancel, idempotent receipts, bounded loops and isolated-computer
  patterns;
- not ORION routing authority.

### V3-RUN-009 disposition

`V3-RUN-009` was staged but **must not be run as the current next step**.

It wrapped one OpenHands primitive edit operation. The code is retained as
experimental reference, but the architecture changed before execution:
continuing to wrap coding primitives one-by-one risks rebuilding command
sequencing already solved by mature Coding Hands/agents.

Next implementation work is the capability inventory and semantic contract, not
another primitive OpenHands wrapper.


## V3-RUN-012 intent abstraction

Status: **FAIL / INCOMPLETE**

Remote task SHA:
`8725e62d9b7c3ee36f4d50d0246b16dacac32367`

Remote attempt:
`413`

Exact V3 SHA:
`37db0cdd5b724d2a3279398294fc9e488826fc87`

Important:
- the benchmark crashed after case 29/32 because the Windows console used cp1252
  and could not print Greek text;
- no valid final aggregate score exists;
- the run nevertheless exposed that the benchmark over-specified raw model
  surface form (null-vs-omitted, every-vs-all) and mixed semantic ambiguity with
  policy/approval concerns.

Decision:
insert a deterministic ORION canonicalizer between Qwen semantic interpretation
and capability resolution.

Authoritative decision:
`docs/decisions/0004-intent-canonicalization.md`

Next:
**V3-RUN-013 — Canonicalization Isolation**
- force UTF-8 output;
- score canonicalized semantics rather than raw surface spelling;
- keep policy-intrusion evidence visible;
- same 32 semantic cases;
- measure raw entity accuracy vs canonical entity accuracy;
- no capability catalog in Qwen prompt.


## V3-RUN-014 native JSON + canonicalization

Status: **OWNER-OBSERVED PHYSICAL PASS**

Exact V3 bootstrap SHA:
`80f17408b105f789113d6ac9717cb6d24d9de465`

The run was launched through the Manual / External AI Workbench lane, not the
GitHub Remote task lane. The legacy results branch therefore still points to
V3-RUN-013 and does not contain the exact RUN-014 aggregates.

The RUN-014 bootstrap returns 0 only if regression plus the complete benchmark
gate pass. Therefore the following threshold claims are proven by the observed
PASS:
- hard no-dispatch: **100%**
- strict JSON: **100%**
- semantic contract-valid: **100%**
- one turn / zero tools: **100%**
- policy-clean: **100%**
- canonical intent accuracy: **>=95%**
- canonical entity accuracy: **>=90%**
- ambiguity detection: **>=85%**
- false ambiguity: **<=10%**
- deterministic resolver correctness: **100%**
- average total tokens/request: **<400**
- average latency/request: **<1000 ms**

This physically validates the architecture:

`Qwen literal semantics -> ORION canonicalizer -> ORION deterministic resolver`

on the current 32-case corpus.

It is not yet a production-scale language benchmark.

Next architectural priority:
**canonical Memory + append-only local event exchange**, while continuing to
harvest proven semantic capabilities from legacy ORION.


## V3-RUN-015 canonical state / Memory Gate

Status: **PHYSICAL PASS**

Exact tested V3 SHA:
`b800de5659ce74e3b52b88e41f4af53a5b6eacfd`

Observed regression:
- **64 passed in 1.00s**

Observed state/memory gate:
- database initialization: **PASS**
- project/task persistence setup: **PASS**
- deterministic event hash: **PASS**
- physical append-only Event trigger: **PASS**
- cross-project Event parent: **DENIED**
- Memory without provenance: **DENIED**
- cross-project Memory provenance: **DENIED**
- first Memory promotion: **PASS**
- silent current-Memory overwrite: **DENIED**
- explicit Memory supersession: **PASS**
- L0 project scope: **PASS**
- L1 current canonical scope: **PASS**
- L2 provenance expansion: **PASS**
- close/reopen persistence: **PASS**
- network/model dependency: **NONE**

This physically proves the first ORION-owned canonical continuity substrate:
immutable Event history + explicit Memory Gate + project-scoped L0/L1/L2
retrieval, without relying on model/chat memory.

Next:
**V3-RUN-016 — local Event Exchange**
`TASK -> PROPOSAL -> REVIEW -> DECISION -> ACTION -> EVIDENCE -> RESULT`

The next gate must prove idempotent external ingestion, causal/task scope,
recipient inbox/ack state without mutating Events, bounded task packets,
restart persistence and no GitHub/network dependency.


## V3-RUN-016 local Event Exchange

Status: **OWNER-OBSERVED PHYSICAL PASS**

Exact tested V3 SHA:
`0f77a8e07da6936e811936b50a1d201887a1ca93`

The owner reported PASS for:
`scripts/v33_local_event_exchange_bootstrap.ps1`

This physically validates the first local mailbox layer over the Event Ledger:
- exact external duplicate ingestion is idempotent;
- conflicting external duplicate is denied;
- recipient inbox/acknowledgement works without mutating Events;
- exchange receipt state is append-only;
- PROPOSAL -> REVIEW -> DECISION -> ACTION -> EVIDENCE -> RESULT causal chain persists;
- cross-task parent links are denied;
- bounded task packets remain project/task scoped;
- close/reopen preserves exchange state;
- no GitHub/network/model dependency is required by the gate.

Architectural consequence:
GitHub can remain source control while live AI<->ORION<->Hands coordination moves to the local Event Exchange.

### Remote transport correction

The temporary manual-PowerShell step was caused by the ChatGPT GitHub connector refusing writes to legacy `CURRENT_TASK.ps1`.

Legacy ORION already contained an exact-SHA named-task dispatcher driven by
`REMOTE_TASKS.json`.

That path is now being activated for V3 so future gates can use:
`CHECK GITHUB -> named V3 task -> RUN`
with a data-only `V3_GATE.json`, rather than copying PowerShell manually.


## V3-RUN-017 named-task transport

Status: **PHYSICAL PASS**

Remote SHA:
`98b1a78beb3edcab95f7dfe22fbf4b87d7c3580e`

Named task:
`v3-current-gate`

Session:
`8ba1ec0b741c`

Result:
`PASS`

This proves the restored normal transport:
`CHECK GITHUB -> APPROVE & RUN -> exact named V3 gate`

ORION Remote remains a separate operator/transport repo. ORION-V3 remains the
core under test. The bridge is data-driven through `V3_GATE.json`.

## V3-RUN-018 Coding Factory WorkPackage

Status: **PHYSICAL PASS**

Exact V3 SHA:
`6ef6e9ccd3bea7a9e56c5761173ed76609c47ddc`

Remote staging SHA:
`4544acdd1aebb23769392eff9bd4dc5f78e8dc68`

Named-task session:
`3c93b3f33491`

Observed regression:
- **77 passed in 3.02s**

Observed WorkPackage gate:
- artifact deduplication: **PASS**
- artifact tamper detection: **PASS**
- deterministic package identity: **PASS**
- manifest reload/integrity: **PASS**
- out-of-scope FILE: **DENIED**
- out-of-scope PATCH target: **DENIED**
- non-exact base SHA: **DENIED**
- package-bound PROPOSAL -> REVIEW -> DECISION chain: **PASS**
- candidate execution authority: **NONE**
- cross-package review reuse: **DENIED**
- reopen persistence: **PASS**
- network/model/execution dependency: **NONE**

This physically proves the first immutable candidate-output side of the Coding
Factory. A cloud coder can eventually hand ORION exact PATCH/FILE bytes and
ORION can freeze them into a scope-bound, base-SHA-bound WorkPackage before any
execution authority exists.

### Current next priority

Do **not** connect a cloud coder directly to a real checkout yet.

Next:
1. Attempt/lease ownership + checkpoint + Stop truth.
2. Isolated exact-SHA Git worktree execution envelope.
3. One harmless mechanically applied WorkPackage with exact path/diff/evidence
   verification.
4. Then benchmark mature coding-agent / semantic Coding Hand candidates on the
   same bounded PC task.
5. Only after those gates, connect real cloud coder/reviewer providers through
   the already-existing Provider Vault / Reviewer Connector contracts.

Agent benchmarks are therefore planned, but the agent remains a replaceable
Hand under ORION authority rather than becoming the control plane.


## V3-RUN-019 Attempt ownership / lease / checkpoint / Stop

Status: **PHYSICAL PASS**

Exact tested V3 SHA:
`8388fb3f1b445be377c460defdd66a8010b198a4`

Remote staging SHA:
`aadf31b927ef439c91ba0f9d126277e541e7bc38`

Named-task session:
`11afb5138e9d`

Observed regression:
- **84 passed in 3.43s**

Observed Attempt ownership gate:
- Attempt creation: **PASS**
- one active execution lease: **PASS**
- second active claimant: **DENIED**
- checkpoint without current lease: **DENIED**
- expired lease advance: **DENIED**
- reclaim after expiry: **PASS**
- stale late worker/result after replacement: **DENIED**
- close/reopen recovery: **PASS**
- Stop invalidates ownership: **PASS**
- checkpoint/result after Stop: **DENIED**
- network/model execution dependency: **NONE**

This physically proves the first durable execution-ownership layer above the
existing low-level ActionLease primitive.

A WorkPackage still does not gain authority merely by existing or being reviewed.
Execution must belong to a durable Attempt, and only the current fenced lease may
advance checkpoint/result truth. A late worker may still physically finish work,
but ORION rejects its stale state transition.

### Current next priority

**V3-RUN-020 — isolated exact-SHA WorkPackage execution envelope**

Prove:
1. disposable Git worktree at the exact approved base SHA;
2. clean/identity checks before effects;
3. immutable WorkPackage reload by manifest/hash;
4. one harmless mechanically applied FILE/PATCH artifact;
5. only allowed paths changed;
6. exact diff/hash/evidence captured;
7. deterministic verifier passes;
8. Attempt lease/checkpoint ownership is used;
9. cleanup happens on PASS/FAIL/Stop;
10. no push/merge and no cloud/model dependency.

After that common envelope is physically proven, begin the PC coding-agent /
semantic Coding Hand benchmark on the same bounded task.


## V3-RUN-020 attempt 1 — authoring preflight lesson

Status: **FAIL — ARCHITECTURE NOT REACHED**

Remote staging SHA:
`d97373e49156a4fda941c248b2d13c51cc038895`

Session:
`1738e15e6d7f`

Observed:
- pytest collection stopped before RUN-020 execution-envelope behavior began;
- root cause was a malformed Python import containing literal escaped `\\n`
  sequences;
- this is classified as `AUTHORING_SYNTAX_ERROR`, not an execution-envelope
  architectural failure.

Promoted correction:
- added self-contained repository authoring preflight before V3 regression;
- added reusable in-core Python/JSON preflight;
- Coding Factory now preflights actual changed source before accepting verifier
  evidence;
- added a regression test for the exact escaped-newline failure class;
- recorded canonical lesson
  `FAILURE_LESSON-AUTHORING-SYNTAX-001`.

RUN-020 remains the current gate and must be rerun after this correction.
