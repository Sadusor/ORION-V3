# Decision 0002 — Separate ORION Core, Coding Factory and Computer Escalation

Date: 2026-10-03

Status: **ACCEPTED**

## Context

During V3.1 donor qualification, several concepts were being collapsed into one
"agent" architecture:

- the already-proven Coding Hands;
- the future autonomous cloud-AI coding loop;
- the lightweight daily assistant;
- the whole-PC GUI/computer-use agent;
- the final ORION interface.

That framing encouraged unnecessary primitive-Hand wrapping and risked making a
heavy agent the default path for simple commands.

## Decision

ORION Core is the shared authority/memory/task/evidence substrate.

The following remain distinct:

1. **Lightweight assistant** — Qwen semantic intent plus deterministic ORION
   capability/workflow routing and proven fast Hands.
2. **Coding Factory** — a workflow using replaceable cloud reasoning/review AIs,
   Qwen coordination where useful, and existing/qualified Coding Hands.
3. **Whole-PC Computer Hand** — explicit escalation for novel GUI work.
4. **ORION interface** — ORION-owned Jarvis-style product surface.

The Coding Factory is a workflow, not an ORION authority mode.

## Qwen boundary

Qwen may infer intent, entities and ambiguity.

Qwen does not:
- choose security/risk policy;
- mint permission;
- select arbitrary shell as the normal implementation;
- declare PASS;
- promote canonical Memory.

ORION deterministically resolves semantic intent to capability/workflow and
enforces authority.

## Capability Registry

ORION will maintain a semantic/policy Capability Registry.

This does not replace or duplicate donor ToolRegistries.

The registry maps stable semantic capability IDs to:
- typed parameters;
- effect/approval class;
- trusted scope;
- implementation binding;
- preconditions;
- Stop/evidence/postcondition contracts.

Known operations should use vetted implementations rather than model-generated
raw shell.

## Guard consequence

The guard is retained.

Routine friction should be reduced by validating semantic capabilities and typed
arguments rather than re-interpreting arbitrary PowerShell on every request.

Implementation-side pre-effect validation/containment and ORION post-effect
verification remain mandatory.

## Memory consequence

Canonical Memory and continuity move earlier in the roadmap.

Chat/model memory is not sufficient for project continuity.

PASS/FAIL records are evidence. Verified lessons/capabilities are promoted
through a Memory Gate.

## GitHub consequence

GitHub remains source control.

The live AI<->PC mailbox should eventually move to local canonical state plus an
append-only event log.

## V3-RUN-009 consequence

The staged V3-RUN-009 primitive OpenHands file-edit adapter is not the next
physical run.

It remains experimental reference code until/unless the capability architecture
needs it.

## Consequences

Positive:
- simple daily commands stay fast/cheap;
- agents are invoked only when their intelligence is useful;
- existing proven Hands are preserved;
- cloud models remain replaceable;
- guard logic becomes simpler and more auditable;
- memory becomes a first-class continuity mechanism.

Trade-offs:
- ORION must define a strong semantic capability contract;
- implementation bindings must be validated and versioned;
- memory promotion/retrieval quality becomes critical;
- whole-PC traces cannot be blindly promoted into trusted capabilities.

## Follow-up

1. Inventory legacy ORION Remote/V3/donor capabilities.
2. Define semantic Capability contract.
3. Harvest/register first capability pack.
4. Benchmark Qwen routing.
5. Implement canonical Memory and local event exchange.
6. Build Coding Factory workflow.
7. Add Whole-PC escalation later.
