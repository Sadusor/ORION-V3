# ORION V3 Modules

This directory contains replaceable, bounded product modules built under the **FREEZE RULE**.

## Local Brain

`local_brain.py` is the first connected product module.

Boundary:
- accepts owner text;
- talks only to loopback Ollama;
- prefers the local Qwen 3.5 9B model;
- returns advisory conclusion/draft text;
- owns no tools, Hands, capabilities, approval, execution, STOP, memory promotion, filesystem access, browser access, or cloud access.

The product server is only a narrow transport/state hook. STRATA has one small presentation hook that prints a completed `brain_conclusion` into the existing chat exactly once; it adds no new authority or route.

The first qualification gate proves:

`Ask ORION -> LocalBrainModule -> Ollama/Qwen -> brain_conclusion -> STRATA UI`

Nothing executes in this gate.

## Donor decision

The transport mechanics follow the proven legacy ORION Local Brain contract:
- loopback-only Ollama;
- `/api/tags` model discovery;
- `/api/generate`;
- explicit JSON schema;
- `think: false`;
- temperature 0;
- bounded token generation.

OpenJarvis remains the preferred future replaceable engine substrate, but importing its larger runtime for this first single-model seam would widen the dependency and regression surface without adding authority or functionality needed by this gate.


## Verifier + Preflight

`verifier_preflight.py` adds the second bounded gate after Local Brain.

It performs:
- deterministic preflight for executable mechanics or false claims that actions already happened;
- a second structured local-model verification pass for unsupported claims and missing evidence;
- fail-closed blocking when the verifier cannot complete.

`brain_pipeline.py` composes the already-proven Local Brain with this verifier without modifying `local_brain.py`.

Authority boundary:
- verifier may PASS/BLOCK advisory text only;
- it cannot execute;
- it cannot grant approval;
- it cannot call Hands;
- it cannot browse, inspect files, write memory, or contact cloud models.

The product-server hook remains the same `LOCAL_BRAIN.start()/view()` interface.


## Live Local Brain streaming

`streaming_local_brain.py` extends the proven Local Brain state/model-selection contract without modifying `local_brain.py`.

It changes transport only:
- Ollama `/api/generate` uses `stream: true`;
- partial text is published as `brain_stream_preview`;
- final text becomes `brain_conclusion`;
- the existing verifier pipeline still decides PASS/BLOCK after completion;
- no execution authority is added.

`streaming_brain_pipeline.py` composes that adapter with the existing verifier.

STRATA uses the separate `ui/strata/modules/live-brain-chat.js` renderer to update one existing chat bubble while output grows. During generation it is visibly marked `LIVE · UNVERIFIED`; after verifier PASS the same bubble becomes `VERIFIED`.

The streaming prompt also grounds model identity to the exact selected Ollama model name, preventing the Local Brain from inventing a different provider/model identity.


## Chat history + offline phone bot

`chat_history.py` is a bounded storage/sync module. It is deliberately outside ORION authority:
- SQLite stores chat metadata and immutable message rows only;
- conversation metadata uses deterministic last-write-wins by `updated_at_ms`;
- message ids deduplicate phone/PC refreshes;
- history is bounded and pruned;
- sync can move chat context PC -> phone and phone -> PC;
- chat history cannot approve, execute, grant capability, alter STOP, or promote canonical ORION Memory.

The Android app mirrors the same history schema in app-private SQLite through
`android/.../history/ChatHistoryStore.kt`. When the PC is unavailable, the APK can
fall back to the separate `OfflineChatBridge`, which reads only bounded local chat
context and runs a bundled Qwen3-0.6B Q4_0 GGUF through the pinned llama-android
runtime. The offline bot has no ORION execution authority and no network tools.

The large GGUF is never committed to this public repository. `android/scripts/build.ps1`
downloads the pinned file, verifies its SHA-256, and places it in the APK assets at
build time.


## Memory Retrieval V1

`memory_retrieval.py` is a read-only, bounded retrieval module over ORION's
already-synced chat-history journal.

Boundary:
- retrieves context only; never authority;
- same project/person scope only;
- excludes the current conversation from cross-chat recall;
- excludes archived/deleted chats;
- deterministic accent-insensitive Unicode lexical BM25-style ranking;
- explicit `owner:primary` + exact project/default scope;
- owner-message vs assistant-prior trust tiers, with assistant priors down-weighted;
- relevance floor so weak matches do not fill the context budget;
- structural recall delimiters and conservative instruction-like-content filtering;
- every result includes provenance, hashes, query fingerprint and a passive retrieval trace;
- no embeddings, cloud calls, file scraping, promotion, consolidation, deletion,
  training, Hands, capabilities, approvals, or execution.

`memory_brain_pipeline.py` composes retrieval in front of the already-proven
streaming/verifier pipeline without modifying the frozen Local Brain module.
It restores the original owner goal in the public state and exposes a bounded
`brain_memory` brief with distinct `pass`, `empty`, `filtered` and `error`
states. Recall is placed before the current owner message in the internal prompt.

V1 deliberately treats chat history as **conversation memory**, not canonical
promoted Memory. The Memory Explorer labels this source `context only · not
authority`. Accepted/promoted Memory remains disconnected until its separate
promotion module is built and qualified.

