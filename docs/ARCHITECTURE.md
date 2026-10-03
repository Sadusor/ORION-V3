# ORION V3 Architecture

## North Star

ORION V3 is a persistent personal AI control plane assembled from replaceable mature components.

Stable principle:

**Models think and propose. Hands act. ORION remembers, routes, authorizes, verifies and stops.**

The authoritative expanded system model is:
`docs/ORION_SYSTEM_MODEL.md`.

## Core layering

```text
USER
  -> ORION interface
      -> ORION Core
          -> semantic intent / task state / memory
          -> deterministic policy + Capability Registry
          -> capability / workflow / specialist escalation
          -> Hands / agents / donors
          -> evidence
          -> verifier
          -> PASS/FAIL + Memory Gate
```

## ORION Core

ORION owns:
- canonical Task / Attempt / Event truth;
- canonical Memory;
- project registry and trusted bindings;
- semantic Capability Registry;
- deterministic routing/policy;
- PermissionGrants and Action Leases;
- approvals and budgets;
- evidence normalization and verification;
- Stop/recovery truth;
- local AI/cloud-AI exchange state;
- continuity across restarts and model replacement.

No donor, model, Hand, agent or UI is a co-authority.

## Qwen governor

Qwen3.5-9B is the leading lightweight governor candidate.

Qwen may:
- interpret intent;
- extract entities/parameters;
- detect ambiguity;
- propose a small composition;
- package relevant context;
- suggest human escalation.

Qwen may NOT:
- mint authority;
- choose risk policy;
- widen scope;
- select arbitrary shell as the normal path;
- declare a side effect successful;
- promote canonical Memory.

Rule:

**Qwen proposes; ORION disposes.**

## Semantic Capability Registry

The ORION Capability Registry is a semantic/policy registry, not a duplicate
low-level tool registry.

A capability defines:
- stable semantic ID;
- typed parameters;
- effect/approval class;
- trusted scope requirements;
- implementation binding(s);
- preconditions;
- Stop contract;
- evidence contract;
- postconditions;
- provenance/version.

OpenJarvis ToolRegistry or another donor may still own concrete tool
implementations underneath.

Known request flow:

```text
user -> Qwen typed intent -> ORION capability resolution/policy
     -> vetted implementation -> evidence -> verifier
```

## Guard

Do not remove the guard.

Routine guard friction is reduced by authorizing semantic capabilities instead
of asking policy to understand arbitrary shell syntax.

Security requires:
1. implementation-side validation/containment before effects;
2. ORION evidence/postcondition verification after effects.

Registration alone never grants authority.

## Execution paths

### Lightweight assistant

Normal daily path:
Qwen -> known capability/workflow -> proven lightweight Hand.

Do not launch a heavy agent for a known operation such as open/close/status/
search/test/restart.

### Coding Factory

The Coding Factory is a workflow on ORION Core, not the personal assistant.

Target:
cloud architect/reviewer AIs -> Qwen coordinator where useful -> existing or
qualified Coding Hands -> local project -> tests/diff/evidence -> review loop.

Cloud AIs reason; they do not directly own PC authority.

A mature coding agent may be used as one semantic Coding Hand when high-level
coding work requires an internal loop.

### Whole-PC Computer Hand

Escalation only for novel GUI/desktop tasks that cannot be expressed as a known
capability/workflow.

It may internally be agentic, but ORION owns the envelope, Stop, evidence and
acceptance.

## Deterministic escalation ladder

1. Exact capability.
2. Known workflow.
3. Small deterministic composition.
4. Single bounded cloud reasoning step.
5. Coding Factory for project-development work.
6. Whole-PC Computer Hand for novel GUI work.

Escalation requires lower-cost rungs to be unavailable or insufficient.

## OpenJarvis substrate

OpenJarvis remains a replaceable infrastructure donor for:
- ToolRegistry / ToolExecutor;
- WorkflowEngine where compatible;
- engines/provider plumbing;
- channels/connectors;
- useful built-in tools;
- frontend/runtime components.

OpenJarvis agents do not become the ORION control plane.

## Evidence / verification

Hand/agent output is not automatically success.

Expected outcomes:
- confirmed
- unverifiable
- refused
- failed
- stopped
- blocked

Agent-declared “done” is a proposal. ORION verification decides PASS/FAIL.

## Stop

Timeout != Stop.

ORION reports STOPPED only after underlying owned work actually terminates or
equivalent cancellation is verified.

## Memory

Canonical Memory remains ORION-owned.

Target classes:
- PROJECT_FACT
- DECISION
- CURRENT_STATE
- FAILURE_LESSON
- CAPABILITY
- EVIDENCE reference
- USER_PREFERENCE
- RAW_HISTORY/event log

PASS/FAIL is evidence, not automatic training data.

Retrieval is progressive:
L0 summary -> L1 compact context -> L2 detailed evidence.

## Local exchange

GitHub remains source control.

Live cloud-AI <-> ORION <-> Hands coordination should eventually use an
append-only local event log rather than GitHub as a mailbox.

Initial event types:
PROPOSAL, REVIEW, DECISION, ACTION, EVIDENCE, RESULT.

## UI

The final ORION interface is ORION-owned and may reuse selected donor
infrastructure.

Publicly observable jarvis.institute behavior/UX is product inspiration:
central visual state, chat/voice, activity, conclusions, approvals and timeline.

Stock OpenJarvis desktop is not the final ORION product.

## Default routine flow

```text
owner
 -> Qwen semantic intent
 -> ORION deterministic capability/policy
 -> proven Hand
 -> evidence
 -> verifier
 -> memory/state
```

Complex coding and whole-PC work are explicit escalation paths, not the default.
