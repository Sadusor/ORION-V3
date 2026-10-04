# Decision 0014 — Build ORION-Native Agent V0

Date: 2026-10-04  
Status: OWNER-APPROVED DIRECTION / IMPLEMENTATION STARTED  
Authority effect: none until physical qualification

## Decision

Build a deliberately small ORION-native agent loop instead of adopting a third-party agent framework as ORION's execution authority.

The agent is a bounded reasoning/execution gear inside ORION:

```text
Owner
  ↓
ORION task + scope + policy
  ↓
Model proposes ONE structured action
  ↓
ORION validates
  ↓
ORION Hand executes
  ↓
normalized observation + Journal
  ↓
model proposes next action
```

The loop may repeat until DONE, FAIL, ASK_OWNER, ESCALATE_MODEL, STOP, or a budget boundary.

## Why now

ORION already owns most of the difficult system boundaries:

- owner authorization;
- task identity;
- exact project/scope binding;
- deterministic Hands;
- capability registry;
- Evidence Packs;
- STOP architecture;
- persistent state and provenance;
- Memory architecture;
- cloud reviewer/provider plumbing;
- phone/Remote control;
- project linking;
- protected baseline preservation.

The missing capability is not a new control plane. It is a small bounded iterative loop.

External DeepSeek review independently reached the same verdict: **BUILD ORION AGENT V0**, while warning that scope creep is the main implementation risk.

## Non-goal

Do not build another general agent framework.

Agent V0 is not intended to reproduce:

- DeepSeek Harness;
- OpenHands;
- Octop;
- AutoHarness;
- Google ADK;
- arbitrary autonomous multi-agent orchestration.

Those remain donors, competitors, or specialist substrates.

## Routing hierarchy

Normal ORION execution should remain:

```text
DIRECT DETERMINISTIC HAND
        ↓ if insufficient
KNOWN WORKFLOW / QUALIFIED SKILL
        ↓ if insufficient
ORION AGENT V0
        ↓ if insufficient
STRONGER MODEL / HUMAN
```

The existence of Agent V0 must not make ordinary tasks agentic.

Examples:

- open Chrome → direct Hand;
- publish an exact file → deterministic capability;
- known release preparation → qualified workflow/Skill;
- explore unfamiliar repo + diagnose + edit + retest → Agent V0 candidate.

## Authority split

### Model owns

- interpretation;
- hypotheses;
- next-action proposals;
- explanatory reason;
- optional self-reported confidence;
- terminal suggestion (DONE/FAIL/ASK_OWNER/ESCALATE_MODEL).

### Agent loop owns

- sequential state machine;
- bounded context assembly;
- delivery of observations;
- counters/budgets;
- terminal loop state.

### ORION owns

- available tool/Hand set;
- actual permissions;
- canonical target resolution;
- approved root;
- network policy;
- owner confirmation policy;
- idempotency semantics;
- state/snapshot binding;
- STOP;
- process ownership;
- evidence;
- sandbox;
- promotion into real project state;
- Memory promotion;
- Skill qualification.

Model confidence is telemetry only. It never grants authority.

## Minimum Agent V0

V0 contains only:

1. Task State.
2. Context Builder.
3. replaceable Model Adapter.
4. strict Action Proposal schema.
5. ORION Policy Gate.
6. task-scoped frozen Hand Registry.
7. Executor.
8. Observation Normalizer.
9. append-only hash-chained Journal.
10. budgets.
11. external STOP hook.
12. Terminal Result.

One action is proposed and executed at a time.

## V0 proposal shape

```json
{
  "step_id": 1,
  "state": "continue",
  "action": "read_file",
  "target": "src/auth.py",
  "parameters": {},
  "reason": "inspect current implementation",
  "expected_effect": "read",
  "idempotency_key": null,
  "confidence": 0.72,
  "expected_state_hash": "..."
}
```

Extra fields are rejected.

The proposal is advice/data until ORION validates it.

## Failure semantics

Execution distinguishes:

```text
NOT_STARTED
STARTED
COMPLETED
FAILED
CANCELLED
OUTCOME_UNKNOWN
```

`OUTCOME_UNKNOWN` means ORION cannot determine whether a material effect committed.

It must not be blindly retried.

Timeout alone is not automatically `OUTCOME_UNKNOWN`; executor evidence determines that state.

## Deliberately deferred

V0 has no:

- subagents;
- parallel tool calls;
- model-written workflows;
- arbitrary `run_code`;
- dynamic tool registration;
- generic unrestricted shell;
- Skill invocation;
- mid-loop Memory retrieval;
- model-selected permission expansion;
- persistent cross-restart conversation;
- background-job semantics;
- multi-model routing.

