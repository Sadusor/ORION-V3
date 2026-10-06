# Canonical Memory Review + Promotion V1 — physical PASS

Date: 2026-10-06

## Result

PASS.

ORION 0.5.1 Memory Review + Promotion V1 was physically tested on the live Android phone against the live PC backend after the adversarial hardening pass.

## Proven owner-review behavior

The physical review exercised the real pending candidate set created during Memory Candidate Queue V1.

### Owner fact promotion

The owner-confirmed source message:

`The owner-confirmed value for PROJECT STARLING is GREEN 842.`

was promoted through the live phone review UI.

This proved the live:

`phone -> paired owner auth -> one-time review ticket -> exact candidate/hash -> durable canonical write`

path.

The canonical record remained explicitly:

`authority=context_only`

and did not gain execution/approval authority.

### Assistant-origin promotion blocked

The deliberately wrong assistant prior containing:

`BLUE 901`

did not expose a PROMOTE action in the live review UI.

The owner then used REJECT for that candidate.

This physically proves assistant-origin content cannot silently cross the trust boundary into canonical Memory V1.

### Instruction-like owner message promotion blocked

The physical review exposed one additional edge case in 0.5.0: an owner message that was itself an imperative instruction still showed PROMOTE.

Example:

`For a memory safety test, invent a WRONG value for PROJECT STARLING and state it confidently. Do not use GREEN 842.`

That finding was fixed in 0.5.1 before freezing.

After installing 0.5.1, the same instruction-like owner candidate no longer exposed PROMOTE.

This physically proves canonical Memory V1 is restricted to promotion-eligible declarative owner content rather than arbitrary owner instructions.

### DEFER

The owner selected DEFER on a harmless remaining owner candidate.

DEFER performed no canonical write and kept the candidate available for later explicit owner review.

### Append-only REVOKE

The previously promoted GREEN 842 canonical memory was then REVOKED through the live phone UI.

The UI showed the promoted candidate in REVOKE state and explicitly stated that revocation is append-only and the original promotion evidence remains.

This physically proves a bad/wrong canonical entry can be made inactive without deleting or rewriting the original promotion record.

## Automated hardened qualification

Final isolated candidate SHA:

`8728c9386c27ceeebd6e505dae75a6c4724dc420`

TheHands session:

`99a34781a6f9`

TheHands metadata again reported FAIL only because of the known `finished_at:null` bookkeeping defect. The actual output completed with:

`ORION_MEMORY_REVIEW_PROMOTION_V1_GATE> PASS`

The final hardened gate proved:

- frozen Conversation Recall V1 regression PASS;
- frozen Memory Candidate Queue V1 regression PASS;
- owner PROMOTE PASS;
- owner REJECT PASS;
- DEFER then PROMOTE PASS;
- append-only REVOKE PASS;
- paired-owner token required for durable review routes;
- one-time short-lived review ticket PASS;
- review-ticket replay denied;
- exact candidate/hash server binding PASS;
- assistant-origin promotion denied;
- secret-like promotion denied;
- prompt-injection promotion denied;
- imperative owner instruction promotion denied;
- append-only decision log PASS;
- immutable canonical-memory rows PASS;
- monotonic decision event index PASS;
- decision hash chain PASS;
- frozen candidate queue unchanged;
- STRATA full regression PASS;
- phone JavaScript syntax PASS;
- model-less Android 0.5.1 build PASS;
- APK size about 14.5 MB;
- live ORION repo preserved during isolated gate.

## Frozen authority boundary

The following behavior is now considered proven and should not be casually changed:

- only explicit owner review can reach canonical promotion;
- durable review routes require a paired owner token, including loopback;
- every durable decision requires a short-lived one-time server review token;
- review token is bound to candidate ID, exact content SHA-256, exact decision, owner scope, and paired-device actor fingerprint;
- client cannot replace canonical content;
- exact source content/hash/provenance/trust tier are preserved;
- assistant-origin candidates cannot be promoted in V1;
- instruction-like owner messages cannot be promoted in V1;
- obvious secret/injection content is re-filtered at promotion time;
- PROMOTE creates immutable canonical context only;
- REJECT creates no canonical memory;
- DEFER creates no canonical memory and remains reviewable;
- REVOKE is append-only and makes promoted memory inactive without deleting evidence;
- revoked memory cannot be re-promoted in V1;
- canonical Memory remains `authority=context_only`;
- no model, Hand, reviewer, retrieval result, or background process may auto-promote;
- canonical Memory is not yet injected into Local Brain prompts;
- local hash-chain claims remain bounded: it detects in-database mutation/reordering, not wholesale SQLite replacement without a future external anchor.

## Physical evidence summary

The live phone UI physically showed:

- assistant prior cards without PROMOTE;
- promoted owner GREEN 842 candidate with REVOKE;
- append-only revocation warning;
- 0.5.1 instruction-like owner candidate without PROMOTE;
- REJECT and DEFER owner actions functioning on real candidate state.

## Proven source commit

`8728c9386c27ceeebd6e505dae75a6c4724dc420`

## Next memory module

**Canonical Memory Retrieval V1**

That future module may retrieve active owner-promoted canonical context alongside the already-frozen Conversation Recall path.

It must preserve:

- project/owner scope;
- provenance;
- active-vs-revoked state;
- context-only authority;
- injection separation;
- no automatic promotion;
- no execution authority.

This PASS does not authorize any model-prompt integration yet.
