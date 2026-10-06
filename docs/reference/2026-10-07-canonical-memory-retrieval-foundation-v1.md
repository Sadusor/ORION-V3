# Canonical Memory Retrieval Foundation V1

Date: 2026-10-07
Status: candidate under isolated qualification
Branch: `feature/canonical-memory-retrieval-foundation-v1`

## Why this module exists

After Canonical Memory Review + Promotion V1 physically passed and was frozen,
DeepSeek performed an adversarial architecture review of the planned read path.

The review's useful correction was that several concerns originally placed under
later "memory maintenance" are actually retrieval-correctness boundaries:

- exact canonical scope resolution;
- retrieval-time admission control distinct from promotion-time admission;
- supersession representation before retrieval freezes;
- structural separation of owner-approved durable context from ordinary
  Conversation Recall;
- explicit epistemic labeling so "canonical" never becomes synonymous with
  verified truth or execution authority;
- explicit context-budget ownership.

The review verdict was PROCEED WITH CHANGES.

## Frozen modules remain untouched

This module does not modify the frozen behavior of:

- Conversation Recall V1;
- Memory Candidate Queue V1;
- Canonical Memory Review + Promotion V1.

Canonical rows remain immutable.

## Scope contract

V1 supports one owner scope:

`owner:primary`

Project scope is exact:

- `project_id=""` means the default project scope;
- the default scope is not a wildcard;
- a named project retrieves only that named project;
- no implicit global-memory namespace exists in this V1 foundation.

A future global namespace must be introduced explicitly rather than inferred from
an empty project id.

## Retrieval-time admission

Promotion-time admission answers:

"May this exact source message become durable owner-approved context?"

Retrieval-time admission answers:

"May this durable item be injected for this owner/project/conversation now?"

The read gate independently requires:

- active (not revoked);
- not superseded for current retrieval;
- exact owner scope;
- exact project scope;
- supported owner trust tier;
- complete source candidate provenance;
- source conversation is not the current conversation;
- no secret/instruction/injection risk under the retrieval-time policy.

Failure is exclusion with a trace reason. Memory never gains authority by passing
the gate.

## Epistemic meaning

Internal code may retain "canonical" for continuity with the frozen storage
module, but model-facing context uses:

`owner-approved durable context, not verified truth`

Every item remains:

`authority=context_only`

It is never:

- system/developer instruction;
- execution authority;
- approval authority;
- permission;
- capability grant;
- verified objective truth.

## Supersession without rewriting frozen rows

DeepSeek proposed storing supersession affordances on canonical rows. ORION keeps
the intent but not the mutable-row mechanism because Canonical Memory V1 already
proved immutable rows.

Instead this foundation creates a separate append-only supersession ledger:

`old_memory_id -> replacement_memory_id`

Each event stores:

- exact old/new memory ids;
- exact old/new content hashes;
- owner scope;
- project scope;
- actor fingerprint;
- one-time review-token hash;
- monotonic event index;
- previous event hash;
- event hash;
- timestamp/reason.

Rules:

- both endpoints must already be active durable memories;
- supersession cannot cross project scope;
- one memory cannot supersede itself;
- replacement must itself be current;
- an old memory cannot be redirected to a different replacement;
- one-time owner supersession tokens are consumed once;
- UPDATE and DELETE of supersession events are denied by SQLite triggers.

The hash-chain limitation remains explicit: it detects in-database mutation or
reordering, not wholesale local database replacement without a future external
anchor.

## Retrieval behavior

Current retrieval:

- excludes revoked memories;
- excludes superseded memories;
- supports bounded deterministic BM25;
- uses recency only as a deterministic tie/browse order;
- requires provenance;
- excludes source memories from the current conversation;
- emits exact scope and filter traces.

Historical mode may include a superseded memory only as:

`status=historical`

with its `superseded_by` relation.

## Fusion contract for the next module

Owner-approved durable context and Conversation Recall must never be flattened
into one ranked list.

Default combined context budget:

- 40% owner-approved durable context;
- 60% Conversation Recall.

The next integration module must preserve two structurally labeled blocks and must
not let storage class silently decide a conflict.

Automatic semantic contradiction detection is deliberately not claimed in this
foundation. Items expose:

- `contradiction_flag=null`;
- `conflict_status=not_evaluated_until_fusion`.

The fusion module must surface potentially conflicting evidence rather than
pretending a brittle lexical heuristic can prove semantic contradiction.

## Not yet connected

This foundation does not yet:

- inject owner-approved durable context into Local Brain;
- change the frozen Conversation Recall prompt;
- create a phone/STRATA supersession UI;
- expose a product HTTP supersession route;
- automatically detect candidates;
- automatically detect semantic contradictions;
- consolidate/merge memories;
- use embeddings, vectors or graph retrieval.

## Qualification gate

The isolated gate must prove at minimum:

- frozen Conversation Recall regression PASS;
- frozen Candidate Queue regression PASS;
- frozen Review + Promotion regression PASS;
- exact scope isolation;
- default scope is not global;
- revoked exclusion;
- superseded-current exclusion;
- historical labeling;
- current-conversation exclusion;
- retrieval-time risk filtering;
- owner trust-tier admission;
- per-item epistemic labeling;
- deterministic ordering;
- separate fusion contract;
- explicit 40/60 budget contract;
- one-time supersession ticket;
- cross-project supersession refusal;
- supersession append-only triggers;
- supersession hash-chain audit;
- read-only retrieval does not mutate frozen canonical state.

Only after this foundation passes should ORION build the actual combined
Canonical Memory Retrieval integration into Local Brain.
