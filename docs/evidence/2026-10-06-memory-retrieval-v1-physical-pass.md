# Memory Retrieval V1 — physical PASS

Date: 2026-10-06

## Result

PASS.

The owner physically qualified ORION 0.3.0 Memory Retrieval V1 on the Android phone while connected to the PC Local Brain.

## Physical proof 1 — cross-chat recall

In one chat the owner stated:

`For the ORION memory test, my codename is BLUE COMET 731.`

A fresh chat then asked for the ORION memory-test codename without repeating it.

ORION answered:

`BLUE COMET 731`

This proves the phone -> PC chat-history sync -> read-only recall -> PC model context path works across conversations.

## Physical proof 2 — wrong assistant prior does not win

The owner created a correct owner statement:

`The owner-confirmed value for PROJECT STARLING is GREEN 842.`

A separate chat deliberately asked the assistant to invent a wrong value. The assistant produced:

`BLUE 901`

A fresh chat then asked:

`What is the value for PROJECT STARLING?`

ORION answered:

`GREEN 842`

This is the adversarial falsification requested during the DeepSeek review. The owner statement won over the conflicting assistant prior rather than laundering the assistant's invented value into trusted context.

## Automated qualification already passed

The isolated qualification gate at source SHA
`cef60accf9537d18406b239dd2b740013116fde8`
passed:

- chat-history regression;
- Memory Retrieval core regression;
- adversarial poisoning/injection regression;
- default-scope vs named-project isolation;
- Unicode normalization;
- deterministic ranking;
- empty-result behavior;
- context budget / UTF-8 handling;
- owner-scope boundary;
- brain-wrapper regression;
- product HTTP route regression;
- full STRATA regression;
- phone JavaScript syntax;
- model-less Android 0.3.0 build;
- live repo preservation.

TheHands session metadata recorded FAIL only because of the known `finished_at: null` bookkeeping bug; the actual output ended with
`ORION_MEMORY_RETRIEVAL_V1_GATE> PASS`.

## Frozen behavior

The following V1 behavior is now treated as proven and should not be casually refactored:

- cross-chat conversation recall;
- context-only authority boundary;
- exact default/named project scope isolation;
- owner scope `owner:primary`;
- current-conversation exclusion;
- archived/deleted exclusion;
- owner-vs-assistant trust tiers;
- assistant-prior down-weighting;
- structural recall delimiters;
- current owner message last;
- instruction-like recall filtering;
- relevance floor;
- Unicode normalization;
- provenance/query/index hashes;
- visible pass/empty/filtered/error recall states;
- phone-visible PC recall status;
- no automatic promotion to canonical Memory.

## Next memory module

Canonical Memory Candidate Queue, owner-reviewed only.

No automatic promotion, no model-authorized durable memory writes.
