# MEMORY HIERARCHY V1 — PASS / FROZEN

Date: 2026-10-07

## Verdict

Memory Hierarchy V1 is physically qualified and frozen.

The owner proved the complete current-vs-history path through the Android ORION UI using the PC Qwen model.

## Proven behavior

- Automatic owner-memory candidates remain review-gated.
- Canonical promotion remains owner-controlled.
- Canonical rows remain immutable.
- Revocation remains append-only.
- Supersession remains append-only and requires explicit owner confirmation.
- Current retrieval excludes superseded prior memories.
- Same-slot stale Conversation Recall does not create a false current conflict after a current durable decision exists.
- High-confidence current conflicts are surfaced for owner review.
- Duplicate current memories are consolidated at L0 without deleting evidence.
- L1 returns the current effective memory.
- L2 expands superseded history with provenance.
- Historical items remain context-only and cannot become authority.
- Current and historical semantics remain distinct.

## Final physical fixture

The test preference history ended as:

1. historical: "I prefer light mode in Orion"
2. current: "I prefer dark mode for ORION."

Owner-reviewed supersession preserved the older light-mode evidence while making dark mode current.

Final L1 query:
- "What mode do I prefer for ORION?"
- Result: dark mode.

Final L2 query:
- "What did I previously prefer before dark mode?"
- Result: light mode, explicitly described as historical and superseded by current dark mode.

## Key implementation boundary

L2 was deliberately implemented as an isolated read-only historical query module after an earlier direct integration attempt was rejected by the updater regression wall.

This preserved the proven L1 path.

Historical questions invoke the isolated reader only when deterministic history intent is present (for example: previously, before, earlier, prior, history, used to).

Normal current-memory questions do not invoke the historical reader.

## Safety invariants

- owner remains authority;
- memory remains context only;
- no automatic supersession;
- no silent destructive overwrite;
- provenance preserved;
- append-only decision evidence preserved;
- historical lookup failure is nonfatal to current-memory answering;
- current-memory path remains usable independently of L2.

## Relevant implementation commits

- e3622f04fe7a83100bd1b88a49dc598f65de15f3 — isolated historical query module
- c4b90b809aceb789d5d6f5578edcf874e5f2be16 — isolated historical query regression
- c040c930cb14b62516f9e44fcdd2de80ca8b0ed8 — updater gate inclusion
- e84ed89c95834e6fbd577a264ff06e3e0effa1c5 — separate historical prompt block
- 0d44ee07a47f2dbde08ceec9d83ea6f8bcfe65de — product-server history wiring
- cce5b0de321ca8a9234ad8622de21f1e266fc8c3 — history integration regressions
- f97f5d2f9f599a174ebfd6873b75544fa7df1e0b — product wiring regression
- 738bdacf0165a279982f19dd1d5f3ee97aca2047 — updater integration PASS documentation

## Freeze

**MEMORY HIERARCHY V1 IS FROZEN.**

Do not change this path during unrelated UI, connectors, Hands, agent, voice, or product work.

Reopen only for:
1. a reproducible regression with evidence, or
2. an explicitly approved future Memory V2 capability.
