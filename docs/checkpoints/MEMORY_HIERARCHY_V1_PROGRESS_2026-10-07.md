# Memory Hierarchy V1 — Physical Progress — 2026-10-07

Status: IN PHYSICAL QUALIFICATION

## Physical evidence recorded

### L0 hierarchy surface — PASS
Owner physically checked the Android Settings -> Memory hierarchy surface after installing ORION 0.5.4.

Observed:
- L0 current items: 1
- duplicates consolidated: 0
- chars: 28
- L1 current / L2 history ready
- on-demand "Memory hierarchy checked" feedback visible

This proved the hierarchy route/UI plumbing before a duplicate fixture existed.

### Duplicate consolidation — initial FAIL
Owner promoted two semantically equivalent active canonical preferences:
- "I prefer light mode in Orion"
- "My preferred ORION mode is light"

The first physical hierarchy check reported:
- 2 active canonical memories
- L0 current items: 2
- duplicates consolidated: 0

Root cause: the deterministic preference-slot normalizer did not cover the phrase form
"value + dimension + in + target" (for example "light mode in Orion").

No canonical, promotion, retrieval-foundation, or frozen conversation-recall module was changed.

### Duplicate consolidation — repaired physical PASS
Normalization was extended only in the conflict/consolidation parsing seam and regression tests were added for the exact live phrase.

After PC update and connection refresh, owner physically checked Memory hierarchy again.

Observed:
- Canonical memory: 2 active canonical memories
- Memory conflicts: no unresolved high-confidence conflicts
- L0: 1 current item
- duplicates consolidated: 1
- chars: 32
- L1 current / L2 history ready
- visible "Memory hierarchy checked" feedback

Result: PASS.

## Safety / architecture properties preserved

- Canonical memory rows remain immutable.
- Duplicate consolidation happens at read/prompt time.
- No canonical row was deleted or rewritten.
- All source evidence remains available.
- No automatic promotion.
- No automatic supersession.
- No execution authority is granted by memory.
- Frozen Conversation Recall route remains unchanged.
- Hierarchy check is on-demand; no new background polling was added.

## Relevant implementation commits

- d696c6e772e97685ab44db6bfbc5e3b008bfab16 — read-only consolidation + L0/L1/L2 hierarchy
- 0c520046cf38a0e384a53dc8b7a6d5a8d03c9151 — hierarchy retrieval facade
- 72c7416075db7c6b50270e7c118b68e73d32dc63 — preserve frozen Conversation Recall search route
- f4dccdd457a1942bf8970c9de97e22a2444adcbe — expose L0 consolidation counts
- 2875fa35b60c1f99802873515846a115dd5347b0 — Android on-demand hierarchy check
- a00418edf2edb6f3c454f6cd6439bb424ddc7005 — hierarchy proof UI
- bb5396c004abee1928cde3f102db0fe072fe1385 — canonical memory regression wall in updater
- 2dc6c9e235c53e87a9494a3713b6f1ca4a743128 — live phrase normalization repair
- e5772341712dddc52620c7f80a03deb107b08c20 — conflict phrase regression
- 64342d590593c5e17d823fba1e51537e07479861 — duplicate phrase regression

## Remaining physical gates before Memory V1 freeze

1. L1 current retrieval after consolidation: model should receive/use one effective current fact, not duplicate context.
2. Supersession/conflict owner-review flow with two genuinely conflicting active memories.
3. L2 historical/provenance expansion verification.
4. Final bounded stress/adversarial pass: duplicate, contradiction, scope, typo, restart persistence and context budget.

Do not freeze Memory Hierarchy V1 until these remaining gates are physically evidenced.


## Remote connectivity interruption during physical qualification

During the L1 physical test the Android app intermittently fell back to LOCAL even though the PC backend remained reachable.

