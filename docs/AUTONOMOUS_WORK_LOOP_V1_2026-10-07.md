# ORION V3 — Autonomous Work Loop V1

Date: 2026-10-07  
Status: **OWNER-LOCKED DIRECTION / CURRENT PRIORITY**  
Implementation rule: **smallest physical proof -> PASS -> freeze -> extend**

## Goal

Remove the owner from the repetitive task-router/context-reminder role while preserving ORION authority and real evidence.

Target first loop:

```text
Owner: Continue
  -> read project Vault / STATE.md
  -> local model proposes one bounded task
  -> ORION classifies GREEN / YELLOW / RED
  -> confined Work Hand executes
  -> real evidence verifies FAIL/PASS
  -> ORION updates STATE/JOURNAL
  -> continue
```

The project folder is the **Vault**. `STATE.md` is the canonical current-state/front-page file. Existing ORION Memory remains separate reusable durable knowledge.

## Locked principles

1. ORION owns authority, state transitions, evidence acceptance and STOP.
2. Models reason/propose; they never authorize themselves or declare verified PASS.
3. Hands execute; they do not become authority.
4. Real authenticated evidence determines execution truth.
5. Autonomous writes require physically proven workspace confinement.
6. GREEN proceeds autonomously; YELLOW waits for owner; RED/frozen operations are denied before Hands.
7. Existing ORION STOP remains authoritative.
8. Vault owns project continuity; model hidden state does not.
9. Models/providers remain replaceable.
10. Round-3 design is a target direction, not a frozen component specification; physical evidence may falsify future component hypotheses.
11. Do not create duplicate Memory, evidence, STOP, event, project-state or chat systems.
12. Reuse existing ORION/TheHands/donor code before building new mechanisms.

## Immediate roadmap

### 0 — Audit + donor reuse map — CURRENT

No implementation until actual code is inspected and classified `EXISTS / PARTIAL / MISSING / REUSE`.

Inspect ORION-V3 + TheHands for Vault/project state, Qwen invocation, Hands invocation, evidence, STOP, risk/frozen checks, Git, owner-input hook, status/events and workspace confinement.

### 1 — Minimal Vault

Disposable Work project:

```text
<project>/
  STATE.md
  JOURNAL.md
  repo/
```

STATE contains only current project state. JOURNAL is append-only. Durable reusable lessons remain candidates for the existing Memory pipeline rather than accumulating into a shadow memory.

### 2 — Confined Work Hand

Prove the Hand cannot write outside the assigned workspace. Audit existing TheHands first, then existing confinement donors/runtime mechanisms. If not proven, remain read-only/dry-run.

### 3 — Tiny loop

Build only `STATE -> model -> ORION -> Hands -> evidence -> STATE`, with a per-cycle owner-instruction hook.

### 4 — FAIL across restart qualification

One path must prove: one owner Continue; correct STATE; bounded proposal; GREEN autonomous execution; deliberate authenticated FAIL; kill/restart before repair; fresh Qwen repairs without owner reminder; authenticated PASS; STATE/JOURNAL update; YELLOW waits; frozen/RED denied before Hands; existing STOP halts; owner can watch the real cycle live.

### 5 — Model replacement

Swap Qwen for another compatible local model and continue from the same Vault/evidence before adding enrichment.

### 6 — Existing Memory integration

Use frozen ORION Memory only as context enrichment. Do not reopen Memory V1/V1.1.

### 7 — Separate Work Chat

Reuse existing ORION chat infrastructure for project-scoped Work Chat. Normal Chat remains separately usable.

### 8 — Qualified Skills

First candidates: repo/code search, docs/research retrieval, Git/project inspection. Qwen requests; ORION authorizes.

### 9 — Cloud specialists

Add Architect + Adversarial roles using replaceable existing provider infrastructure.

### 10 — Work observability/UI

Build around real observed events and needs: Chat, Activity, Plan, Council, Files/Vault, Evidence.

### 11 — Headless + notifications

Same loop detached; minimal owner-needed notifications. Routine GREEN stays quiet.

