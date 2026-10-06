# DeepSeek adversarial review — Memory Retrieval V1

Date: 2026-10-06  
Reviewed candidate: `876d9bff8d3e8432254294fab7ff9c6ab8340f90`  
Reviewer verdict: **PASS WITH CHANGES**

## Blocking findings

DeepSeek agreed with the read-only retrieval-first architecture, but identified eight fixes that should land before physical qualification:

1. distinguish owner messages from assistant-prior messages and do not give them equal trust;
2. make empty `project_id=""` an explicit default scope, never a wildcard;
3. structurally delimit recalled text and place the current owner message last;
4. add a confidently-wrong-assistant falsification test;
5. apply a relevance floor rather than always filling the result budget;
6. verify Unicode-aware normalization/casefold behavior;
7. distinguish normal empty recall from retrieval error and make failures owner-visible;
8. reserve an owner/user scope now, even while ORION is single-owner.

Additional recommended low-cost improvements:

- preserve query fingerprint and index/schema version in provenance/trace;
- keep message hashes for corruption/debug evidence;
- reserve supersession fields without implementing supersession yet;
- measure recall misses before deciding whether embeddings are necessary;
- do not prematurely label raw chat recall as OpenViking-style L0/L1/L2 memory;
- keep the next memory module as an owner-reviewed canonical candidate queue, not auto-promotion.

## Changes applied before physical test

The branch now implements:

- `owner_message_unverified` vs `assistant_prior_unverified` trust tiers;
- fixed assistant-prior ranking weight below owner messages;
- exact `owner:primary` scope;
- exact named/default project isolation;
- bounded chat snapshot scan -> lexical prefilter -> 320 candidate cap;
- Unicode NFKD normalization + combining-mark removal + casefold;
- deterministic BM25 ranking with absolute + relative relevance floor;
- cumulative hit/miss counters in retrieval trace;
- SHA-256 query fingerprint;
- message SHA-256;
- index version;
- reserved supersession metadata;
- conservative instruction-like risk flags;
- risky stored rows remain visible diagnostically but are excluded from model context;
- XML-like `<ORION_RECALL_CONTEXT>` / `<ORION_RECALL_ITEM>` structural boundaries;
- recalled context before `<OWNER_CURRENT_MESSAGE>`;
- distinct `pass / empty / filtered / error` recall states;
- phone Settings shows empty/filtered/error truthfully;
- STRATA marks a recall backend failure unavailable rather than faking an empty result;
- adversarial deterministic tests for poisoning, project leakage, injection filtering, Unicode normalization, determinism, empty result, context budget and owner-scope rejection.

## Deliberately deferred

- embeddings / hybrid dense retrieval;
- OpenViking L0/L1/L2 hierarchy;
- graph retrieval;
- automatic consolidation;
- contradiction/supersession logic;
- temporal/as-of recall;
- file/PDF/image ingestion;
- canonical promotion;
- training/fine-tuning.

These remain deferred until the simpler recall module produces physical evidence.

## Required physical falsification after automated gate

Before freezing V1:

- plant a harmless unique owner fact in Chat A and recover it from fresh Chat B;
- prove another project cannot leak into the current/default scope;
- plant a confidently wrong assistant prior and a contradictory correct owner statement;
- query from a fresh chat;
- verify the owner statement wins retrieval order and the model does not present the assistant prior as verified truth.

## Next module if V1 passes

**Canonical Memory Candidate Queue** — owner-reviewed intake only. No automatic promotion and no model-authorized writes.
