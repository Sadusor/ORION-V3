# V3-RUN-015 — Canonical State / Memory Gate Physical PASS

Date: 2026-10-03

Status: **PHYSICAL PASS**

## Exact physical output

ORION-V3 regression:

```text
64 passed in 1.00s
V3_REGRESSION> PASS
```

State / Memory probe:

```text
DB_INIT> PASS
PROJECT_TASK_PERSISTENCE_SETUP> PASS
DETERMINISTIC_EVENT_HASH> PASS
EVENT_APPEND_ONLY_TRIGGER> PASS
CROSS_PROJECT_EVENT_PARENT> DENIED
MEMORY_WITHOUT_PROVENANCE> DENIED
CROSS_PROJECT_MEMORY_PROVENANCE> DENIED
FIRST_MEMORY_PROMOTION> PASS
MEMORY_SILENT_OVERWRITE> DENIED
EXPLICIT_MEMORY_SUPERSESSION> PASS
L0_PROJECT_SCOPE> PASS
L1_CURRENT_CANONICAL_SCOPE> PASS
L2_PROVENANCE_EXPANSION> PASS
CLOSE_REOPEN_PERSISTENCE> PASS
NETWORK_MODEL_DEPENDENCY> NONE
CANONICAL_STATE_MEMORY_GATE> PASS
STATUS> PASS
STATE_MEMORY_PROBE> PASS
STATUS> PASS
```

## Exact tested V3 SHA

`b800de5659ce74e3b52b88e41f4af53a5b6eacfd`

## What this physically proves

### Authoritative state

A fresh local SQLite database can persist projects, tasks, immutable events, and promoted canonical Memory.

### Append-only history

Event payload hashes are deterministic over canonical JSON.
SQLite triggers physically reject UPDATE and DELETE against the Event Ledger.

### Project isolation

Cross-project event-parent references are rejected.
Memory provenance from another project is rejected.
L0/L1 retrieval does not leak task or Memory state from another project.

### Memory Gate

Canonical Memory requires a real source Event.
A second current Memory record for the same project/kind/key cannot silently overwrite the previous record.
Changing canonical Memory requires explicit supersession: old row remains SUPERSEDED and the new row becomes CURRENT.

### Progressive retrieval

- L0 provides bounded orientation state.
- L1 returns bounded current canonical Memory.
- L2 expands exact immutable Event provenance including parent Event context.

### Persistence

Project/Event/Memory state survives database close and reopen.

### Dependency boundary

The gate required no network, model, Ollama, OpenMuse runtime, or KnowledgeOS runtime.
The authoritative state foundation is ORION-owned and stdlib/SQLite based.

## Donor principles preserved

From KnowledgeOS: SQLite authoritative; evidence/history separate from interpretation; semantic/vector indexes remain derived/rebuildable.

From OpenMuse: durable task/event thinking and future lease/checkpoint patterns.

Neither donor became ORION's authority layer.

## Architectural consequence

The continuity problem is no longer only a design document.
ORION now has a physically proven substrate for immutable history, current canonical Memory, explicit corrections/supersession, project-scoped context, and provenance.

This is the foundation for replacing GitHub-as-mailbox with a local exchange.

## Next gate

V3-RUN-016 should prove the local exchange protocol on top of this Event Ledger:

```text
TASK
 -> PROPOSAL
 -> REVIEW
 -> DECISION
 -> ACTION
 -> EVIDENCE
 -> RESULT
```

The test should prove causal parent chain, project/task scope, actor identity, idempotent external message ingestion, deterministic pending-work views, no event mutation, bounded exchange packet retrieval, restart/reopen continuity, and no GitHub requirement.

No real cloud AI is needed for the first exchange gate.
