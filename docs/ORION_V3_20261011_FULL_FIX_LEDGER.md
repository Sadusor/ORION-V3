# ORION V3 — October 11, 2026 Complete Fix / Recovery Ledger

Status: DOCUMENTATION ONLY. PRODUCTION FROZEN. Companion to `docs/ORION_V3_OWNER_FREEZE_20261011.md` and `docs/ORION_OWNER_FINAL_DEPLOY_20261011.md`.
No source, APK, PC binaries, SQLite, flags, tokens or live modules were changed by this ledger.

## Objective and frozen boundaries
Owner wanted permanent project-scoped conversation history, indexed retrieval, phone↔PC sync, safe database persistence, one ORION PC/Android release, removal of the separate ORION2 qualification APK, and source preservation in GitHub and local Gitea.
Frozen V1 Remote, TheHands product, working modules, owner-controlled canonical memory and STOP mechanisms were not to be redesigned. Only TheHands PowerShell-1 command was used as a remote GITCHECK/deployment runner. Production archive HTTP and experimental flags remain OFF; local memory candidates are **not** equivalent to proven permanent indexed ingestion.

## Feature implementations and tested scopes
1. Standalone archive SQLite `HistoryArchiveV1`: original messages, project boundaries, owner deletion/tombstones and replay safeguards; regression suites run through TheHands.
2. Disposable Android ORION2 migration/USB archive sync: real USB ADB test verified migration, device credentialed sync, deletion/replay blocking (earlier sessions `402ad9a857b3`, `d5048a07eb79`). This did **not** verify normal-network production archive sync.
3. `history_archive_search_projection_v1.py`: separate SQLite FTS projection, project-scoped retrieval, excludes deleted conversations. It is not the existing canonical memory retrieval index.
4. `history_archive_index_sync_v1.py`: refresh after a committed archive write or owner deletion; test passed (`dfe964cbfffd`); Windows test connections closed explicitly using `contextlib.closing` to prevent WinError 32.
5. `history_archive_indexed_boundary_v1.py`: opt-in composition for successful write/delete, reports index refresh failure without falsely claiming rolled-back archive transactions; tests passed (`f341b250de5f`). Still not wired as live production automatic ingestion.
6. `OwnerChatBackupV1.kt`: owner-chosen document URI, SQLite VACUUM INTO snapshot and integrity check; compiled in GITCHECK. Owner UI added via non-exported `OwnerChatBackupActivityV1.kt`, MainActivity native bridge and visible offline Settings button. Tests/build passed (`35cf59b562e0`, `d74a54fc4814`, `487830d60e48`). **Actual phone backup export displayed failure**; error logging was added in `68c1fe4` but successful phone export was not verified. Do not claim it passed.
7. Android UI correction: native Android menu invisible inside WebView shell; backup button put into actual Settings sheet through `android/app/src/main/assets/offline/index.html` and Javascript interface. Owner confirmed app and old conversations visible after updates. Existing swipe lag predates update and was deferred.

## Release failures, exact cause, correction, evidence
- First attempt to automate final PC+Android deployment (`12cc8e0`) FAILED (`8460163c2cfd`) **before production mutation**: PowerShell syntax error (truncated origin-url check and accidentally duplicated script tail). Repaired in `c1e7d5e`; next TheHands pin `646ec75`.
- Next attempt FAILED (`508387f5278b`) after **PC online backup and independent restore PASS**, because production Git checkout was dirty. Read-only diagnostic TheHands session `7ad2feb9ff3e` showed only untracked `android/.gradle/` and `android/local.properties`; production checkout `E:\ORION-V3-UPDATE-CANDIDATE-20261010`, then HEAD `adcd05b`. Fix was to allow exactly those two generated/local Android paths without deleting or resetting them (`89842bf`). Nothing else ignored.
- Next attempt FAILED (`da55feb179d7`) **after successful PC update and Android `adb install -r`**. PC updater returned PASS with running commit `89842bfcf5d7eef00d94467c268f6458972b2a4d`; Android streamed installation returned Success, but launch verifier used incorrectly escaped regex and reported process unverified. It correctly did not remove ORION2. Repaired regex in `8631b0a`, and switched TheHands to lightweight post-install proof (no reinstall or retests) in `9d30e34`.
- FINAL deployment session `baf6bf738ba6` PASS: PC running desired commit, PC backup present and prior restore PASS, Android launch PASS, ORION2 uninstalled PASS, archive-network disabled, exit zero. Owner confirmed both apps feel fine. No production app data-clear/uninstall of ORION.
- Some earlier backup UI update staging involved Android APK signature validation. Owner ran SHA256/signature preflight and confirmed `SIGNING_CERTIFICATE_MATCH> PASS`, then in-place install; existing chats remained visible.
- Final code-freeze record created as `docs/ORION_V3_OWNER_FREEZE_20261011.md` at GitHub commit `0465557c1f148462c8b7e6e9572c76f860c702ca`. Documentation-only commit is not the running production code version.

## Freeze and Gitea sync reality
TheHands session `9cf5e01326f5` PASS: qualification checkout fast-forwarded to freeze document commit `0465557`, verified document; found only Git remote `origin`. **Gitea push was BLOCKED_NO_UNAMBIGUOUS_GITEA_REMOTE**. GitHub source preserved; Gitea source NOT mirrored in this session. No force push. Do not describe a PASS session as a successful Gitea mirror without checking its labeled subresults.

## Data retention and security
PC chat SQLite is in `%LOCALAPPDATA%\ORION-V3\chat_history.sqlite3`; backups under `%LOCALAPPDATA%\ORION-V3\history-archive-backups`. A PC online backup+restore rehearsal PASS was recorded; do not move actual chat DBs or credentials into Git repositories. Production Android stores chat in its app-private SQLite. Its export failed at runtime, and exact phone↔PC parity remains UNVERIFIED. ORION2 was a separate disposable package, not TheHands. Never change live release flags without a new explicit owner-approved qualification.

## Frozen status and next-day resume
The owner said the updated ORION PC and Android work and asked to stop for the day. Treat all passing modules and this release as frozen; don't repeat solved tests or reopen implementation without owner instruction.
If requested later: (1) identify/add correct local Gitea remote and perform strictly fast-forward source mirror; (2) verify phone↔PC full history parity and persistent archived retrieval separately; (3) profile sluggish Android swipe as an independent performance task. None of these are required to conclude the accepted PC/Android release.
