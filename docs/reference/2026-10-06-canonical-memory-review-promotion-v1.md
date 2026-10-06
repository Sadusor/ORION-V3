# Canonical Memory Review + Promotion V1

Date: 2026-10-06  
Status: IMPLEMENTATION CANDIDATE / ISOLATED GATE PENDING  
Branch: `feature/canonical-memory-review-promotion-v1`

## Purpose

Add the first durable canonical Memory write boundary while preserving the frozen
Conversation Recall V1 and Memory Candidate Queue V1 modules.

The flow is:

```text
existing pending candidate
  -> owner explicitly reviews exact candidate
  -> PROMOTE / REJECT / DEFER
  -> append-only decision evidence
  -> PROMOTE only: immutable canonical-memory record
```

No model, retrieval result, Hand, reviewer, background process or donor memory
engine may make the decision automatically.

## Authority model

Canonical Memory is durable **context**, not execution authority.

A promoted memory may inform later reasoning, but cannot by itself:

- grant permission;
- authorize a consequential action;
- change ORION policy;
- reveal/use secrets;
- bypass approvals;
- invoke Hands or capabilities.

Every canonical memory record therefore reports:

`authority=context_only`

## Frozen-module discipline

This module does not edit the frozen Candidate Queue storage semantics.

It reads candidates through the Candidate Queue public contract and stores review
decisions + promoted memories in a separate database:

`%LOCALAPPDATA%\ORION-V3\canonical_memory.sqlite3`

The frozen Conversation Recall retriever is also unchanged. Canonical Memory
retrieval into model prompts is deliberately a later module.

## Owner decisions

Allowed decisions:

- `PROMOTE` — terminal; creates one immutable canonical-memory record;
- `REJECT` — terminal; creates no canonical memory;
- `DEFER` — non-terminal; the owner may later PROMOTE or REJECT.

V1 terminal decisions cannot be reversed. A future correction/supersession
module will append a new correction record instead of rewriting history.

Repeated identical terminal decisions are idempotent.

## Exact candidate binding

A decision request contains:

- candidate ID;
- expected candidate content SHA-256;
- decision;
- fixed owner scope `owner:primary`.

The server re-reads the candidate from the Candidate Queue and refuses stale or
forged hashes.

The client cannot supply replacement canonical-memory content.

PROMOTE copies the exact candidate content and provenance snapshot.

## Append-only evidence

Decision events are append-only SQLite rows containing:

- decision ID;
- candidate ID and content SHA-256;
- decision;
- fixed rule ID;
- fixed reason `owner_explicit_review`;
- owner + project scope;
- source reference;
- trust origin/tier;
- complete candidate snapshot;
- decision timestamp;
- previous event hash;
- current event hash.

The global decision log forms a tamper-evident hash chain.

SQLite triggers deny UPDATE/DELETE on decision events.

Canonical-memory rows are immutable in V1; SQLite triggers deny UPDATE/DELETE.

## Secret boundary

Normal canonical Memory is not a secret store.

V1 refuses PROMOTE when the exact candidate contains conservative obvious-secret
patterns such as:

- private-key blocks;
- `password = ...`;
- `api_key = ...`;
- `secret = ...`;
- Authorization Bearer values;
- explicit `token = ...` values.

The owner may still REJECT such a candidate. There is no V1 override for normal
Memory promotion.

## UI

### Phone

Settings shows:

- candidates awaiting review;
- promoted count;
- rejected count;
- canonical-memory count.

**Review memory candidates** opens the exact candidate list.

Each reviewable candidate has:

`PROMOTE / REJECT / DEFER`

PROMOTE requires an explicit confirmation dialog.

### STRATA Memory Explorer

Pending/deferred candidate nodes expose the same three owner decisions.

Promoted canonical records become a separate Memory Adapter source:

**Canonical memory (context only)**

They are not labelled execution authority.

## V1 automated falsification gates

Must prove:

- owner PROMOTE creates exact immutable canonical content;
- owner REJECT creates no canonical content;
- DEFER remains reviewable and can later PROMOTE;
- terminal decision reversal is denied;
- repeated identical promotion is idempotent;
- stale/forged candidate content hash is denied;
- secret-like candidate promotion is denied;
- candidate queue remains unchanged;
- decision rows are append-only;
- canonical rows are immutable;
- event hash chain verifies;
- product HTTP route is authenticated;
- forged replacement content from client is ignored;
- canonical GET route returns only promoted records;
- STRATA decision route requires trusted user gesture;
- full previously frozen memory regressions still pass;
- phone JS syntax passes;
- Android 0.5.0 model-less APK builds;
- live ORION repo remains untouched during isolated qualification.

## Physical gate after adversarial review

Use existing real candidates on the phone:

1. PROMOTE the owner-confirmed `GREEN 842` candidate;
2. Settings must show one more promoted item and one canonical memory;
3. canonical record must contain exactly the source content;
4. attempt PROMOTE again -> idempotent/already recorded;
5. REJECT the deliberately wrong assistant `BLUE 901` candidate;
6. it must not enter canonical Memory;
7. DEFER another harmless candidate;
8. it remains reviewable;
9. no existing Conversation Recall behavior may regress.

Only then freeze Review + Promotion V1.

## Explicitly deferred

- canonical Memory injection into Local Brain prompts;
- automatic promotion;
- model-generated summaries as canonical records;
- contradiction detection;
- supersession/corrections;
- temporal history;
- embeddings/hybrid retrieval;
- file/PDF/image ingestion;
- secret-store integration.

## Next module if V1 passes

**Canonical Memory Retrieval V1**

That module will combine owner-promoted canonical context with the already-frozen
Conversation Recall path while keeping canonical memory context-only and
provenance-visible.
