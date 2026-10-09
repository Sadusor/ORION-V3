# Decision proposal — Offline Git forge and ORION vault references (2026-10-09)

Status: BRAINSTORM CAPTURED; NOT APPROVED FOR IMPLEMENTATION.

## Owner idea
Provide a GitHub-like offline place to browse, copy, version and reuse code, including code that may or may not be used by ORION. Integrate ORION's vault concept without mixing their databases. Minimize disk usage and avoid affecting the current remote workflow.

## Candidate architecture
- Evaluate Forgejo as an optional local Git forge. Also compare simply using bare Git repositories plus a lightweight browser before requiring Docker/WSL2 on Windows.
- The forge owns Git objects, commit history and browsing. It is NOT the authority plane.
- ORION's separate vault/ledger owns references to immutable commit SHA, repository identity, scope, task ID, approval digest, verification evidence, provenance, supersession and STOP-related audit state.
- Code may exist in the forge without being trusted, approved, or used by ORION. Import is read-only by default; execution always uses existing approval/scope gates.
- No automatic ingestion of all donor repos. Owner controls mirrors and quotas; preserve TheHands as a separate project.
- Consider local-only binding, authentication, backups, offline operation, malicious repository content, secrets scanning and storage quotas.
- Storage figures (image size, RAM, 100 repositories, 20 GB) quoted by DeepSeek are unverified estimates, not ORION measurements. Git LFS alone does not enforce disk quotas; large objects, LFS, actions artifacts and mirrors require retention policy.
- Avoid placing credentials or sensitive approval payloads into Git history; vault references may contain hashes and metadata, not secrets.

## Proposed staged validation
1. Compare zero-service Git + local UI versus Forgejo Windows deployment footprint, operational overhead, licenses, backup/restore and offline behavior.
2. Prototype a tiny repository with unapproved and approved commits; verify that only vault-referenced, owner-approved commits become eligible for ORION execution.
3. Benchmark disk and idle CPU/RAM on the owner's Windows PC before choosing a service.
4. Add a Codex-style UI entry point to browse code only after current council coding loop works.

## Current priority
Do not divert from existing Gemini/Groq council integration and live failover proof. Frozen V1 Remote and separate TheHands must not be modified by this design.
