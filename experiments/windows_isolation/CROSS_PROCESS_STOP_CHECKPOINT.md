# Cross-process STOP qualification checkpoint — 2026-10-08

Evidence: GitCheck session ed44529f025e, source fc19e0f: CROSS_PROCESS_STOP_GAP CONFIRMED. Independent process committed despite STOP on another process's CommitCoordinator. This is a diagnostic pass and security failure.

Real Vault integration: session 0e3dfc275fe5, 4/4 passed. Safe branch sync: session d195ee4c6307, HEAD 45e0dcc, untracked Android files preserved.

Inspected: work_loop/stop.py only defines StopSource protocol; commit_coordinator.py uses process-local RLock/generation; vault_lock.py already uses SQLite BEGIN IMMEDIATE for cross-process serialization; vault.py enters commit_window before the Vault lock and replays pending transactions during recovery. scripts/stop_orion.ps1 is lifecycle shutdown, not a durable work-loop STOP authority.

Next gate: locate and bind one existing authoritative task STOP owner, including durable state, scope, generation, restart semantics. Serialize STOP acceptance and Vault commit decision through a common cross-process ordering point. Never introduce a competing independent STOP service. Crash recovery must distinguish accepted pre-STOP commits from unaccepted post-STOP commits. No production execution until tests prove these properties. Remote V1 remains frozen. Network isolation remains unverified.
