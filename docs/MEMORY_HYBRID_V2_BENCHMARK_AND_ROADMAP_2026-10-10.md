# ORION V3 — Memory Hybrid V2: evidence, safety boundary and next roadmap
Date: 2026-10-10. Status: **EXPERIMENTAL SIDE-CAR ADDED; INTEGRATION NOT APPROVED OR TESTED**.

## Owner rules
- Memory V1, canonical promotion, supersession, integrity anchors and all frozen production modules remain untouched.
- Neither Forge nor OpenViking nor TheHands product is part of the ORION memory authority. TheHands can transport developer test commands only.
- Synthetic test datasets are disposable, but DO NOT remove user/project memory, SQLite stores, OpenViking `memory-data`, or existing benchmark evidence without explicit evidence-backed approval.
- Indexes may be dropped and rebuilt **only in dedicated experimental locations**, not canonical databases.
- Returned candidate IDs are not trusted prompt context. Revalidate each hit against the canonical memory, revocation/supersession ledger, project scope, provenance, owner permissions, budget and risk gates before use.

## Evidence from verified TheHands runs (2026-10-10)
| Workload | Median ms | Accuracy | Notes |
|---|---:|---:|---|
| ORION existing canonical retriever, 1K | 21.16 | 20/20 | synthetic fixture; existing retrieval core |
| ORION existing canonical retriever, 10K | 213.299 | 20/20 | median threshold FAILED |
| ORION existing canonical retriever, 100K | 2199.188 | 20/20 | median threshold FAILED |
| SQLite FTS5 side experiment, 100K | 0.0695 | 50/50 | in-process index only, not full authority path |
| SQLite FTS5 side experiment, 500K | 0.0826 | 50/50 | index 79.148 MB, built in 2052.42ms |
| SQLite FTS5 side experiment, 1M | 0.0861 | 50/50 | index 157.227 MB, built in 4232.09ms |
| Semantic nomic-embed-text, 10 facts | 12.827 | 10/10 | query embedding included; tiny in-memory semantic corpus |
| OpenViking 86 similar resources, search | 18.43 | top1 12/86; top5 37/86 | HTTP search, distinct workload |

The 100K final hybrid component demonstration: FTS5 exact lookup p50 0.086ms, p95 0.104ms, p99 0.245ms; semantic query p50 12.827ms and p95 29.097ms, all 10/10; project filtering passed in synthetic tests. This was **NOT** full integrated hybrid retrieval on a 100K-vector corpus.

Original ORION vs FTS5 measurements are **not apples-to-apples**: the latter skips canonical retrieval overhead, authority verification, ranking/candidate joins and provenance checks. The test queries have distinctive markers, so they do not prove general semantic accuracy. OpenViking resources are not equivalent to extracted memory records.

The original V1 benchmark runs use synthetic canonical projections above current production candidate-queue cap (500). The measured 1M FTS5 inventory is NOT evidence that production V1 can ingest one million records. Process RAM measurement absent.

Evidence on PC (not committed into ORION):
`E:\ORION-WORK\memory-benchmark-20261010\hybrid_scale_1m.json`
`E:\ORION-WORK\memory-benchmark-20261010\hybrid_final_report.json`
Additional evidence is in TheHands `thehands-results` branch session records for the corresponding runs.

## What was added in ORION V3
`src/orion_v3/modules/memory_indexed_retrieval_v2.py`: separate SQLite FTS5 disposable index, explicit project-scoped candidate IDs, source references, inactive exclusion, bounded result count. No dependency on OpenViking servers, cloud models, or Qwen per lookup.
`src/orion_v3/modules/memory_indexed_retrieval_v2_test.py`: standalone boundary tests.

The sidecar **does not** yet:
- hook into ORION's production canonical retriever;
- verify canonical active/superseded state at result consumption time;
- integrate a persistent vector index, semantic embedding updates or hybrid reranker;
- benchmark FTS5 with broad realistic queries under realistic concurrency;
- implement recovery/rebuild-on-drift or crash-safe sidecar migrations;
- prove execution on owner's Windows PC.

## Roadmap / priority sequence (current knowledge, not replacement for latest canonical project STATUS)
### A. Memory Hybrid V2 (new evidence-based candidate)
1. Physical GIT CHECK for isolated module and regression; investigate any failures; freeze only after verified PASS.
2. Contract-gated adapter to canonical memory projection (explicit project, active state and provenance). Never trust stale sidecar flags.
3. Rebuild/refresh derived FTS5 on approved memory changes, recovery on index corruption/drift, scoped invalidation, idempotent replay.
4. Optional embedding/vector sidecar (`nomic-embed-text`) for semantic miss cases; batch ingestion, project-aware vector filtering, cache, low idle CPU/GPU use.
5. Realistic mixed-query benchmark at 1K/10K/100K; 500K/1M *only if gated*; report ingestion/index update, RAM, end-to-end p50/p95/p99, security, semantic quality, supersession, provenance and adversarial cases.
6. Integrate only behind an OFF-by-default read-only feature flag and revert to frozen retrieval on failure. Owner approves production activation.

### B. Resume core ORION V3 program (higher authority priority; see docs/ROADMAP.md)
1. Deterministic ORION work loop and Vault state/evidence authority; STOP/replay/verification gates.
2. Windows sandbox confinement proof before autonomous untrusted writes. Keep real execution disabled until proven.
3. Reuse existing Qwen/local proposal and free-cloud review gateways; owner approval only at policy-defined important decisions.
4. Independent work Hand executes bounded operations; canonical verification determines truth.
5. Connect approved modules into existing PC/Android ORION UI, with remote work and no TheHands product coupling.
6. Project skills/connectors, offline Git forge integrations and OpenViking/Forge experiments only where measurable value warrants.
7. Regression, performance, observability and freeze each proven module.

### C. Cleanup policy
- Do not clean the user's actual memory: there is no evidence benchmark synthetic records entered ORION canonical memory.
- The ORION benchmark used temporary workspaces, already cleaned up by its harness; JSON reports are useful evidence and should be retained.
- OpenViking isolated test resources live in a separate benchmark workspace on the user's PC. Retain until results and source paths are verified; then delete only with explicit approval.
- Do not attempt to delete memories via ChatGPT personal Memory settings or claim personal memory was cleaned.

## Novelty and decision
SQLite FTS5 indexed retrieval, embeddings and hybrid search are standard retrieval engineering, not a newly invented technique. The project-specific accomplishment is measuring their benefits and limitations on the owner's PC, demonstrating exact lookup at 1M synthetic records, and identifying a low-power modular path compatible with ORION's frozen authority model. This is evidence for a worthwhile prototype, **not a production breakthrough or finished integration**.