Isolation evidence:
- Android refresh alone did not reliably recover immediately.
- ZeroTier was restarted once during diagnosis.
- While the app showed connection problems, Chrome on the same phone successfully reached `http://10.109.233.27:8890/api/health` and ORION returned `ok: true`.
- This isolated the observed failure away from Memory and the PC backend.

Bounded fix:
- Android ORION health timeout increased only from 1800 ms to 4000 ms.
- No backend, Memory, updater, ZeroTier logic, or frozen module was changed.
- commit: `1496abbb6b9d22716f896ad70aa7c3df1e77377a`

Physical result after update + APK install:
- phone reconnected to PC;
- remained connected during a short idle stability observation;
- owner reported: "It's seems fine".

Classification: remote-health-timeout stability PASS for this observation. If the disconnect recurs, reopen it as a separate connectivity issue rather than altering Memory.


## L1 current retrieval after consolidation — initial FAIL then repaired PASS

Initial physical L1 query:
- owner asked: "What mode do I prefer for ORION?"
- durable canonical context correctly contained the current light-mode preference;
- ordinary Conversation Recall still surfaced an older dark-mode owner statement;
- the existing fusion safety contract therefore surfaced an unresolved conflict and asked the owner to clarify.

Classification:
- canonical L1 retrieval itself was correct;
- failure was in fusion semantics between current durable memory and stale same-slot Conversation Recall.

Bounded repair:
- only the canonical-memory integration/fusion layer changed;
- frozen Conversation Recall storage/retrieval was not changed;
- canonical storage was not changed;
- for deterministic owner preference/naming slots only, an older owner recall statement mapping to the same slot as current owner-approved durable memory is omitted from the prompt as historical context;
- unrelated recall remains available;
- generic conflicts that cannot be proven to share the same deterministic slot still surface normally;
- history remains retrievable in L2/provenance expansion;
- no authority change.

Relevant commits:
- `7bb0dcf3845117cc34556c01845c4e57fc95fcfa` — same-slot stale recall shadowing at fusion
- `77dd5dfd37187ef7dc1fd9cb3dff0657d3d4f2cf` — regression for current durable vs stale recall

Physical retest:
- owner asked again: "What mode do I prefer for ORION?"
- ORION PC replied: "Based on the owner-approved durable memory in your context, you prefer light mode in ORION."
- no dark/light clarification requested;
- no duplicate/repeated memory surfaced;
- PC connection remained active during the test.

Result: **L1 CURRENT RETRIEVAL AFTER CONSOLIDATION — PASS**.


## Owner-reviewed supersession flow — physical PASS

Physical fixture:
- one active light-mode canonical preference remained current;
- owner promoted a newer dark-mode canonical preference;
- one duplicate light preference had been revoked by the owner separately;
- after refresh, conflict detector showed exactly 1 unresolved personal-scope conflict.

Conflict review UI physically showed:
- OLDER MEMORY: "I prefer light mode in Orion"
- NEWER MEMORY: "I prefer dark mode for ORION."
- action: "Use newer memory · preserve old evidence"
- explicit confirmation dialog stated the older memory would remain preserved as historical evidence.

Owner confirmed the action.

Post-confirmation physical refresh:
- Memory conflicts: 0 unresolved high-confidence conflicts;
- Memory hierarchy: L0 1 current item;
- duplicates consolidated: 0;
- L1 current / L2 history ready;
- raw canonical promotion store still reported 2 active promoted records, as expected because supersession is represented in a separate append-only relation ledger and canonical rows are immutable.

Result: **OWNER-REVIEWED SUPERSESSION FLOW — PASS**.

Architecture evidence:
- no automatic supersession;
- explicit owner confirmation required;
- older canonical evidence preserved;
- no canonical row mutation/deletion;
- current retrieval/hierarchy excludes superseded prior memory;
- raw promotion-store counts remain distinct from current-effective-memory counts.

UX note for later UI polish:
- "active canonical memories" reflects immutable promotion state and can look confusing after supersession.
- Consider wording such as "promoted records" plus a separate "current effective memories" count without changing storage semantics.
