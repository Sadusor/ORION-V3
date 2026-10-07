# Memory V1.1 Security Batch — 2026-10-07

Status: BUILT / AWAITING ONE PHYSICAL UPDATE GATE

Memory Hierarchy V1 remains frozen. This batch adds sidecars and an offline benchmark harness only.

## V1.1a — Integrity Anchor

New sidecar:
- `src/orion_v3/modules/memory_integrity_anchor.py`

Purpose:
- detect rollback, unknown durable-state replacement, broken internal append-only chains, and local anchor-chain corruption;
- keep reads available while unsafe durable writes are frozen;
- allow explicit paired-owner re-anchor recovery;
- never rewrite canonical Memory V1 state.

Important honesty:
- this first anchor is local tamper evidence, not a fully independent external trust anchor;
- an attacker who can rewrite both the durable DBs and the sidecar files can defeat it;
- a GitHub/USB/second-device mirror remains a later hardening option.

Physical status:
- isolated gate PASS;
- live product-boundary wiring PASS.

## V1.1b — Shadowing Audit

New sidecar:
- `src/orion_v3/modules/memory_shadow_audit.py`

Purpose:
- observe only shadowing decisions already made by frozen V1;
- write detailed evidence for old recall vs current durable same-slot matches;
- never decide whether to shadow;
- never alter Qwen prompt content;
- never block Qwen;
- do zero extra retrieval work when frozen V1 reports zero shadowed items;
- bounded JSONL rotation with retention.

Live wiring is only at the product-server boundary after prompt composition.

Physical status:
- isolated module built;
- product-boundary wiring built;
- awaiting the single batched updater gate.

## V1.1c — Scale Benchmark Harness

New offline harness:
- `tools/bench/memory_scale_benchmark.py`

Target scales:
- 1,000
- 10,000
- 100,000 canonical records

Measures:
- cold/warm retrieval latency;
- p50/p99 latency;
- process working set;
- candidate counts;
- top-1 accuracy;
- top-5 recall;
- project-scope isolation;
- L1 current vs L2 historical correctness.

The full benchmark is manual/offline and is never loaded by normal ORION runtime. The updater runs only a tiny smoke fixture.

## Important scale discovery

While building the harness we confirmed a current V1 production constraint:

- `CanonicalMemoryCandidateQueue.MAX_CANDIDATES = 500`;
- canonical retrieval obtains provenance through that candidate source.

Therefore the present production ingestion path is intentionally bounded to roughly 500 queued/canonical source candidates. A 1k/10k/100k benchmark cannot honestly claim that current V1 production ingestion supports those scales.

The harness explicitly reports this boundary. Above 500 it benchmarks the frozen canonical retrieval algorithm using synthetic public projections so we can learn where retrieval itself bends or breaks before designing V2.

This is not a V1 regression. It is a documented V1 scale boundary and a V2 planning input.

## Batch update rule

Do not ask the owner to perform separate updater cycles for each small sidecar.

This V1.1 batch is qualified through one combined updater run covering:
- integrity regressions;
- integrity product wiring;
- shadow-audit isolated regression;
- shadow-audit product wiring;
- scale-benchmark smoke;
- all existing Memory V1 regression walls;
- STRATA/build/restart verification.

No Android code changed in this batch.


## Physical batched updater qualification — PASS

The owner performed one combined ORION update after V1.1a/V1.1b/V1.1c were batched.

Android Settings showed:
- **Update PASS**
- ORION PC restarted successfully
- phone remained connected to ORION PC

The updater gate included:
- Memory V1.1a integrity-anchor isolated regression;
- integrity product-boundary wiring regression;
- Memory V1.1b shadow-audit isolated regression;
- shadow-audit product-boundary wiring regression;
- Memory V1.1c offline scale-benchmark smoke gate;
- all existing Memory V1 regression walls;
- STRATA regression/build/restart verification.

Result: **MEMORY V1.1 SECURITY BATCH — UPDATER PASS**.

No Android code changed in this batch, so no APK installation is required.

Remaining qualification:
- one bounded normal L1 physical sanity check;
- one bounded historical L2 sanity check if needed;
- then run the full manual 1k/10k/100k scale benchmark separately because it is intentionally not part of normal updater/runtime.


## Batched updater attempt — FAILED / RECOVERED

The first actual attempt to install the full Memory V1.1 batch failed in the updater regression gate and ORION recovered the previous proven runtime.

Important correction:
- an earlier screenshot showing Update PASS belonged to the previous integrity-only runtime;
- `/api/health` proved the running commit was still `03e8bb62c633af0432cdf610595810f44cffce7e`;
- therefore the full V1.1 batch had NOT yet been installed.

Root cause found in the new product-wiring regression fixture, not in Memory V1 behavior:

The fixture contained:
1. an older same-slot dark-mode recall statement; and
2. the source chat statement that had been promoted into the current light-mode durable memory.

Frozen V1 correctly shadowed both recall items:
- one same-slot older-value item;
- one same-slot same-value duplicate.

The new test incorrectly asserted that exactly one item would be shadowed, causing an AssertionError / traceback and correctly blocking the update.

Repair:
- product-wiring test now derives the expected shadow count from frozen V1;
- requires at least one older-value shadow;
- requires the audit sidecar to write exactly the same number of observed events;
- verifies the stale dark -> current light event explicitly;
- no Memory V1 module or shadowing algorithm changed.

Repair commit:
- `1587df1a360907700c52f99201933100a8eadbae`

Status: **FULL MEMORY V1.1 BATCH STILL AWAITING PHYSICAL UPDATER PASS**.
