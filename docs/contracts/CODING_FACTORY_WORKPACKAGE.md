# ORION Coding Factory WorkPackage v0

Date: 2026-10-03

Status: **V3-RUN-018 TARGET**

## Purpose

A cloud coder should return exact candidate work bytes, not prose that a local model must reinterpret.

V0 freezes candidate code artifacts before any execution path exists.

```text
TaskPacket
 -> cloud coder
 -> exact PATCH / FILE bytes
 -> immutable Artifact Store
 -> WorkPackage hash
 -> independent REVIEW
 -> ORION DECISION
```

## Non-goals for V0

- no shell/runtime commands;
- no patch application;
- no Git worktree mutation;
- no cloud API call;
- no automatic approval;
- no Action Lease;
- no execution.

## Artifact Store

Artifacts are content-addressed by SHA-256.

Reads re-hash bytes. Direct filesystem tampering is detected.

Identical bytes deduplicate to the same artifact ID.

## WorkPackage

Required identity includes:
- project ID;
- task ID;
- attempt ID;
- exact base Git SHA;
- coder provider/model;
- prompt/response hashes;
- immutable artifact references;
- allowed/forbidden project-relative paths;
- verifier expectations;
- deterministic package SHA-256.

Supported artifact kinds:
- PATCH — exact patch bytes plus declared target paths;
- FILE — exact bytes plus CREATE/REPLACE and project-relative path.

PATCH target paths are mandatory and must satisfy the same scope rules as FILE artifacts.

## Blackboard

A package candidate is recorded as PROPOSAL.

An independent reviewer records REVIEW against the exact package ID/hash.

ORION records DECISION against that exact reviewed package.

An accepted candidate still has `execution_authority=false` in V0.

A REVIEW from package A cannot be reused to decide package B.

## V3-RUN-018 acceptance

Physically prove:
1. artifact deduplication;
2. artifact tamper detection;
3. exact base SHA validation;
4. out-of-scope FILE denied;
5. out-of-scope PATCH target denied;
6. deterministic package hash/manifest;
7. package reload verifies all artifact hashes;
8. PROPOSAL -> REVIEW -> DECISION causal chain;
9. all three records bind the same exact package hash;
10. cross-package review reuse denied;
11. accepted candidate creates no ACTION and grants no execution authority;
12. DB + artifact package survive close/reopen;
13. no network/model execution dependency.