### 12 — Phone supervision

Status, Work Chat, Activity, evidence, decisions, Pause/Resume/STOP.

### 13 — Extended qualification + freeze

Longer continuity, model/provider replacement, confinement attacks, YELLOW/RED, detach/attach, Pause/Resume, STOP, evidence. Freeze Autonomous Work Loop V1 after physical PASS.

### 14 — Real ORION task

Use the frozen loop on one small non-protected ORION task.

## First qualification PASS contract

All must pass in one bounded qualification:

1. Owner says Continue once.
2. Correct STATE is read.
3. Qwen proposes a bounded task.
4. ORION classifies from concrete properties.
5. GREEN runs without owner approval.
6. Hands stays inside the proven workspace.
7. Real evidence authenticates deliberate FAIL.
8. ORION is killed before repair.
9. Fresh Qwen resumes from Vault/evidence without owner reminder.
10. Repair executes and real evidence authenticates PASS.
11. STATE updates; JOURNAL appends.
12. YELLOW waits for owner.
13. Frozen/RED write is denied before Hands.
14. Existing ORION STOP halts the loop.
15. Owner can observe the real cycle live from one simple view.

A PASS proves only this bounded claim; it does not prove multi-day, multi-project or self-development autonomy.

## Donor reuse priority

### Use now / inspect first

- **Existing TheHands** — execution/evidence and possible existing scope enforcement. First place to inspect for confinement; do not fork the frozen core.
- **OpenMuse + Jev Harness** — frozen proposal hashes, stale-choice rejection, idempotency/receipts and evidence-grounded proposal/approval semantics.
- **CLI-Anything** — deterministic one-operation Hand shape, JSON receipts, inspect-before-mutate and real artifact verification.
- **OpenSandbox** — isolation/mount/network patterns as a confinement challenger if existing TheHands/Windows mechanisms are insufficient. Do not adopt a sandbox platform before the audit proves it is needed.
- **Aider repo-map** — strong candidate for the first read-only code-search/context Skill: compact symbol-aware repository context.
- **KnowledgeOS** — provenance/evidence-vs-interpretation patterns; reuse concepts without creating a second evidence store.

### Use after the core loop proves itself

- **OpenJarvis** — tool/skill registries, capability vocabulary, event adapters and skill manifests. Its current upstream also has sandbox/mount and skill trust/capability patterns; ORION must remain authority and fail-closed.
- **Graft / codebase-memory-mcp** — challengers if Aider repo-map is insufficient for code context.
- **WORKSHOP / OpenJarvis provider patterns** — later replaceable cloud provider mapping/health.
- **PizzaBot / KIRA / Orion-Copilot** — later needs-owner/background-work and phone-supervision UX.

### Explicitly do not import

- donor agent authority;
- donor canonical memory/project truth;
- default-allow security policy;
- a second evidence database;
- a second STOP;
- a second chat system;
- a generic workflow framework before the tiny loop demonstrates need.

## Current donor findings

The existing ORION donor audit already records:
- OpenMuse exact/frozen proposal and receipt patterns;
- CLI-Anything deterministic Hand/evidence shape;
- OpenJarvis registries/capabilities/events;
- Aider repo-map bounded code context;
- KnowledgeOS evidence/provenance separation.

Current upstream OpenJarvis additionally documents a mature Skills system (manifest/parser/manager/executor, dependency-cycle/depth checks, capability unions, trust tiers) and sandbox wrappers with mount allowlists. These are useful **later**, not reasons to replace the tiny V1 loop.

Aider's repo-map remains particularly attractive for the first Skill because it builds compact repository context from important symbols and relationships rather than dumping the whole repository.

## Priority rule

Until the first autonomous-loop qualification passes, new work should serve this roadmap unless the owner explicitly changes priority.

When a test reveals a missing capability, first ask:

1. Does ORION already have it?
2. Does TheHands already have it?
3. Does an audited donor provide a narrow reusable implementation/pattern?
4. Only then build new code.

Borrow capability, not ownership.
