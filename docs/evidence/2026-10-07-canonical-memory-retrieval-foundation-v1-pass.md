# Canonical Memory Retrieval Foundation V1 — qualification PASS

Date: 2026-10-07

## Result

PASS.

The isolated qualification gate for Canonical Memory Retrieval Foundation V1
completed successfully at exact source commit:

`934fe1bf7f430d2892a515e2d4c0ef7f46328982`

TheHands session:

`0ea74b75ef10`

The final gate line was:

`ORION_CANONICAL_RETRIEVAL_FOUNDATION_V1_GATE> PASS`

Unlike several earlier TheHands bookkeeping cases, this session metadata itself
also reported PASS with a populated `finished_at`.

## Frozen regressions preserved

The gate re-ran and passed:

- Chat History;
- Conversation Recall V1;
- Conversation Recall adversarial tests;
- Memory Candidate Queue V1;
- Candidate Queue HTTP tests;
- Canonical Memory Review + Promotion V1;
- Review + Promotion HTTP tests;
- frozen memory-aware Local Brain wrapper;
- existing memory product route;
- STRATA full regression suite;
- frozen phone-shell JavaScript syntax.

The live ORION repo remained unchanged during the isolated gate.

## Retrieval-foundation boundaries proven

The new module passed:

- exact owner/project scope resolution;
- default project scope is not global;
- revoked canonical-memory exclusion;
- superseded-current exclusion;
- explicit historical labeling for superseded memories;
- current-conversation source exclusion;
- retrieval-time admission filtering distinct from promotion-time filtering;
- durable content/provenance integrity recheck at retrieval;
- owner trust-tier-only admission in V1;
- explicit epistemic status:
  `owner-approved durable context, not verified truth`;
- structural separation from ordinary Conversation Recall;
- explicit 40/60 durable-vs-recall context budget contract;
- deterministic BM25 ordering;
- one-time bound supersession ticket;
- cross-project supersession refusal;
- append-only supersession ledger;
- supersession hash-chain audit;
- canonical-memory authority remains `context_only`.

## Supersession representation

Frozen canonical rows remain immutable.

Supersession is represented in a separate append-only ledger:

`old_memory_id -> replacement_memory_id`

The current retrieval path excludes superseded memories by default. Historical
mode may expose them only with `status=historical` and the explicit
`superseded_by` relation.

## Trust meaning

The internal term "canonical" remains for compatibility with the frozen storage
module, but model-facing semantics are explicitly:

`owner-approved durable context, not verified truth`

No durable memory grants:

- execution authority;
- approval authority;
- permissions;
- capabilities;
- system/developer instruction authority.

## Not yet integrated into Local Brain

This PASS freezes the retrieval foundation only.

Owner-approved durable memories are still **not yet injected into Local Brain
prompts**. The next module is the actual Canonical Memory Retrieval integration /
fusion layer.

That integration must preserve:

- separate labeled durable and Conversation Recall blocks;
- the explicit context budget;
- exact owner/project scope;
- revoked/superseded/current-conversation exclusion;
- retrieval-time admission;
- provenance + epistemic labels;
- no silent conflict precedence;
- context-only authority.