Each deferred feature gets a named extension seam but no authority.

## Reserved future seams

Implementation reserves replaceable interfaces for:

- `MemoryContextProvider`;
- `SkillProvider`;
- `SecurityAdvisor`;
- `SandboxProvider`;
- `EscalationProvider`.

These exist so later work can plug in without rewriting the V0 authority boundary.

An interface existing does not mean the capability is enabled.

## Sandboxed coding

Coding adopts the previously accepted principle:

**approve the box, not every movement inside the box.**

Expected unattended shape:

```text
HOST
  ORION authority
  STOP
  evidence
  promotion gate
       ↓
OUTER DISPOSABLE SANDBOX
       ↓
ORION Agent V0
       ↓
bounded Hands / qualified Skills
       ↓
candidate patch + tests
       ↓
ORION verifies exact diff
       ↓
owner / pre-approved promotion policy
```

The coding agent never promotes its own sandbox changes into protected state.

## Personal Assistant relationship

The same ORION authority model governs the Personal/Desktop Assistant, but the Personal lane acts against the real machine and therefore remains more conservative.

- GREEN: low-risk read/open/search/navigation.
- YELLOW: material writes, downloads, installs, external side effects, unusual sensitive scope.
- RED: system/security/credentials/ORION authority/STOP changes by default denied.

The model may warn about risk, but the deterministic capability boundary is authoritative.

## Skills relationship

Learned/reusable skills are qualified capabilities, not remembered authority.

Future skill lifecycle:

```text
successful workflow
  ↓
candidate skill
  ↓
ORION qualification
  ↓
version/hash/scope/policy metadata
  ↓
Skill Registry
  ↓
task-scoped exposure to model
```

Changed skill versions do not inherit trust automatically.

## DeepSeek Harness relationship

DeepSeek Harness remains:

- donor/reference;
- A/B/C benchmark competitor;
- possible fallback/specialist substrate.

It does not become ORION authority.

Its first qualification path, if run, remains headless + native tools + outer ORION-owned isolation.

## Security donor relationship

### Google Mantis

Primary secure-coding/sandbox/verification donor.

Useful patterns:

- deterministic harness owns control flow;
- immutable snapshot-per-pass;
- target read-only / private shadow writes;
- snapshot/content hashes;
- state provenance;
- threat modeling;
- reproduce → patch → independent re-attack;
- sandbox abstraction;
- gVisor / stronger VM options;
- active isolation probes;
- evidence-first vulnerability status;
- security knowledge learned from prior verified findings;
- deterministic budgets and resumable state.

Mantis is not ORION authority and is not installed wholesale by this decision.

### ButterClaw

Primary runtime security-policy/process-monitor donor.

Useful patterns:

- positive capability matrix;
- fail-closed missing capability metadata;
- pre-model/post-model/pre-tool deterministic policy stages;
- bounded chain length;
- policy events;
- process lineage/quarantine concepts;
- transport/payload constraints;
- live-fire adversarial tests.

Static signatures are defense-in-depth only, never the primary boundary.

### Google mcp-security

Security-tool/MCP contract donor and possible future external security intelligence integration.

Do not make paid Google SecOps/SOAR/SCC services required for ORION base safety.

### Athena Investigation MCP

Narrow-capability donor.

Core lesson:

**publish a small typed capability instead of generic privileged backend access.**

### AgenticAnomaly

Indirect prompt-injection benchmark donor.

Use it to improve adversarial fixtures, not as runtime authority.

## Benchmark direction

After the foundation and Qwen adapter are physically qualified, compare:

```text
A — same Qwen -> ORION -> deterministic Hands

B — same Qwen -> ORION Agent V0 -> same Hands

C — same Qwen -> DeepSeek Harness headless -> ORION guard -> equivalent Hands
```

Same machine, model, project snapshot, task and equivalent permissions.

Hard security failures cannot be averaged away by speed.

## Development discipline

Build in slices.

1. Schema + Journal.
2. Model adapter/context.
3. Policy gate.
4. read Hand.
5. sequential loop.
6. write Hand.
7. bounded test/build Hand.
8. safe adversarial cases.
9. resource budgets + physical STOP/process-tree proof.
10. A/B/C benchmark.

Do not move to a larger feature set merely because code exists.

## Current implementation status

The first foundation code has been written in the legacy ORION development repository under:

`spikes/coding_mode_github_loop/orion_agent_v0/`

It is currently **GITHUB-CODED / UNVERIFIED** on the target Windows machine.

No production promotion is implied.

## Post-benchmark decision

After the benchmark, the owner will decide what direction ORION should take next.

The next architecture phase is intentionally not pre-decided.

The benchmark is meant to inform a fresh owner + assistant brainstorming session.
