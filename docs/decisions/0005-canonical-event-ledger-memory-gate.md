# Decision 0005 — Canonical Event Ledger and Memory Gate

Date: 2026-10-03

Status: **ACCEPTED FOR PHYSICAL QUALIFICATION**

## Problem

ORION cannot rely on model/chat memory for project continuity.

A replacement model must be able to resume a project months or years later and
recover:
- what the project is;
- current state;
- accepted architecture decisions;
- what physically passed/failed;
- why an approach was rejected;
- known capabilities;
- open questions;
- the next bounded action.

Raw history alone is not sufficient, and raw PASS/FAIL must not automatically
become trusted knowledge.

## Donor findings

### KnowledgeOS

Source-read at:
`Sadusor/KnowledgeOS@e9e5b9834d971f1f3fc92e41658069ac0fb5735f`

Useful proven design principles:
- SQLite KnowledgeItems/Evidence are authoritative;
- FAISS/vector maps and regions are derived state;
- Evidence stores factual observations;
- interpretation/understanding is separate from Evidence;
- deterministic retrieval is preferred in the core;
- local-first persistence;
- derived indexes may be rebuilt from authoritative state.

ORION should borrow those principles, not reuse KnowledgeOS's file-oriented
KnowledgeItem schema as its control-plane database.

### OpenMuse

Source-read at:
`Sadusor/openmuse@b06caad7005ac5b6d2b451752a3794a6ae1759c1`

Useful patterns:
- compare-and-swap task ownership;
- lease IDs and lease expiry;
- checkpoint only while lease is still owned;
- append task/run events;
- interruption/recovery semantics;
- lost lease aborts active execution.

ORION should adapt these durability semantics while keeping ORION authority and
evidence contracts canonical.

## Decision

ORION Core will use one local authoritative database with three conceptual
layers:

1. **Mutable operational state**
   - projects;
   - tasks;
   - attempts/leases;
   - current task status.

2. **Immutable append-only Event Ledger**
   - proposals;
   - reviews;
   - decisions;
   - actions;
   - evidence references;
   - results;
   - failures;
   - memory-promotion events.

3. **Promoted canonical Memory**
   - project facts;
   - decisions;
   - current state;
   - failure lessons;
   - capability knowledge;
   - user/project preferences;
   - evidence references.

Vector/embedding indexes are derived accelerators only. They never become
canonical truth.

## Event rule

Events are immutable after append.

A correction never rewrites an old event. It appends a new event that references
or supersedes the previous event.

Every event stores:
- event ID;
- project ID;
- optional task/attempt IDs;
- event type;
- actor kind/ID;
- timestamp;
- payload;
- payload hash;
- optional parent event ID.

## Memory Gate

No raw model statement or run result automatically becomes canonical Memory.

Promotion requires:
- provenance to an immutable event;
- explicit memory kind/key;
- promoted value/summary;
- promotion actor;
- optional supersession of a previous canonical record;
- no silent overwrite.

A conflicting/current record must be superseded explicitly.

PASS/FAIL remains Evidence until a lesson/fact is deliberately promoted.

## Memory classes

Initial classes:
- PROJECT_FACT
- DECISION
- CURRENT_STATE
- FAILURE_LESSON
- CAPABILITY
- EVIDENCE_REF
- USER_PREFERENCE

RAW_HISTORY remains in the Event Ledger rather than being copied into canonical
Memory.

## Retrieval rule

Progressive retrieval:

- L0 — tiny current index/summary;
- L1 — compact relevant canonical records;
- L2 — source events/evidence only when required.

Project scope is a hard boundary.

Initial retrieval should be deterministic:
project + memory kind + key/tag + recency/current state.

Semantic/vector retrieval may be added later as a derived index using
KnowledgeOS patterns.

## GitHub rule

GitHub remains source control.

The Event Ledger is the future live AI<->ORION exchange and must not depend on
GitHub commits as message transport.

## Next physical experiment

V3-RUN-015 will prove a minimal local SQLite Event Ledger + Memory Gate:

- project/task scope isolation;
- append event;
- deterministic payload hash;
- no event update API;
- explicit memory promotion from a real event;
- no silent overwrite;
- explicit supersession;
- project-scoped L0/L1/L2 retrieval;
- event provenance expansion;
- persistence across close/reopen.

No embeddings, LLMs, cloud APIs or heavy donor runtime are needed for this gate.
