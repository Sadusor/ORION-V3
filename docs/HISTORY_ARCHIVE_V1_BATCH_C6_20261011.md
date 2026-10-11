# HistoryArchive V1 — Combined C6 regression qualification

Status: COMMITTED, NOT PHYSICALLY VERIFIED, NOT LIVE.

Previous Windows evidence: C5 44/44 PASS (TheHands session 764e9e6a3f37, tested commit 937c637353cd9e75757f699e42306bcd1a578283).

This batch adds independent client tombstone reconciliation (`history_archive_client_reconcile_v1.py`) and six disposable-data tests. The reconciliation function removes all owner-deleted conversation/message records from a proposed offline snapshot while refusing cross-project collisions, without trusting the client's deletion flags. It is not connected to PC or Android clients and does not modify live state.

Qualification target: **50 tests** (44 previous + 6 new) in ONE TheHands PowerShell 1 GITCHECK, plus compile verification. No PC/Android changes, actual source-side text capture, production cross-process lock, authenticated delete HTTP endpoint, or feature activation. Existing Stage A/B/C1/C2/C3/C4/C5 code remains frozen; Gitea and TheHands runtime untouched.

Remaining hold: Android local SQLite and PC live store can truncate at 8,000 characters; full original text is available only when captured before that boundary. This batch demonstrates server-side original-text retention from a raw payload, not an end-to-end Android transport proof. Real owner credential enrollment and operating-system protection still unqualified.

After physical PASS, freeze this additive module and proceed to actual clients in one bounded subsequent batch rather than repeated small module tests.

## Correction (2026-10-11)
The C6 test formerly asserted that the legacy live ChatHistoryStore truncated text to 8,000 characters. That assertion was removed: it is not an acceptance criterion for permanent history. The test now checks only complete original-message preservation by the archive. This test does not certify the full current PC/Android text ingestion path, which must be verified against the previously implemented unlimited-chat behavior before production activation.
