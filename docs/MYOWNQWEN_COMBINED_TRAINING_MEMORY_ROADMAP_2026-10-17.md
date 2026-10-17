# Myownqwen — Combined ChatGPT + Gitea Training and Memory Roadmap
Date: 2026-10-17
Status: **PLANNED / DONOR COPY ONLY. NO INTEGRATION, NO TRAINING CHANGES.**
Destination: Standalone `E:\QWEN-TRAINING-PIPELINE`. ORION-V3, TheHands and TheLoop are independent and remain frozen/unmodified.

## Current facts and guardrails
- Current independent Myownqwen V2.1 Soup training: `data\training\myownqwen_v2_1`; 3,017 training examples and 296 reserved validation examples; 755 expected steps. User later reported ~83%, not verified by this branch.
- Do not stop/restart/reconfigure active training; preserve checkpoint, source data, private SQLite stores and original Ollama tags.
- **Source-of-truth:** local Git repositories and verified test evidence for code; historical ChatGPT messages are conversations, not proven correct solutions.
- **Data policy:** private ChatGPT exports and Gitea database stay on local Windows machine; do not upload chat content, repositories, credentials or trained adapters to GitHub. This branch holds only pre-existing ORION code donor files and plans.
- **Freeze:** ORION canonical memory, V1/V1.1, integrity, promotion/supersession and the indexed V2 source remain untouched. Copied code is reference only, not permission to overwrite frozen modules.

## Milestones (in required order)
### M1 — Finish and qualify existing ChatGPT adapter
1. Wait for completion; verify saved LoRA files, trainer metadata, train/eval evidence, and hash outputs.
2. Merge, GGUF export, quantization and new separate Ollama tag using proven procedure only.
3. Baseline-vs-trained test including coding, Greek/English, conversation quality, hallucination, security and negative regressions.
4. Freeze successful adapter and test evidence; retain held-out evaluation questions.

### M2 — Read-only combined-source inventory
1. Map ChatGPT SQLite/message index and local Gitea bare repositories; identify correct paths and repository HEADs. No mutation.
2. Record repository, project ownership, default branch, commit SHA, language, tests, license, size and status (finished/unfinished/unknown).
3. Do not label unfinished code as successful; do not train on unreviewed secrets or materials without sufficient rights.
4. Separate sources by project and provenance; never assume a ChatGPT assistant claim or PASS string is verified.

### M3 — Local memory / retrieval V1 (FIRST use donor references)
1. **Chat history index:** SQLite FTS5 over approved conversation excerpts. Preserve conversation IDs, author roles, timestamps, provenance, and project scope; exclude current conversation when appropriate.
2. **Gitea code index:** index read-only files at exact repository/commit/path/part coordinates with source identity; maintain revision and reject stale index on commit change.
3. **Candidate revalidation:** FTS sidecar results are non-authoritative candidates. Re-check permissions, project, active/revoked/superseded records, provenance, current Git revision, confidence and context budget before injecting snippets.
4. SQLite-first: measure precision/recall and p50/p95 against realistic queries; add embeddings only when measured lexical misses justify them. Never mistake ORION's 1M synthetic FTS5 lookup test for integrated production performance.
5. No cross-project/wildcard recall by default. Bounded snippets, token budget, safe query parsing, no code execution from retrieved text. Treat repo code and old messages as untrusted content.

### M4 — Whole-project learning corpus and fine-tuning V3 (separate experiment)
1. Build project maps: tree, APIs, symbols, imports, docs, tests, version/commit pointers, dependency links; retain retrieval to retrieve full exact source.
2. Extract instruction/correction pairs from reviewed commits and independently passing tests; focus on bug->fix, feature->patch, code->test, architecture explanations.
3. Include representative ChatGPT conversational cases to reduce skill regression; deduplicate and keep test cases project-disjoint where possible.
4. Prompt-completion/token-budget validation before training; reject wholly masked/truncated answers. Never treat arbitrary raw repository snapshots as correct labels.
5. Train a NEW isolated adapter; compare original, V2.1 and V3 on held-out code tasks, cross-file integration, test correctness and conversation retention. No automatic promotion.

### M5 — Controlled completion of unfinished projects
1. Qwen selects a project, retrieves exact latest files and accepted prior decisions, builds a bounded change proposal.
2. Runs only inside isolated checkout with owner-approved scope and deterministic GITCHECK/test evidence; STOP and approval gates remain external to model.
3. Save only verified corrections as future candidates; never let a model-generated PASS establish its own success.

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
