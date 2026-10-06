# Canonical Memory Candidate Queue V1

Date: 2026-10-06  
Status: IMPLEMENTATION CANDIDATE / PHYSICAL GATE PENDING  
Branch: `feature/canonical-memory-candidate-queue-v1`

## Purpose

Create the first explicit boundary between **conversation recall** and **canonical Memory**.

A recalled chat message may be useful, but it is not durable truth. V1 therefore adds a separate owner-reviewed intake queue:

```text
exact existing chat message
  -> owner explicitly selects it
  -> candidate queue
  -> PENDING ONLY
  -> future canonical promotion module
```

No model, Hand, background process or retrieval result automatically enters canonical Memory.

## Hard authority boundary

This module may:

- snapshot an exact existing user/assistant chat message;
- preserve its provenance and content hash;
- store it as a pending candidate;
- list queued candidates;
- deduplicate repeated owner selections.

This module may **not**:

- create canonical Memory;
- promote, reject or supersede durable Memory;
- delete or rewrite chat history;
- accept arbitrary candidate text supplied by the client;
- infer a candidate automatically;
- grant permissions or execution authority;
- let a model approve its own output.

Every API response explicitly reports `canonical_memory_written=false`.

## Source resolution

The client submits only:

- `conversation_id`;
- `message_id`;
- the expected `project_id`;
- fixed `owner_scope=owner:primary`.

The server then re-reads the exact message from the authoritative synced chat-history store.

The client is **not allowed to choose the candidate content**. Any extra `content` field is ignored.

This prevents a compromised/stale UI from laundering arbitrary text into the candidate queue while pretending it came from an existing message.

## Candidate provenance

Each pending candidate stores:

- deterministic candidate ID;
- exact content snapshot;
- SHA-256 of the content;
- owner scope;
- project scope;
- source conversation ID;
- source message ID;
- source role;
- source message transport/source;
- source timestamp;
- source reference;
- trust origin;
- trust tier;
- classification;
- reason for candidate;
- submitted timestamp;
- state `pending`.

Trust mapping:

- user message -> `trust_origin=user`, `trust_tier=owner_message_unverified`;
- assistant message -> `trust_origin=derived`, `trust_tier=assistant_prior_unverified`.

This preserves the poisoning protections proven in Memory Retrieval V1.

## Persistence

Store:

`%LOCALAPPDATA%\ORION-V3\memory_candidates.sqlite3`

The queue is append-oriented.

V1 does **not** silently prune old candidates. If the bounded queue reaches 500 pending records, new intake is refused until a later review/decision module can resolve the queue.

Repeated selection of the same exact source/content is idempotent and returns the existing candidate.

## Source restrictions

Rejected:

- missing conversation/message;
- deleted conversation;
- archived conversation;
- project mismatch;
- unsupported owner scope;
- non-user/non-assistant role;
- empty message.

## UI

### STRATA Memory Explorer

A recalled conversation node may expose:

**Propose as memory candidate**

The action is an approval-kind route and requires a real trusted user click.

The Memory Explorer then shows queued candidates as:

**CANDIDATE · not promoted Memory**

### Android phone

Long-press an existing chat message -> **Propose as memory candidate**.

The phone sends only the exact message/conversation/project identifiers to the PC.

Settings shows the current pending candidate count and explicitly states that candidates are not canonical Memory.

## Why no Promote/Reject yet?

Promotion is the actual durable-memory trust boundary and deserves its own module and physical qualification.

Keeping candidate intake separate proves that:

1. recall works;
2. owner can explicitly nominate useful material;
3. nomination alone changes no canonical truth;
4. later policy can review provenance before any durable promotion.

## Tests

Automated V1 gate must prove:

- exact server-side source snapshot;
- client-supplied forged content is ignored;
- user vs assistant trust tier preservation;
- idempotent dedupe;
- project-scope mismatch denial;
- archived/deleted source denial;
- unsupported owner scope denial;
- chat history remains unchanged;
- authenticated product HTTP intake;
- `GET /api/memory/candidates` returns pending candidates;
- candidate intake UI route requires trusted gesture;
- full STRATA regression;
- phone JavaScript syntax;
- Android model-less APK build;
- live ORION repo remains untouched during isolated qualification.

## Physical test

After automated qualification and promotion to main:

1. long-press the owner message `GREEN 842`;
2. choose **Propose as memory candidate**;
3. Settings should show **1 pending candidate**;
4. repeat the same action; count must remain 1 and UI should say already queued;
5. ask ORION the fact normally; behavior must still come from Conversation Recall, not from the candidate queue;
6. no UI anywhere may claim the candidate is canonical Memory.

Only then freeze Candidate Queue V1.

## Next module

**Canonical Memory Review + Promotion V1**

That future module may implement owner decisions:

`PROMOTE / REJECT / DEFER`

with append-only decisions and provenance. No automatic promotion is authorized by this document.
