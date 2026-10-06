# Canonical Memory Candidate Queue V1 — physical PASS

Date: 2026-10-06

## Result

PASS.

ORION 0.4.0 Memory Candidate Queue V1 was physically tested on the Android phone against the live PC backend.

## Proven behavior

The owner explicitly long-pressed existing chat messages and chose:

`Propose as memory candidate`

The phone showed:

`Queued as memory candidate`

Settings then showed:

`5 pending candidates · not canonical Memory`

This proves the live phone -> authenticated PC -> exact source resolution -> pending candidate persistence path works.

## Dedupe physical proof

The owner then selected the exact same source message again:

`The owner-confirmed value for PROJECT STARLING is GREEN 842.`

ORION responded:

`Already queued as memory candidate`

Settings still showed:

`5 pending candidates · not canonical Memory`

The count did not increase to 6.

This physically proves idempotent deduplication for the same exact source message/content.

## Important authority result

The candidate queue did **not** promote any selected message to canonical Memory.

The UI continued to state:

`not canonical Memory`

The automated qualification gate also proved:

- exact server-side source snapshot;
- arbitrary client-supplied forged candidate text ignored;
- authenticated intake;
- project/owner-scope enforcement;
- user vs assistant trust provenance preserved;
- archived/deleted source denial;
- chat history remains immutable;
- canonical memory write = NONE;
- full frozen Memory Retrieval V1 regressions still PASS;
- full STRATA suite PASS;
- phone JavaScript syntax PASS;
- Android model-less 0.4.0 build PASS;
- live ORION repo preserved.

## Frozen boundary

The following behavior is now treated as proven and should not be casually refactored:

- owner-only explicit candidate intake;
- exact source-message server resolution;
- no arbitrary client text accepted as candidate content;
- pending-only candidate state;
- no automatic promotion;
- no model-authorized canonical memory writes;
- deterministic candidate identity;
- idempotent deduplication;
- exact project/default-scope checks;
- owner scope `owner:primary`;
- user vs assistant trust provenance;
- append-oriented bounded candidate persistence;
- queue overflow refusal instead of silent pruning;
- Android long-press candidate action;
- phone-visible pending count;
- STRATA Memory Explorer candidate intake;
- canonical-memory-written = false.

## Proven source commit

`1f762e7b9de99b4474027f5edfd4cc15d68c9133`

## Next memory module

**Canonical Memory Review + Promotion V1**

That future module may add explicit owner decisions:

`PROMOTE / REJECT / DEFER`

with append-only decision evidence and provenance.

No automatic promotion is authorized by this PASS record.
