# ORION V3 — Owner final deployment and preservation (2026-10-11)

## Intent

Owner requested final PC + production Android in-place update, remove the isolated ORION2 qualification package, save existing conversation data, and stop development. TheHands remains a separate product and execution remote. No modifications to frozen V1, existing memory modules, or live archive flags are authorized.

## Verified before deployment

- Existing archive indexing modules and tests: PASS in TheHands GITCHECK.
- Android UI owner backup export action: compiled and source-qualified. Actual private phone SQLite export FAILED at runtime; diagnostic commit was added; **no successful phone database export** has been verified.
- Production Android app already updated once in place after a passing signing-certificate check; user confirmed conversations still visible.
- Existing PC SQLite online backup and independent restore rehearsal: PASS in earlier TheHands GITCHECK.
- Isolated USB archive sync and deletion replay: PASS in earlier qualification; **not equivalent to production normal-network archive sync**.

## Owner final deployment procedure

Run `scripts/orion_owner_final_deploy_v1.ps1` through a pinned, successful TheHands PowerShell1 GITCHECK. It must:

1. Check qualification commit identity and **run live PC SQLite online backup + restore rehearsal**; stop immediately if it fails.
2. Discover PC production checkout from the single running ORION.exe executable path; reject dirty/diverged production checkouts and any confusion with the qualification repo.
3. Fast-forward production source to the exact qualified commit; use the existing PC updater with regression/build/rollback/health gates; wait for PASS.
4. Require one authorized connected Android phone, package identity and matching installed/candidate signing certificates; install production ORION with `adb install -r` only (never `uninstall` or data-clear production ORION).
5. Only after verified ORION installation, uninstall the separate `com.sadusor.orionv3.archivequal` (ORION2), as explicitly requested by owner.
6. Persist result and partial failure in `%LOCALAPPDATA%\\ORION-V3\\final-owner-deployment.json`.

## Explicit boundaries / still unverified

- Production archive HTTP and phone archive opt-in remain **disabled**. The existing normal PC↔phone history sync is separate; full permanent archive normal-network authentication has not been qualified.
- Existing production PC SQLite backup is verified, but **complete phone ↔ PC conversation parity** is not verified and phone database export has not passed; an in-place Android update preserves app data but does not itself prove an independent phone backup.
- If any gate blocks the update, stop and retain the current app/data. Never delete ORION2 early or claim all stages PASS without evidence.
- No automatic cleanup of backups or worktrees. Freeze after owner verifies successful deployment.
