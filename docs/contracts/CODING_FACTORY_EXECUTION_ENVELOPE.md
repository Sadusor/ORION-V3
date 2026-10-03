# Coding Factory exact-SHA execution envelope

Status: **V3-RUN-020 candidate — not proven until the physical gate passes**

## Purpose

V3-RUN-018 proved immutable candidate WorkPackages.
V3-RUN-019 proved durable Attempt ownership and fenced execution leases.

This envelope is the first layer permitted to mechanically apply an accepted
WorkPackage, and only inside a disposable Git worktree.

## Required authority chain

```text
PROPOSAL
 -> REVIEW
 -> DECISION (candidate accepted, still no execution authority)
 -> current Attempt lease
 -> ACTION bound to package + lease generation
 -> disposable exact-SHA worktree
 -> EVIDENCE
 -> RESULT
```

A DECISION alone does not authorize effects.

The ACTION must bind:
- WorkPackage ID/hash;
- manifest artifact ID;
- exact base SHA;
- Attempt ID;
- current lease generation;
- current worker identity.

If ownership changes, the old ACTION becomes stale and cannot authorize the new
worker.

## Containment

Execution must:
1. reload and hash-check the immutable WorkPackage;
2. resolve the approved full Git SHA;
3. create a detached disposable worktree at exactly that SHA;
4. verify exact HEAD and clean pre-effect state;
5. revalidate the current Attempt lease before effects;
6. mechanically apply only WorkPackage FILE/PATCH artifacts;
7. stage changes only inside the disposable worktree;
8. compare actual Git changed paths against allowed/forbidden scope;
9. capture exact binary diff SHA-256 and resulting Git tree SHA;
10. run a deterministic verifier;
11. persist checkpoint/result truth;
12. remove the worktree on PASS, FAIL or Stop.

## Declared paths are not trusted evidence

PATCH target declarations are pre-effect metadata, not proof of what the patch
actually changed.

After application, the envelope uses Git's actual changed paths as the authority
check. A patch that claims an allowed target but changes another path must fail
and be discarded with the disposable worktree.

## V0 verifier

RUN-020 permits only deterministic `file_sha256` verification.

No model decides PASS.

## Prohibited operations

The V0 envelope contains no:
- `git push`;
- `git merge`;
- `git commit`;
- cloud/model call.

A resulting Git tree SHA is evidence only. No branch or remote is updated.

## Donor reuse

The Git worktree lifecycle follows the already physically proven legacy ORION
Remote exact-SHA/worktree/cleanup pattern.

OpenMuse remains useful for broader isolated-computer/container patterns, but it
does not replace this Git-specific envelope or ORION authority.
