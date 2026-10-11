# HistoryArchive Stage C5 — Owner Capability (Not Live)

Status: SOURCE COMMITTED / PHYSICAL GITCHECK PENDING.

C4 completed 37/37 physical Windows tests: TheHands session 8b24f7c4487a, tested ORION commit 81d4d615c71beae562196d180363f4665bae5b28. C4 tests used a stub owner verifier; paired-device authentication alone does not authorize destructive deletion.

C5 introduces isolated `history_archive_owner_capability_v1.py`, a distinct cryptographically random owner secret stored as a SHA-256 digest under the designated state directory. Enrollment, rotation and revocation demand a trusted physical-confirmation argument, and the current secret is necessary for rotation. This argument is only a testable API contract, **not** real proof of physical presence; it MUST NOT be bound to client input. Do not expose enrollment, raw token or digest through HTTP, chat logs, GitHub, or the Android app. Windows ACL/DPAPI protection and secure operational enrollment remain unqualified. The new file is not imported in live product_server and does not create a real owner token on the user machine.

Seven new isolated C5 tests verify fail-closed unenrolled state, enrollment authorization, verification, refusal of duplicate enrollment, revocation, rotation and persistence across object re-creation. Run all 37 previous tests plus seven C5 tests (44 expected), and Python compile on TheHands PowerShell 1. Any test failure means no PASS/freeze.

All Stage A/B/C1/C2/C3/C4 modules and frozen runtime untouched. No live archive, deletion HTTP route, cross-process sync gate, original-message capture or PC/Android tombstone reconciliation activated.
