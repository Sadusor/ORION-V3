# Work Loop Vault commit integration audit — 2026-10-08

Status: CODE INSPECTED / NOT PHYSICALLY QUALIFIED FOR REAL EXECUTION.

## Confirmed from current code
- `ProjectVault.record_verified_result` holds a process-local RLock and a SQLite BEGIN IMMEDIATE mutex.
- It recovers pending work before reading state; checks project/task; invokes an optional guard once; then writes pending, replaces STATE.md, appends JOURNAL.md and removes pending.
- `WorkLoopEngine.apply_evidence` evaluates the optional guard before calling Vault and Vault evaluates it again. Executor PASS remains rejected unconditionally by `independently_verified_pass`.
- `TransactionIdentity` is a separate, tested deterministic digest. It is not integrated into pending records, and it is not an authorization token.

## Specific missing boundaries
1. The commit guard is checked before pending is written; STOP occurring after that check can still allow the commit. Checking twice before the call does not close this window.
2. Pending recovery currently replays a prepared state/journal entry without revalidating STOP, source revision, or an independent verification decision. This is an interrupted transaction concern, not proof of a present exploit.
3. Pending records have no unique transaction identity; recovery deduplicates by substring search in JOURNAL.md. A journal line containing the same entry as a substring can cause a false deduplication.
4. No durable distinction exists between verified-but-not-committed and interrupted/unverified execution. Real execution must never be retried automatically after restart.
5. No OS-level filesystem isolation is established. Python path checks, SQLite locking and a Job Object are not an OS sandbox.

## Minimal next implementation batch
- Add a **versioned pending transaction schema** with transaction ID, explicit phase and exact journal marker; preserve migration/recovery for existing pending V1 records.
- Add fail-closed recovery rules: only complete a transaction with durable ORION-owned verified decision; otherwise mark interrupted/blocked and require review. Do not convert a pending executor receipt to PASS.
- Introduce an authority-owned commit coordinator that serializes STOP generation and commit decision. Define precisely the linearization point; distinguish STOP requested before commit from STOP after commit. Avoid claiming that filesystem and STOP are atomically synchronized across arbitrary processes.
- Tests: duplicate journal substring, replayed pending ID, STOP at each commit phase, malformed/tampered pending, interrupted before/after state replacement, and restart without re-execution.
- Keep real execution disabled. Only integrate transaction identity after a compatible migration strategy and tests.

## Freeze and evidence
The 2026-10-08 TheHands session `9ddb74b2fe42` physically reported 89 passed / 3 skipped for commit `afff355`; this is dry-run only. Existing Work Loop authority and Memory modules remain frozen by default. No production Vault changes were made by this audit.
