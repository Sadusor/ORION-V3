# Myownqwen — Combined ChatGPT + Gitea Training and Memory Roadmap
Date: 2026-10-17
Status: **OWNER ORDER CONFIRMED: GITEA TRAINING BEFORE ALL-DATABASE MEMORY. PLANNED; NO INTEGRATION OR TRAINING CHANGES.**
Destination: Standalone `E:\QWEN-TRAINING-PIPELINE`. ORION-V3, TheHands and TheLoop are independent and remain frozen/unmodified.

## Current facts and guardrails
- Current independent Myownqwen V2.1 Soup training: `data\training\myownqwen_v2_1`; 3,017 training examples and 296 reserved validation examples; 755 expected steps. User later reported ~83%, not verified by this branch.
- Do not stop/restart/reconfigure active training; preserve checkpoint, source data, private SQLite stores and original Ollama tags.
- **Source-of-truth:** local Git repositories and verified test evidence for code; historical ChatGPT messages are conversations, not proven correct solutions.
- **Data policy:** private ChatGPT exports and Gitea database stay on local Windows machine; do not upload chat content, repositories, credentials or trained adapters to GitHub. This branch holds only pre-existing ORION code donor files and plans.
- **Freeze:** ORION canonical memory, V1/V1.1, integrity, promotion/supersession and the indexed V2 source remain untouched. Copied code is reference only, not permission to overwrite frozen modules.

## Milestones — owner-confirmed order (2026-10-17)
**Sequence: complete existing ChatGPT run → train using curated Gitea projects → connect memory to ALL eligible databases.** Do NOT build or activate the combined memory pipeline before the Gitea-training milestone. Read-only source discovery, dataset preparation and testing are allowed prerequisites for training, not a deployment of the future memory service.

### M1 — Finish and freeze the current ChatGPT-trained model
1. Verify V2.1 completion and full saved adapter, logs, held-out evaluation and baseline comparison.
2. Preserve/qualify the output under a distinct model ID without touching original Qwen/Ollama models; record a rollback point.
3. Do not interrupt or reconfigure training in progress.

### M2 — Read-only Gitea inventory and training dataset
1. Enumerate all local Gitea repositories from actual repository storage, not solely application database metadata; record project/repository IDs, commit SHA, branch, languages, license, tests, source paths and whether completed/unfinished/unknown.
2. Inventory full project structure, cross-file dependencies, documentation, test suite, meaningful commits and fixes. Preserve source and execution evidence; do not modify original Gitea data.
3. Build a **project-aware Gitea training corpus** using architecture explanations, verified bug→fix patches, feature→implementation, tests, and vetted code examples. Use unfinished projects as context/tasks, **not** assumed-correct answers.
4. Screen credentials, private material, rights/licensing, generated noise, duplicates and token truncation; separate train/validation/test by projects or commits to prevent leakage.
5. Preserve representative ChatGPT examples if necessary to avoid behavioral forgetting. Repository size is not a measure of training quality.

### M3 — Train and evaluate Myownqwen on Gitea (BEFORE memory pipeline)
1. Train a **new isolated Gitea-specialization adapter** on the curated dataset, using measured GPU budgets and resumable checkpoints. No in-place edits to frozen V2.1 adapter.
2. Benchmark base Qwen, ChatGPT-trained V2.1 and Gitea-trained candidate on held-out multi-file coding tasks, bugs, project architecture understanding, test correctness, Greek/English responses and conversation regression.
3. If a stage fails, retain prior working model and artifacts. Promote/freeze only after a verified PASS and owner acceptance.
4. Training learns patterns and conventions, **not guaranteed literal recall of entire repositories**; exact files are handled by M4.

### M4 — Connect a unified, LOCAL, read-only memory pipeline to ALL user's eligible databases (AFTER Gitea training)
1. Begin with a read-only inventory and owner-approved connector matrix; distinguish database engines, storage paths, schemas, access rights, freshness and source-of-truth. **ALL** means all discovered and authorized compatible data sources, not unrestricted database access.
2. Include ChatGPT conversations and code-index SQLite, local Gitea repositories/metadata/history, relevant standalone Myownqwen memory/training/evaluation stores, and any other databases explicitly discovered and approved. ORION's canonical memory may be *referenced* by an allowed read-only adapter, never modified or silently merged. Do not assume all stores reside in the same engine or directory.
3. Introduce **separate read-only adapters** per source; use consistent provenance fields: source database, project, conversation/repository/file identifier, commit/version, author/trust level, timestamp, active/superseded status and permission scope.
4. Adapt frozen ORION FTS5 indexed-retrieval and Gitea-index DONOR code into *new Myownqwen modules*, without modifying upstream modules, policies, or original DBs. Derived indexes must be disposable and rebuildable.
5. Enforce project isolation, permissions, source freshness, revocation/supersession, bounded context/token budgets, prompt-injection resistance and cited snippets. No default wildcard cross-database retrieval. If multiple projects must be searched, owner-authorized explicit selection is required.
6. Evaluate cross-source queries (past ChatGPT decision → current Gitea implementation → verified tests), end-to-end precision/recall, realistic p50/p95, update/rebuild, corrupted index recovery and negative tests. Add embeddings only after measured FTS5 misses.
7. Provide model-facing retrieval/search, not direct write access. No cloud uploads of private DBs, code, secrets or embeddings.

### M5 — Controlled continuation of unfinished projects
1. Qwen retrieves approved current files and relevant historical decisions, then proposes bounded edits.
2. Execute in isolated checkouts with external permissions, STOP, tests/GITCHECK and canonical verification — never treat model assertions as PASS.
3. Review and store verified lessons as future training candidates; preserve module-only freeze discipline.

## ORION V3 donor material — copied verbatim into this BRANCH ONLY
Source repository: `Sadusor/ORION-V3`, main commit `612944632126f2d83b0cc76258fddc957ba61e99`.
Copied paths beneath `donors/orion-v3-memory-20261017/` mirror source paths.
- `memory_indexed_retrieval_v2.py` + test — FTS5 project-bound candidate IDs, disposable sidecar, no canonical authority.
- `gitea_code_index_v1.py` + test — project/repo/commit-specific SQLite FTS5 code chunks.
- `gitea_readonly_v1.py`, `gitea_codebase_map_v1.py`, `gitea_source_context_v2.py`, `gitea_relevance_v2.py`, `gitea_auto_index_v2.py` — upstream-specific Gitea read/search adapter and support.
- ORION indexed V2 PASS checkpoint + hybrid benchmark roadmap (as contextual references).
**DO NOT import donor files directly as a finished Myownqwen product.** The auto-index module is hardcoded to ORION project `orion-v3` and a particular local Gitea endpoint. Rebuild new Myownqwen adapters against its own source data, with independent tests and explicit owner approval.

## Acceptance gates
- Read-only inventory accurate; no source edits or exposure of private data.
- Retrieval enforces project isolation, provenance, commit consistency, revocation/supersession, safe UTF-8/Greek queries, bounded budgets, and corrupted-index rebuild.
- Cross-source query tests demonstrate correct citations and distinguish user instructions from stale assistant suggestions.
- Training dataset records licensing, redaction, provenance, labels, no train/eval leak and full answer tokenization.
- Holdout coding tests must materially improve without regression; freeze each passing new module.

## Execution state
**Only a source-code donor copy and plan on an isolated ORION GitHub branch.** No Windows writes, Gitea imports, model tuning, GitHub fork changes or live training process interventions performed.
