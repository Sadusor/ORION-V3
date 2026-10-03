# ORION System Model — 2026-10-03 Architecture Freeze

Status: **AUTHORITATIVE DIRECTION**

This document freezes the architecture clarified on 2026-10-03 after the
OpenJarvis, OpenHands, OpenMuse and external-review audits.

The key correction is that ORION is **not one agent** and its Coding Factory is
**not the personal assistant**.

## North star

Models think and propose.
Hands execute.
ORION remembers, routes, authorizes, verifies and stops.

Models and Hands are replaceable. Canonical continuity belongs to ORION.

## ORION Core

ORION Core is the shared substrate used by every workflow and interface.

It owns:

- canonical Task / Attempt / Event state;
- canonical Memory and promotion;
- project registry and trusted bindings;
- semantic Capability Registry;
- deterministic policy / authority;
- approvals and Action Leases;
- routing and escalation;
- budgets and resource limits;
- evidence normalization;
- verification and PASS / FAIL truth;
- Stop / cancellation truth;
- local AI <-> Hand / cloud-AI exchange state;
- continuity across restarts, model changes and future years.

No model, donor agent, UI or Hand becomes an authority peer.

## Four distinct concepts

### 1. Lightweight personal assistant

This is the normal Jarvis-style daily path.

User request -> Qwen governor -> typed intent/entities -> ORION deterministic
policy -> known capability/workflow -> proven lightweight Hand -> evidence.

Examples:
- open/close an application;
- open a project;
- search a project;
- run tests;
- inspect GPU/RAM;
- start/stop Ollama;
- open a URL;
- check Git status;
- restart ORION.

The normal path must not start a heavy whole-PC agent merely to perform a known
operation.

Qwen does **semantic routing**, not implementation selection and not authority.

Qwen may decide:
- user intent;
- referenced entities;
- whether input is ambiguous;
- whether the request contains one intent or a composition;
- whether clarification/human escalation is needed.

ORION decides deterministically:
- which registered capability implements that intent;
- which implementation is currently preferred;
- whether the request authorizes the effect;
- scope / binding validity;
- approval requirements;
- availability;
- workflow validity;
- budgets.

Rule: **Qwen proposes; ORION disposes.**

Qwen should emit typed intent + parameters. It should not generate arbitrary
PowerShell as the normal control path.

### 2. Coding Factory workflow

The Coding Factory is a workflow that runs on ORION Core. It is not the
personal assistant and not a separate authority mode.

Current proven manual pattern:

strong chat AI -> GitHub transport -> legacy ORION Remote -> PowerShell/files/
tests on the owner's PC -> PASS/FAIL evidence -> strong AI reviews -> next turn.

The existing Coding Hands already prove that the PC can create/edit files, run
commands/tests and return evidence. The major remaining automation problem is
the reasoning/review loop around those Hands.

Target workflow:

1. Architect/reasoning cloud AI receives the task plus only relevant context.
2. It produces a proposal.
3. Reviewer/critic AI receives task + proposal + bounded context.
4. Reviewer accepts, corrects or requests another review.
5. Qwen3.5-9B acts as a lightweight coordinator/foreman where useful.
6. Existing Coding Hands execute locally.
7. ORION captures tests/diff/output/evidence.
8. Relevant evidence returns to the reasoning workflow.
9. The loop continues until the ORION verifier accepts the result or human help
   is required.

Free/cheap cloud AIs are replaceable reasoning sources. They do not receive PC
authority.

A mature coding agent such as OpenHands or Claude Code may itself be used as a
**semantic Coding Hand** when the input is high-level. Its internal agent loop
is an implementation detail inside a bounded coding step; it does not become
ORION Core.

When an external strong AI already produced an exact patch/commands, ORION
should prefer deterministic execution instead of paying for another agent to
re-reason the work.

### 3. Whole-PC Computer Hand

This is an escalation Hand for novel GUI/desktop work that cannot be expressed
as a known capability or workflow.

Examples:
- unfamiliar accounting software;
- visual workflows with no API;
- arbitrary desktop interaction;
- UI recovery that requires perception.

It may inspect the screen, click, type and recover from UI changes.

It is **not the normal assistant brain** and not the boss. ORION invokes it only
after lower-cost deterministic capabilities/workflows are insufficient.

Successful repeated whole-PC behavior may later become a deterministic
capability/workflow, but successful traces are only evidence. Promotion requires
independent verification and policy/human approval.

### 4. ORION interface

The final main experience is ORION-owned and should use publicly observable
jarvis.institute product/UX ideas where useful:

