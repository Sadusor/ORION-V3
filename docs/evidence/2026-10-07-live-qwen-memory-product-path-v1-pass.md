# Live Qwen Memory Product Path V1 — Physical PASS

Date: 2026-10-07  
Status: **PHYSICAL PASS**

## Purpose

Prove that the real local Qwen 9B receives both qualified memory sources through the actual ORION product route while the current owner message remains the directive.

This test used isolated temporary state on E: and did not touch the owner's live ORION chat, candidate, canonical-memory, pairing, or supersession databases.

## Qualified ORION source

Exact main SHA tested:

`74e394a0eec44a3e5f6c8f159d2cd923ad925e0c`

Product wiring source had already passed and been frozen before this gate.

## Physical TheHands evidence

Hand:

`PowerShell 1 · MAIN · LIVE QWEN MEMORY GATE`

TheHands session:

`3dc1b452496a`

Published evidence commit:

`4893c03988a3addc663775d2b5afe2402009f642`

Result:

**PASS**

## Isolation

Gate worktree:

`E:\ORION-WORK\live-qwen-memory-v1-74e394a0eec4\repo`

Temporary state:

`E:\ORION-WORK\live-qwen-memory-v1-74e394a0eec4\state`

Storage policy:

`E_DRIVE_ONLY`

The worktree and temporary state were cleaned after the gate.

## Ollama behavior

Ollama was initially not running.

The Hand found:

`C:\Users\SouS\AppData\Local\Programs\Ollama\ollama.exe`

It started a temporary `ollama serve`, waited for `/api/tags`, used the process only for the gate, and stopped the exact process it started after PASS.

Model physically used:

`qwen35-9b-orion:latest`

## Test markers

Owner-approved durable context:

`DURABLE-5831`

Conversation Recall context:

`RECALL-2746`

Current-chat-only context:

`CURRENT-9999`

The current owner request asked Qwen to return the durable and recall markers and not include the current-chat-only marker.

Physical Qwen reply:

`durable=DURABLE-5831; recall=RECALL-2746`

## Proven properties

PASS:

- real Qwen product path;
- owner-approved durable memory reached Qwen;
- Conversation Recall reached Qwen;
- current conversation remained context-only;
- current owner directive boundary held;
- current-chat-only marker was not returned;
- exact owner message isolation remained intact;
- live ORION persistent state was untouched;
- temporary Ollama lifecycle was cleaned up;
- E:-only temporary working/state paths were used.

## Meaning

The memory pipeline is no longer only structurally tested.

It is now physically proven end to end through the real local Qwen model:

`chat history -> recall retrieval + owner-approved durable retrieval -> separated context blocks -> current owner message last -> Qwen -> verified answer`

Memory remains context only. Durable memory remains owner-approved durable context, not verified truth.

## Next bounded task

Deploy the already-qualified main build to the live ORION runtime, then perform one simple phone-to-PC physical recall test against the owner's real app surface before declaring the complete memory retrieval path frozen for daily use.
