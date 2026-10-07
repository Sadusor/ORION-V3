# Canonical Memory Retrieval Integration V1 — Physical PASS

Date: 2026-10-07  
Status: **PHYSICAL PASS / FROZEN CANDIDATE**

## Scope

This gate qualified the integration-only layer that combines:

- frozen Conversation Recall V1;
- frozen Canonical Memory Retrieval Foundation V1;
- current-conversation context from the Android client;
- the exact current owner message.

It did **not** connect the integration to `product_server.py` / live Qwen yet.

Qualified source branch:

`feature/canonical-memory-retrieval-integration-v1`

Qualified exact source SHA:

`2c9e3c85205827b7da2f0c0e7e6c123e7307220a`

Merged to main through PR #9:

`393969cf8e726f7ccb4a5e1de4018712154c0b11`

## Physical TheHands evidence

Hand:

`PowerShell 1 · MAIN · MEMORY INTEGRATION GATE`

TheHands session:

`480f578835bc`

Published evidence commit:

`bfcb0680263b98a29dfe8cdc682b6f762b5febfb`

Result:

**PASS**

The qualification worktree lived on:

`E:\ORION-WORK\canonical-memory-integration-v1-2c9e3c852058`

and was removed successfully after the gate.

## Qualified integration behavior

All 20 adversarial integration tests passed.

Proven properties:

- non-Android `memory_query` remains a retrieval hint and does not replace the owner directive;
- the exact Android latest owner message is isolated from the legacy local-history wrapper;
- current-conversation transcript is context-only;
- owner current message remains the final directive block;
- conversation recall and durable memory remain structurally separate;
- duplicate/overlapping memory does not gain authority;
- durable memory never exceeds 40% of the 4000-character memory budget;
- unused durable budget may flow to recall;
- one retrieval source may fail without blocking the owner request;
- both retrieval sources may fail and the owner request still proceeds;
- exact project scope and current-conversation exclusion are forwarded;
- retrieved body text and metadata are escaped against prompt-structure injection;
- revoked/tampered durable rows are rejected again at prompt assembly time;
- unresolved durable scope fails closed;
- all-filtered memory injects no fake context;
- conflicts are surfaced rather than silently resolved;
- prompt assembly is deterministic for identical inputs.

## Failure history retained as evidence

Attempt 1:

- source SHA `2910c7839ec6ff9fead637c84e973ac1db409139`
- TheHands session `e6cb6f467aed`
- failed test 02 because the Android wrapper detector matched literal `\n` text instead of real newlines.

Attempt 2:

- source SHA `937defd0b91552b1ed237c57771f2c5b33a77267`
- TheHands session `cf672eb6285f`
- tests 01–08 passed;
- failed test 09 because clipped context budget accounting omitted two newline characters, causing a clipped item to be discarded.

Both defects were fixed only in the integration module/tests. Frozen memory modules remained unchanged.

## Frozen regression results

PASS:

- `memory_retrieval_test.py`
- `memory_retrieval_adversarial_test.py`
- `memory_brain_pipeline_test.py`
- `memory_candidate_queue_test.py`
- `memory_review_promotion_test.py`
- `canonical_memory_retrieval_foundation_test.py`

The qualification worktree finished clean.

## Authority statement

Memory remains:

`authority=context_only`

Durable memory remains:

`owner-approved durable context, not verified truth`

No memory source can grant execution authority, approvals, permissions, STOP bypass, capability expansion, or policy changes.

## Next bounded task

Wire the qualified integration wrapper into the product Local Brain/Qwen path through the smallest possible hook, without editing the frozen retrieval/promotion/candidate/foundation modules.