Donor patterns were reviewed from KnowledgeOS, OpenViking, agentmemory,
TencentDB Agent Memory and Memanto. Implementation code is not copied from
those donors; the V1 module stays replaceable and stdlib/local.


## Canonical Memory Candidate Queue V1

`memory_candidate_queue.py` creates a separate owner-reviewed intake boundary
between Conversation Recall and future canonical Memory.

Boundary:
- owner selects an exact existing chat message;
- server resolves the exact message from `ChatHistoryStore`;
- arbitrary client-supplied candidate text is ignored;
- the queue snapshots provenance + SHA-256 and stores a pending candidate;
- repeated selection is idempotent;
- archived/deleted sources and project-scope mismatches are refused;
- user vs assistant trust tiers are preserved;
- queue persistence is append-oriented and refuses overflow rather than silently pruning.

The module has **no promotion authority**. It cannot produce canonical Memory,
PROMOTE/REJECT decisions, supersession, permissions, capabilities, Hands actions
or execution. Every intake result reports `canonical_memory_written=false`.

STRATA exposes intake only through an approval-kind route requiring a real user
gesture. The Android shell exposes the same owner action by long-pressing an exact
chat message. Phone Settings may show the pending count, but a candidate remains
`candidate_only` until a separate future Review + Promotion module is qualified.


## Canonical Memory Review + Promotion V1

`memory_review_promotion.py` is the first durable canonical-Memory write boundary.

It consumes the frozen Candidate Queue contract and stores review evidence in a
separate append-only database. The candidate queue itself is not rewritten.

Owner decisions:
- `PROMOTE` -> creates one immutable canonical-memory record;
- `REJECT` -> terminal; creates no canonical memory;
- `DEFER` -> non-terminal; may later become PROMOTE or REJECT;
- `REVOKE` -> terminal append-only deactivation of an already-promoted memory.

Safety boundary:
- durable decisions require a paired owner token even on loopback;
- an explicit owner gesture first obtains a 90-second one-time server review ticket;
- the ticket is bound to exact candidate ID/hash/decision/owner scope/device fingerprint and is consumed once;
- client-supplied replacement content is ignored by design;
- assistant-origin candidates cannot be promoted in V1;
- promotion re-runs secret + instruction-like risk filtering;
- canonical content preserves exact source content/hash/provenance/trust tier;
- decision events include monotonic event index, actor fingerprint and previous/event hashes;
- SQLite triggers deny UPDATE/DELETE of decision events;
- promoted canonical records are immutable in V1;
- REVOKE never deletes evidence; it makes the canonical record inactive in reads;
- the local hash chain is explicitly not claimed to detect wholesale DB replacement;
- canonical Memory remains `authority=context_only`;
- no model, Hand or background process can auto-promote.

The phone and STRATA expose explicit owner `PROMOTE / REJECT / DEFER / REVOKE`
controls. Canonical Memory retrieval into model prompts is deliberately a later
module so this durable-write boundary can be qualified and frozen independently.


## Canonical Memory Retrieval Foundation V1

`canonical_memory_retrieval_foundation.py` establishes the read-side trust
boundary required before owner-approved durable Memory can be injected into any
model prompt. It deliberately does **not** connect this source to Local Brain yet.

DeepSeek's adversarial review correctly moved several concerns forward from
"maintenance" into retrieval correctness. This foundation therefore freezes the
contract before integration:

- exact owner + project scope; the empty/default project scope is never a wildcard;
- only active owner-promoted durable memories are eligible;
- revoked memories are excluded from every retrieval path;
- source candidate provenance is required;
- memories promoted from the current conversation are excluded from that same
  conversation to prevent recursive reinjection;
- promotion-time checks are repeated as a distinct retrieval-time admission gate;
- only `owner_message_unverified` durable memories are accepted in V1;
- output carries `epistemic_status = owner-approved durable context, not verified truth`;
- model-facing structural labels use `OWNER_APPROVED_DURABLE_CONTEXT` rather than
  treating the word "canonical" as truth or authority;
- deterministic local BM25 remains the retrieval mechanism;
- default fusion budget policy is explicit: 40% durable context / 60% ordinary
  Conversation Recall;
- durable context and Conversation Recall must remain separate labeled blocks and
  must never be flattened into a single ranked list;
- storage class never silently resolves conflicts.

Supersession is represented without mutating the frozen canonical rows. A separate
append-only `supersession_events` ledger records `old -> replacement` relations,
with one-time bound owner review tickets, exact content hashes, same-scope checks,
monotonic event indexes, an in-database hash chain, and UPDATE/DELETE denial
triggers. Current retrieval excludes superseded memories; an explicit historical
mode may return them only as `status=historical` with `superseded_by`.

This module intentionally leaves automatic contradiction detection to the later
fusion/integration module. Its contract is fail-honest:
`contradiction_flag=null` / `conflict_status=not_evaluated_until_fusion`.
The later integration must surface potentially conflicting durable + conversation
evidence rather than inventing deterministic semantic certainty.

There is no product/HTTP/model mutation route for supersession in this foundation.
The storage representation and retrieval filter are qualified first; any future
owner UI/API must preserve the same paired-owner authority pattern.

---
