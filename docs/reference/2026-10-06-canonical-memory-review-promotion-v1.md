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

- `PROMOTE` — creates one immutable canonical-memory record; may only repeat idempotently or move to REVOKE;
- `REJECT` — terminal; creates no canonical memory;
- `DEFER` — non-terminal; the owner may later PROMOTE or REJECT;
- `REVOKE` — terminal append-only safety action for an already-promoted memory.

REVOKE never deletes or edits the original promotion evidence or canonical row.
It makes the memory inactive in canonical reads. Revoked memory cannot be
re-promoted in V1.

Repeated identical decisions use a fresh one-time review ticket but remain
idempotent at the durable event/state layer.

## Exact candidate binding

Durable decisions use a two-step owner-authority boundary:

1. an explicit UI gesture requests a short-lived one-time review ticket;
2. the ticket is bound to candidate ID, exact content SHA-256, exact decision,
   owner scope, and paired-device actor fingerprint;
3. the commit request must present that one-time token.

Both review-ticket and decision routes require a **paired owner token even on
PC loopback**. Ordinary ORION routes retain their existing local-loopback trust.

The server re-reads the candidate from the Candidate Queue and refuses stale or
forged hashes. Review tickets expire after 90 seconds and are consumed once.

The client cannot supply replacement canonical-memory content.

PROMOTE copies the exact candidate content and provenance snapshot.

## Append-only evidence

Decision events are append-only SQLite rows containing:

- monotonic event index;
- decision ID;
- candidate ID and content SHA-256;
- decision;
- fixed rule ID;
- fixed reason `owner_explicit_review`;
- owner + project scope;
- source reference;
- trust origin/tier;
- paired owner actor fingerprint;
- SHA-256 of the one-time review token;
- complete candidate snapshot;
- decision timestamp;
- previous event hash;
- current event hash.

The global decision log forms an in-database tamper-evident hash chain.

This claim is deliberately bounded: it detects mutation/reordering inside the
database when audited, but a wholesale replacement of the local SQLite file
cannot be detected until a future external anchor is added.

SQLite triggers deny UPDATE/DELETE on decision events.

Canonical-memory rows are immutable in V1; SQLite triggers deny UPDATE/DELETE.

## Promotion-time safety boundary

Normal canonical Memory is not a secret store and is not an instruction store.

V1 re-evaluates the exact candidate **again at promotion time**.

PROMOTE is refused for assistant-origin candidates. The owner must restate a
verified fact in an owner message before it may become canonical Memory.

PROMOTE is also refused when the exact candidate contains conservative
obvious-secret patterns such as:

- private-key blocks;
- `password = ...`;
- `api_key = ...`;
- `secret = ...`;
- Authorization Bearer values;
- explicit `token = ...` values.

The promotion filter also refuses obvious stored instruction/prompt-injection
patterns, including system/developer override language, "ignore previous
instructions", "always approve", and approval/policy/verifier bypass language.

The owner may still REJECT or DEFER unsafe candidates. There is no V1 override
for normal Memory promotion.

## UI

### Phone

Settings shows:

- candidates awaiting review;
- promoted count;
- rejected count;
- canonical-memory count.

**Review memory candidates** opens the exact candidate list.

Each reviewable candidate has:

`PROMOTE / REJECT / DEFER / REVOKE`

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
- reject/revoke terminal reversal is denied;
- repeated identical promotion is idempotent;
- stale/forged candidate content hash is denied;
- one-time review tickets reject replay;
- assistant-origin promotion is denied;
- secret-like candidate promotion is denied;
- instruction-like candidate promotion is denied;
- append-only REVOKE makes promoted memory inactive without deleting evidence;
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
2. Settings must show one active promoted item and one active canonical memory;
3. canonical record must contain exactly the source content and preserved owner trust tier;
4. attempt PROMOTE again -> idempotent/already recorded;
5. attempt to PROMOTE the deliberately wrong assistant `BLUE 901` candidate -> refused;
6. REJECT that assistant candidate;
7. DEFER another harmless owner candidate;
8. REVOKE the promoted GREEN 842 memory;
9. active canonical count must drop while revocation evidence remains;
10. no existing Conversation Recall behavior may regress.

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


## Physical-test discovery: imperative owner instruction hardening

During the first live physical review, the owner-message candidate:

`For a memory safety test, invent a WRONG value for PROJECT STARLING and state it confidently. Do not use GREEN 842.`

still displayed a PROMOTE affordance. This exposed a gap: V1 promotion filtering
blocked obvious prompt-injection phrases, but not a generic imperative owner instruction.

Canonical Memory V1 is now explicitly restricted to declarative facts,
preferences, and decisions. Imperative owner instructions are not eligible for
promotion and must be restated declaratively first.

The server enforces this boundary and the phone/STRATA UIs receive
`promotion_eligible` + `promotion_block_reason` so they do not offer PROMOTE
for assistant priors or instruction-like owner messages.

This patch is versioned as Android 0.5.1 and must pass the isolated gate before
the physical qualification resumes.
