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


## L2 integration update — regression gate FAIL before activation

Attempted L2 chat-routing update failed during the updater regression wall before activation.

Observed on Android Settings:
- Update FAILED
- traceback reported
- previous ORION recovery attempted

Root cause in the staged L2 patch:
- the new integration regression expected durable prompt items to expose an explicit `status="current|historical"` label;
- the durable prompt renderer text described current/historical semantics but omitted the actual status attribute;
- therefore the canonical-memory integration regression failed as designed and the updater recovered the previous ORION build.

Bounded repair:
- emit the existing item status on `ORION_DURABLE_ITEM` prompt records;
- no storage, promotion, recall, supersession, Android, updater, or authority behavior changed;
- repair commit: `53b81620ce9d73a631a68bab1d3c07386c390689`.

Classification: regression gate FAIL / rollback PASS. Re-run required before L2 physical qualification.


## L2 retry — second regression block; integration restored to last proven baseline

A second L2 update attempt was also blocked by the updater regression wall before activation.

Because the phone browser cannot access authenticated update diagnostics without the paired owner token, ORION security was not weakened to expose the update log.

Professional recovery decision:
- stop layering patches onto the failed L2 integration attempt;
- restore `canonical_memory_integration.py` and its integration test to the last physically proven baseline from checkpoint commit `bb942cf840320f9971b11057be3837392ae4a42d`;
- keep all already-proven L0/L1, duplicate consolidation, stale-recall fusion, conflict detection and supersession behavior;
- redesign L2 as a smaller isolated follow-up rather than risking the proven current-memory path.

Restore commits:
- `512743d06d40cc6e58811dbd1be3be341b678ec6` — proven integration baseline restored
- `0416fa2a56427f17976fa13bf50441229aed305a` — proven integration regression baseline restored

Status: L2 historical chat routing remains NOT PASSED / NOT FROZEN.


## Proven-baseline recovery update — physical PASS

After restoring canonical-memory integration and its regression test to the last physically proven baseline, the owner ran Settings -> Update ORION before seeing the diagnostic prompt.

Physical Android evidence showed:
- ORION PC: connected;
- Update ORION: PASS;
- message: "ORION PC restarted; latest Android APK is ready to install."

Interpretation:
- source rollback/recovery to the proven memory integration completed successfully;
- ORION runtime restarted successfully;
- remote phone connection recovered;
- no Android code changed in the baseline restore, so APK reinstall is not required for this recovery step.

Result: **PROVEN MEMORY BASELINE RESTORE — PASS**.

L2 historical chat routing remains isolated as the only unfinished Memory Hierarchy V1 gate.


## Proven baseline sanity retest after rollback — PASS

After the restored baseline update passed, the first retest accidentally used the phone-local model and therefore had no access to PC canonical memory. This was correctly identified as a model-selection issue, not a Memory failure.

Owner then selected the PC model and asked:
- "What mode do I prefer for ORION?"

Physical result:
- model pill: PC · Qwen3.5
- ORION answer: "Based on the owner-approved durable memory in your context, you prefer dark mode for ORION."
- no stale light-mode conflict surfaced;
- superseded prior memory did not leak into current recall.

Result: **CURRENT CANONICAL RETRIEVAL BASELINE AFTER ROLLBACK — PASS**.

The current-memory path remains frozen/proven. L2 historical chat routing is the only unfinished hierarchy gate and must be rebuilt separately.


## Isolated historical-memory query module — updater gate PASS

A new read-only L2 historical query module was introduced separately from the proven L1/current-memory integration.

Module contract:
- historical intent is deterministic (previously / before / earlier / history / prior / used to);
- starts from the already-proven current durable retrieval result;
- walks the append-only supersession ledger backwards;
- returns superseded canonical records as historical context only;
- preserves candidate/source and supersession provenance;
- does not mutate canonical rows, decisions, recall, or supersession events;
- current-memory chat integration remains unchanged.

Regression fixture proves:
- current anchor = dark mode;
- historical expansion = prior light mode;
- supersession provenance preserved;
- canonical rows mutated = NONE;
- authority = context only.

Relevant commits:
- `e3622f04fe7a83100bd1b88a49dc598f65de15f3` — isolated historical query module
- `c4b90b809aceb789d5d6f5578edcf874e5f2be16` — isolated historical query regression
- `c040c930cb14b62516f9e44fcdd2de80ca8b0ed8` — updater gate inclusion

Physical updater evidence:
- Android Settings showed Update PASS;
- ORION PC restarted successfully;
- PC remained connected.

Result: **ISOLATED L2 HISTORICAL QUERY FOUNDATION — PASS**.

Next: connect this already-tested read-only result to Qwen as a separate historical context block without changing L1 retrieval.


## Isolated L2 history -> Qwen integration — updater PASS

The safer L2 integration was connected only after the isolated historical-memory module passed independently.

Integration properties:
- normal L1/current-memory path remains unchanged;
- explicit historical questions only invoke the isolated read-only history module;
- historical records are injected in a separate historical durable block;
- current durable memory remains the effective present context;
- historical expansion has a separate bounded context budget;
- historical lookup failure is nonfatal to current-memory answering;
- no Android code changed.

Regression coverage proves:
- normal current query does not call history;
- historical query calls the isolated history reader;
- current dark-mode durable memory remains present;
- prior light-mode memory is injected once as historical;
- historical item is explicitly labeled historical and linked to its superseding memory;
- owner current message remains last;
- history failures do not break current durable memory.

Relevant commits:
- `e84ed89c95834e6fbd577a264ff06e3e0effa1c5`
- `0d44ee07a47f2dbde08ceec9d83ea6f8bcfe65de`
- `cce5b0de321ca8a9234ad8622de21f1e266fc8c3`
- `f97f5d2f9f599a174ebfd6873b75544fa7df1e0b`

Physical updater evidence:
- Android Settings showed Update PASS;
- ORION PC restarted;
- PC remained connected.

Result: **ISOLATED L2 -> QWEN INTEGRATION GATE — PASS**.

Final physical semantic qualification still required.
