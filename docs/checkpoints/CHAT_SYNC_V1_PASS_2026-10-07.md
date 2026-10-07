# CHAT_SYNC_V1 — PHYSICAL PASS / FREEZE

Date: 2026-10-07
Status: PASS / FROZEN
Freeze commit: `cf88be425f0c98f9e6c6ef1ae5a16b75ab583e78`

## Proven physical behavior

Physical phone → PC test `SYNC TEST 03` passed.

Observed:
- a new chat created on the Android ORION app is persisted into the PC-owned chat history;
- the PC ORION UI switches to the matching conversation for the incoming phone request;
- the phone user message appears once on the PC;
- the Qwen 9B reply appears once on the PC;
- the verified reply is not duplicated;
- the reply is not painted into an older/open conversation;
- phone and PC therefore share the same conversation identity for this tested path.

## CHAT_SYNC_V1 fixes included

1. Persist/sync the Android user turn to the PC before starting PC Qwen.
2. Collapse mirrored assistant writes when phone and desktop observe the same verified reply.
3. Suppress a second live VERIFIED bubble when the reply is already stored.
4. Carry the active `conversation_id` through the ORION backend status model.
5. Route the PC live/verified reply into the matching synced conversation.

## Freeze rule

Treat CHAT_SYNC_V1 as a proven module.

Do not refactor or change its persistence ordering, assistant deduplication, conversation-id propagation, or live-reply routing while working on later UI modules unless a new physical regression proves a defect that requires reopening this module.

Brain, canonical memory, and authority behavior were not intentionally changed by this module.