- central ORION/Jarvis visual;
- Ready / Thinking / Running / Waiting / Approval states;
- chat and later voice;
- visible conclusions and activity;
- task timeline;
- status and evidence;
- minimal daily surface with deeper panels when needed.

Stanford OpenJarvis UI/runtime code is donor infrastructure, not the final
product identity.

## Semantic Capability Registry

The Capability Registry is an ORION semantic/policy registry.

It is **not** a second low-level tool registry competing with OpenJarvis
ToolRegistry.

OpenJarvis ToolRegistry or another donor may still hold concrete tool
implementations. ORION Capability Registry maps stable semantic capabilities to
policy metadata and one or more vetted implementations.

Each capability should define at minimum:

- `id`;
- description / intent;
- typed parameter schema;
- effect class;
- approval class;
- allowed scopes / trusted-binding requirements;
- candidate implementation(s);
- preconditions;
- Stop contract;
- evidence contract;
- postconditions;
- availability/health probe;
- version / provenance.

Example:

```text
intent: app.open
params: { app: "chrome" }

ORION capability: app.open
policy: low-risk / direct user request sufficient
implementation: trusted application registry -> exact executable launch
evidence: process/window observed
```

Qwen never needs to know `Start-Process`.

## Guard redesign

Do not remove the guard. Move the normal authority decision away from arbitrary
shell syntax.

Old path:

model -> raw shell text -> guard must understand arbitrary command -> allow/block

Target path:

Qwen -> typed intent -> ORION Capability Registry -> deterministic policy ->
vetted implementation -> evidence verification

A registered name is not automatically safe.

Every implementation must enforce its contract before side effects:
- validate typed inputs;
- resolve targets from trusted bindings/registries;
- avoid untrusted shell interpolation;
- reject scope widening;
- use containment where appropriate.

ORION then validates the postcondition/evidence after execution.

Security requires both:
1. pre-effect contract enforcement / containment;
2. post-effect verification.

## Initial approval/effect model

Keep the taxonomy small and practical.

- Class 0 — read-only / observational.
  Direct user request is sufficient.
- Class 1 — reversible routine effect.
  Direct, unambiguous user request is normally sufficient.
- Class 2 — bounded modification.
  Parent Task / Action Lease may authorize the bounded work without prompting
  for every internal operation.
- Class 3 — consequential / destructive / external.
  Requires stronger explicit scope/approval unless the user's exact direct
  request itself is the unambiguous approval for that exact effect.

Do not ask redundant questions such as:
"You asked me to open Chrome. May I open Chrome?"

## Deterministic escalation ladder

Prefer the cheapest sufficient rung.

1. Exact registered capability.
2. Known registered workflow.
3. Small deterministic composition of registered capabilities.
4. Single bounded cloud reasoning step for analysis/research.
5. Coding Factory workflow for project-development work.
6. Whole-PC Computer Hand for GUI/novel work that cannot be expressed below.

Escalation requires the lower rung to be unavailable or insufficient.

## Existing Hands vs future agents

The proven legacy ORION Remote remains useful.

Its current PowerShell/file/test/Git/project mechanics should be harvested into
semantic capabilities instead of thrown away.

A high-level model should normally select:
`project.run_tests`, `app.open`, `orion.restart`, etc.

The implementation can reuse the already-proven legacy scripts/PowerShell
mechanics, OpenJarvis tools, native Windows APIs or another stronger donor.

A heavy agent is an escalation path, not the default implementation for a
known command.

## Capability promotion

Do not neural-train Qwen on raw successful traces.

Learning means promoting verified experience into reusable policy/memory.

Candidate flow:

agent/workflow succeeds -> store immutable evidence -> repeated success on the
same task class -> deterministic extraction -> candidate capability/workflow ->
test against prior cases -> contract/scope review -> human/policy approval ->
registry promotion.

A successful trace is evidence, not trusted code.

Do not promote tasks that still depend on:
- unstable UI layout;
- visual judgment;
- human judgment;
- highly variable external data;
- non-deterministic interpretation that cannot be represented safely.

## Canonical Memory

Memory is a central ORION capability, not optional model chat history.

Required memory classes:

- `PROJECT_FACT`
- `DECISION`
- `CURRENT_STATE`
- `FAILURE_LESSON`
- `CAPABILITY`
- `EVIDENCE` references
- `USER_PREFERENCE`
- `RAW_HISTORY` / exchange events

Only promoted, provenance-backed facts/lessons become canonical.

PASS/FAIL records are evidence. They are never automatically treated as truth
or training examples.

Useful promotion checks include:
- provenance to a Task/Attempt and verifier;
- correlation/deduplication;
- contradiction detection;
- explicit promotion decision.

## Progressive context retrieval

Do not dump all history into every model.

Target levels:

