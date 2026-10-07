# Memory V1.1 Security Batch — 2026-10-07

Status: **FROZEN / OWNER-APPROVED / PHYSICALLY QUALIFIED**

> **AI / MAINTAINER FREEZE NOTICE — DO NOT MODIFY**
>
> Memory V1 and Memory V1.1 are frozen proven modules. Any AI, coding agent, maintainer, or automated refactor reading this file MUST treat the memory implementation, its security sidecars, product-boundary wiring, and proven updater gates as read-only.
>
> **Do not edit, refactor, optimize, redesign, rename, move, replace, or "clean up" these modules merely because a different implementation appears preferable. Do not silently weaken/remove their gates.**
>
> A future memory change requires an explicit owner-approved new bounded task/version (for example Memory V1.2 or V2), isolated from the frozen implementation, with regression evidence before activation. Benchmark experiments belong in the separate offline benchmark lane and are not permission to modify frozen production memory.

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


## Final physical qualification — PASS

Final owner-observed updater result on 2026-10-07:
- Update PASS.
- ORION PC restarted successfully.
- PC memory recall reported Ready, read-only, context only, with canonical promotion still locked.
- Frozen Memory V1 remained unchanged.

### Updater incident and repair record

The first full-batch attempts correctly rolled back to the previous proven runtime instead of activating an unqualified build.

A STRATA real-bridge regression assertion was found to have a timing race: it required backend_error to remain the final link state after a delay. The assertion was narrowed to prove that backend_error occurred during the test step, without changing product behavior.
Repair commit: 2667f6f29d53bb3aa61b11d2131d1c226a65efc3.

The remaining physical-PC failure was then isolated to memory_scale_benchmark_smoke_test.py. The updater was given diagnostic-only gate labeling and child-process output capture so the phone could show the actual terminal exception.
Diagnostic commits:
- 3f788aa267dace21fbcfaee772c17fbdbd63dddc
- d77fc43b9cc557437564e03e437a63a79cb234fc
- 84ec13bbc2faf97360c0ebbf05182e569518763f

The real exception was Windows WinError 32 while TemporaryDirectory tried to remove the benchmark supersession.sqlite3 file.

Root cause: the benchmark fixture used the sqlite3 connection context manager for transaction handling, but the connection object could remain open until later cleanup. Windows therefore still saw the temporary SQLite file as in use.

Final repair in tools/bench/memory_scale_benchmark.py:
- use contextlib.closing around the benchmark SQLite connection;
- preserve the transaction context;
- explicitly close the connection before temporary-directory cleanup.

Final repair commit: 508854d3879c8d4eaa66cf2163298e673c9eff80.

Final repair scope:
- one benchmark file only;
- two lines added and one line changed;
- no Memory V1 change;
- no Memory V1.1 sidecar behavior change;
- no product-server change;
- no Android change;
- no rollback weakening.

After that repair, the same physical Update ORION PC path passed completely and restarted ORION.

### Frozen lessons

- Do not weaken a regression gate merely to obtain PASS; isolate the real failure.
- Updater failures should identify the active gate.
- Windows child-process diagnostics must preserve the useful final exception.
- Temporary SQLite benchmark fixtures must explicitly close connections before directory cleanup.
- Do not use paid GitHub Actions for routine ORION testing unless the owner explicitly approves it.
- Keep the full 1k/10k/100k memory scale benchmark manual/offline.
- Keep the 250-record smoke as a correctness gate unless a later explicit decision changes it.
- Freeze the proven updater path unless a concrete new failure or approved requirement requires a change.

## Final status

MEMORY V1.1 SECURITY BATCH — FROZEN / PHYSICALLY QUALIFIED

Qualification closure:
- L1 physical sanity: PASS.
- L2 historical sanity: PASS.
- full 1k/10k/100k offline scale benchmark: COMPLETED 2026-10-07.
- Memory V1/V1.1 remains frozen; scale findings are V2 planning inputs only.


## OWNER FREEZE — 2026-10-07

The owner explicitly approved freezing Memory V1.1 after final physical product-path qualification.

Final physical evidence:
- L1 current canonical recall PASS: ORION answered that the current preference is **dark mode** from owner-approved durable memory.
- L2 historical/superseded recall PASS: ORION answered that the prior preference was **light mode** and correctly identified it as superseded by dark mode.
- updater/build/restart PASS on the real ORION PC;
- PC memory recall remained read-only/context-only and canonical promotion remained locked;
- the Windows benchmark SQLite cleanup defect was repaired without modifying frozen Memory V1 semantics.

