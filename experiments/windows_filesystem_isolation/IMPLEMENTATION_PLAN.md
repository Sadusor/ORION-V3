# Filesystem isolation V1 — implementation plan

## Candidate: restricted SID, not only disabled privileges

Windows restricted token access checking is a dual access check: normal token SIDs AND restricting SIDs must permit the access. Create a fresh random security identifier for a disposable restricted identity, add it to the token's restricting SID list, and grant that SID explicit workspace permissions. Files outside the workspace will lack that explicit permission, subject to verified behavior. The token still needs ordinary owner permission on the workspace. Do not mutate ACLs of existing files or folders.

The implementation must use documented Win32 token and security descriptor APIs and independently inspect the resulting child token. Prefer a narrowly-scoped helper over a generic privileged service. Fail closed if a token is not actually restricted or if an outside read succeeds.

## Physical fixture

Create two new disposable directories: INSIDE and OUTSIDE. The parent writes a random nonce to both; the child is asked to read/write inside and read outside. Confirm the outside read is denied and outside bytes remain unchanged. Repeat with child process launch, create, rename, and reparse-point traversal after baseline. Never use real user files for the test.

## Boundaries

No changes to TheHands product, Windows account rights, registry policy, or production directories. No arbitrary Work Hand commands. Job Object kill-on-close remains mandatory. Network egress and cross-process STOP ordering remain separate unqualified gates.

## Review requirement

Do not treat a PowerShell ACL error, a failed CreateProcessAsUser call, or a single denied path as proof. Require inside success AND outside denial on the same token, plus process-tree and reparse-path cases. Record exact Win32 errors and evidence.