- L0 — tiny index/summary;
- L1 — compact relevant state/lesson/decision;
- L2 — detailed evidence/artifacts only when required.

Project/task scope is a hard filter.

Qwen should usually receive L0 + a small relevant L1 set.
Strong cloud reviewers receive targeted L1/L2 only as needed.

A core acceptance query is:

`project_id -> reconstruct enough current state to resume work correctly after months/years`.

## Local exchange replacing GitHub transport

GitHub remains source control.

It should eventually stop being the live mailbox between cloud reasoning and
the local PC.

Use an append-only event log in ORION's local database rather than creating a
new network service.

Minimum conceptual event:

```text
event_id
task_id
attempt_id
event_type
actor
actor_kind
created_at
content_hash
content_ref
parent_event_id
status
```

Initial event types:
- PROPOSAL
- REVIEW
- DECISION
- ACTION
- EVIDENCE
- RESULT

Events are immutable. Corrections/supersession create new events.

Cloud AI adapters may submit only validated event schemas. They do not receive
arbitrary database access.

GitHub remains responsible for source code, commits, branches, tags, PRs and
optional CI/release state.

ORION local state remains canonical for task/attempt/event state, permissions,
approvals, project bindings, Memory, evidence, capability registry and AI
exchange.

## Donor roles after the architecture correction

### Stanford OpenJarvis
Reuse selectively:
- ToolRegistry / ToolExecutor;
- WorkflowEngine where compatible;
- engines/provider plumbing;
- useful built-in tools;
- frontend/runtime components.

Do not make its autonomous agents the ORION control plane.

### OpenMuse
Strong donor for the ORION middle/execution durability layer:
- SQL task leases;
- durable workers;
- checkpoints/recovery;
- pause/resume/cancel;
- idempotent operations/receipts;
- bounded model loop patterns;
- task/activity UX;
- isolated computer patterns.

OpenMuse is a worker/durability donor, not ORION's routing authority.

### OpenHands / Claude Code
Candidates for semantic Coding Hands when a high-level coding task requires an
internal coding loop.

Do not rebuild their editor/terminal/agent sequencing if a candidate passes the
ORION benchmark and containment/verification contracts.

### jarvis.institute
Product/UX inspiration only. Publicly observable behavior can inspire ORION's
interface and workflow experience; proprietary source is not treated as a code
donor.

### KnowledgeOS and memory donors
Primary focus for canonical memory, evidence/provenance, retrieval and
long-term project continuity.

## Current experimentally proven facts

- OpenJarvis remains a replaceable substrate under ORION authority.
- V3-RUN-007 physically proved a deterministic OpenJarvis WorkflowEngine path
  under an ORION lease with no autonomous agent loop.
- V3-RUN-007 physically proved Qwen3.5-9B can perform a one-shot routing task:
  1 turn, 0 tools, 130 prompt tokens, 3 completion tokens, 133 total tokens,
  approximately 4.57 seconds, correct route.
- V3-RUN-008 physically proved OpenHands FileEditor and Windows Terminal are
  strong Hands without running the OpenHands agent.
- The OpenHands tool environment is too dependency-heavy to make an always-
  loaded ORION core dependency.
- Legacy ORION Remote remains the proven execution/transport fallback.

## V3-RUN-009 disposition

`V3-RUN-009` was staged to wrap one OpenHands primitive file-edit operation
behind ORION authority.

**DO NOT EXECUTE IT AS THE NEXT PRIORITY.**

Reason:
the architecture was corrected before execution. Continuing to wrap primitive
coding commands one by one risks recreating the command-sequencing problem that
mature coding agents/Hands already solve.

The staged code may remain as experimental evidence/reference until later
cleanup. It is not the current architectural direction.

## Immediate implementation priority

1. Inventory proven capabilities already present in legacy ORION Remote, V3,
   OpenJarvis and native Windows/PowerShell.
2. Define one stable semantic Capability contract.
3. Register/harvest a substantial first batch rather than teaching commands one
   at a time.
4. Build a Qwen routing benchmark over natural-language requests -> typed
   intent/parameters.
5. Design/implement canonical Memory + append-only local event exchange.
6. Build the cloud-AI Coding Factory workflow around existing Coding Hands.
7. Add Whole-PC Agent escalation after the lower-cost paths are stable.
8. Continue the ORION-owned Jarvis-style UI on top of the shared core.

## Non-negotiable rule

**Known task -> Qwen + registered capability/workflow.**

**Complex coding/project development -> Coding Factory + existing/qualified
Coding Hands.**

**Unknown/visual desktop task -> Whole-PC Computer Hand.**

**Everything -> ORION canonical Memory, evidence and continuity.**