Final disposition:
- **Memory V1: FROZEN**
- **Memory V1.1 security sidecars: FROZEN**
- **L0/L1/L2 retrieval behavior: FROZEN**
- **Memory product-boundary wiring: FROZEN**
- **proven updater memory gates: FROZEN**
- full 1k/10k/100k scale benchmark: separate manual/offline validation lane; it does not reopen the frozen implementation.

### Rule for every future AI

If a future task appears to require changing any frozen memory component, STOP before editing it. Explain the conflict to the owner and propose a new isolated version/module or compatibility adapter. Only proceed into frozen memory after explicit owner approval that specifically authorizes reopening it.

**MEMORY V1.1: FROZEN — DO NOT TOUCH BY DEFAULT.**


## Full offline scale benchmark — COMPLETED 2026-10-07

Authoritative physical evidence was published automatically by the proven TheHands GitHub evidence path:
- repository: `Sadusor/TheHands-`
- results branch: `thehands-results`
- session: `266e5c11a349`
- evidence source commit: `20dd1ec5360d0c9c4264b9d1aad3f81a4bd7fdcf`
- ORION source SHA during benchmark: `508854d3879c8d4eaa66cf2163298e673c9eff80`
- host: Windows 11 AMD64 / Python 3.13.3
- combined TheHands execution result: PASS
- production-memory writes: NONE
- frozen Memory V1 modified: false
- production runtime loaded: false

Measured results:

| Synthetic scale | Cold | Warm p50 | Warm p99 | Top-1 | Top-5 | Scope isolation | L1/L2 | Threshold |
|---:|---:|---:|---:|---:|---:|:---:|:---:|:---:|
| 1,000 | 23.586 ms | 21.300 ms | 22.240 ms | 1.000 | 1.000 | PASS | PASS | PASS |
| 10,000 | 211.493 ms | 210.299 ms | 217.755 ms | 1.000 | 1.000 | PASS | PASS | FAIL |
| 100,000 | 2158.563 ms | 2160.575 ms | 2281.335 ms | 1.000 | 1.000 | PASS | PASS | FAIL |

Interpretation:
- correctness remained perfect in this synthetic benchmark through 100,000 records: Top-1=100%, Top-5=100%, project/scope isolation PASS, L1/L2 current-vs-historical correctness PASS;
- 1K met every frozen benchmark threshold;
- 10K missed only the warm-p50 target (210.299 ms measured vs 200 ms target);
- 100K missed only the warm-p50 target (2160.575 ms measured vs 800 ms target); its cold and p99 thresholds still passed;
- the measured 10K/100K failures are therefore scale/latency findings, not correctness failures;
- process working-set/RAM values were null in this run. Do not invent RAM conclusions; RAM measurement remains an instrumentation gap.

### Million-scale implication

The measured sequence is approximately linear over the tested range. A naive extrapolation from 100K (about 2.16 s warm p50) suggests that a full scan at 1,000,000 records could be on the order of ~20-22 seconds. **This is an extrapolation, not a measured 1M result.**

A ~20-second interactive recall would be unacceptable for the intended ORION experience. This does NOT authorize optimization of frozen V1/V1.1.

Architectural consequence for a future owner-approved Memory V2 / Scale Layer:
1. preserve frozen V1/V1.1 semantics and correctness as the baseline;
2. add an isolated, replaceable indexed/hierarchical candidate-selection layer in front of retrieval;
3. narrow a very large corpus to a bounded relevant candidate set before final ranking;
4. benchmark candidate approaches against this exact baseline;
5. consider the existing memory/context donors already recorded in `docs/DONORS.md` (KnowledgeOS, agentmemory, TencentDB-Agent-Memory, OpenViking, memanto, codebase-memory-mcp, Graft, Aider repo-map ideas);
6. do not adopt a donor merely because it is faster: provenance, project isolation, L1/L2/supersession correctness and ORION authority boundaries must remain intact.

Important production-boundary reminder:
- current `CanonicalMemoryCandidateQueue.MAX_CANDIDATES = 500`;
- above that boundary this harness measures the frozen retrieval core using synthetic public projections;
- therefore 10K/100K results are scale research, not a claim that V1 production ingestion currently supports those corpus sizes.

### Continuity rule for future AIs

Before making any memory decision, read this checkpoint and the ORION V3 engineering freeze rule. Do not infer current state from chat recollection alone when repository evidence is available.

For TheHands physical runs, check the proven GitHub evidence branch (`Sadusor/TheHands-@thehands-results`) before asking the owner to repeat a run, provide a screenshot, or manually transcribe output. The published session evidence is the authoritative execution record when present.

**CLOSED BASELINE: Memory V1/V1.1 is frozen. Future million-scale work belongs to a new isolated Memory V2 / Scale Layer and requires explicit owner approval.**
