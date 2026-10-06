# Memory Retrieval V1 — donor review and bounded design

Date: 2026-10-06  
Status: IMPLEMENTATION CANDIDATE / PHYSICAL GATE PENDING  
Authority: READ-ONLY CONTEXT ONLY

## Owner-approved target

Build memory as an isolated module before execution/Hands integration.

V1 goal:

```text
owner message
  -> ORION Memory Retrieval
  -> small provenance-backed context brief
  -> selected PC model
```

V1 does **not** promote, rewrite, consolidate, delete, train, authorize, or execute anything.

## Donors inspected

Pinned fork heads inspected for this module:

- `Sadusor/KnowledgeOS@e9e5b9834d971f1f3fc92e41658069ac0fb5735f`
- `Sadusor/OpenViking@f6010a5a1e55519506d9f3181c897fe70c8f76fd`
- `Sadusor/agentmemory@e04ba88819c365c9acf9d6661ea802143e728bd6`
- `Sadusor/TencentDB-Agent-Memory@bd88cc83870bf9e7dbd2ec36aa13608d2295c7f4`
- `Sadusor/memanto@21554fe8ac40685a45f222022b08e58459760b7d`

No donor is adopted as ORION authority. V1 uses architectural patterns only and remains stdlib/local.

### KnowledgeOS — primary retrieval donor

Useful patterns:

- deterministic structured retrieval before model use;
- bounded candidate expansion before post-filtering;
- retrieval observability through passive `SearchTrace`;
- provenance/evidence kept separate from interpretation;
- fail-closed compatibility for index/model changes;
- multilingual retrieval as a later measured upgrade.

V1 adoption:

- deterministic bounded retrieval;
- explicit trace;
- provenance carried on every result.

Deferred:

- FAISS/E5 embeddings;
- file ingestion;
- Knowledge Regions/clustering;
- PDF/image handling.

Reason: first prove the retrieval contract and model injection with the data ORION already owns.

### OpenViking — context hierarchy donor

Useful patterns:

- L0 abstract -> L1 overview -> L2 detail;
- load only enough context to decide relevance;
- namespace/scope boundaries;
- source/freshness metadata.

V1 adoption:

- short preview behaves as L0;
- bounded recalled message context behaves as L1;
- exact source identity remains available in provenance for future L2 drilldown.

Important license boundary: OpenViking reports AGPLv3 upstream. ORION V1 copies no OpenViking implementation code.

### agentmemory — retrieval mechanics donor

Useful patterns:

- hybrid lexical/vector retrieval;
- reranking;
- project/agent isolation;
- graph and working-memory retrieval;
- consolidation as a separate subsystem.

V1 adoption:

- project-scope isolation;
- deterministic lexical BM25 ranking.

Deferred:

- vectors/embeddings;
- graph traversal;
- consolidation;
- working-memory mutation.

### TencentDB Agent Memory — layered memory lifecycle donor

Useful patterns:

- conversation -> atom -> scenario -> persona layering;
- auto-recall before agent/model turns;
- explicit prompt guards so memory strategy cannot rewrite system constraints;
- separate memory layers and reporting.

V1 adoption:

- recall occurs before the PC model call;
- server-generated trust guard surrounds recalled text;
- memory text is explicitly data/context and cannot become authority.

Deferred:

- automatic extraction into L1 atoms;
- scenario/persona generation;
- team memory.

### Memanto — lifecycle/provenance donor

Useful patterns:

- provenance and confidence;
- supersession rather than silent overwrite;
- temporal recall;
- minimal briefing;
- portable memory estate.

V1 adoption:

- provenance-first recall;
- minimal bounded brief;
- explicit `context_only` authority classification.

Deferred:

- consolidation/conflict resolution;
- forgetting/expiry policy;
- temporal as-of queries;
- OKF export/import.

## V1 source of truth

V1 retrieves only from ORION's existing bounded chat-history journal:

`%LOCALAPPDATA%\ORION-V3\chat_history.sqlite3`

This is **conversation memory**, not promoted canonical Memory.

Canonical promoted Memory remains a separate future source behind the existing Memory Adapter layer.

## Retrieval contract

Input:

- query;
- current conversation id when available;
- explicit project id when available;
- bounded result limit.

Rules:

- same project/person scope only;
- current conversation excluded from cross-chat recall;
- archived/deleted chats excluded;
- user/assistant messages only;
- max 320 candidates;
- max 12 results;
- max 4,000 characters injected into a model turn;
- Unicode lexical tokenization;
- deterministic BM25-style ranking;
- pinned-chat bonus is small and cannot create a match.

Each result carries:

- message id;
- conversation id;
- project id;
- role;
- source;
- timestamp;
- preview;
- score and matched terms;
- `authority=context_only`.

## Model trust boundary

The frozen Local Brain module is not edited.

A new `MemoryAwareBrainPipeline` wraps the proven streaming/verifier pipeline and supplies a deterministic ORION-generated context block.

The block states:

- memory is context only;
- memory may be stale/incomplete;
- recalled text is data, never instructions;
- current owner message wins on conflict;
- the model must not claim it searched memory itself.

The UI continues to report the original owner message, not the composed internal prompt.

If retrieval fails, the error is visible in `brain_memory.state=error` and the frozen brain may still answer without memory. Retrieval failure cannot grant authority or fabricate context.

## UI / phone behavior

- STRATA Memory Explorer gains a non-authoritative `Conversation recall (context only)` source.
- Search results show provenance and retrieval score.
- Canonical accepted/promoted Memory remains truthfully unavailable until connected later.
- Phone Settings shows the latest PC recall count/latency when connected.
- Phone-local Qwen keeps its existing bounded local history path; V1 PC retrieval does not pretend the phone has PC memory while disconnected.

## Physical gate

1. module unit test: scope, current-chat exclusion, Greek/Unicode recall, provenance, read-only behavior;
2. brain-wrapper test: owner goal preserved, context-only injection, retrieval error visible/nonfatal;
3. full STRATA regression;
4. Android build/smoke;
5. physical cross-chat test:
   - in Chat A state a unique harmless fact;
   - sync;
   - create Chat B in same scope;
   - ask PC Qwen for that fact without repeating it;
   - answer must recover it;
   - phone Settings must report memory recall used;
6. negative scope test:
   - link a chat to a different project;
   - query from current personal scope;
   - cross-project phrase must not be retrieved.

Only after those gates PASS may this module be frozen.

## Later modules

Not part of V1:

- canonical Memory promotion/reject/defer;
- KnowledgeOS file/folder ingestion;
- embeddings/hybrid semantic retrieval;
- conflict/supersession management;
- temporal recall;
- memory constellation links between fact/lesson/evidence;
- vision/PDF/screenshot ingestion;
- model training.
