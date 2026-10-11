# ORION V3 — HistoryArchive Stage B Qualification
Date: 2026-10-11
Status: WINDOWS GITCHECK PASS / EXPERIMENTAL INTEGRATION OFF BY DEFAULT

## Evidence
- TheHands PowerShell 1 published session: a01537046e02.
- Evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/a01537046e02.json
- ORION tested commit: 13dcab35df928d06051e0e91ee92853bf6e73ae3
- TheHands task commit: 4ad02efd7b84b0024729dc668c662d3bc08afa42
- Test result: 11 tests ran; 11 passed in 1.531 s; py_compile succeeded.
- Live ORION unchanged.

## Frozen boundaries
Freeze the standalone archive module at Stage A proven commit f5329013ce6cd06d8e9ef118bcf56e4cb60776bb. Stage B adapter and experimental server seam are qualified for tested scope only. No changes to frozen ChatHistoryStore, canonical memory, verifier, approval, STOP, Gitea code, or TheHands product runtime.

## Tested behaviors
- Archive-before-live-sync on disposable databases; original >8000-character text retained.
- Idempotent sync replay and original archive persistence.
- Archive failure prevents calling live sync.
- Missing explicit project scope and conversation rows flagged deleted are refused in experimental mode.
- Source modules compile, Windows connection cleanup.
- The original live path remains when environment ORION_HISTORY_ARCHIVE_V1_EXPERIMENTAL is not 1.

## Unresolved production blockers
- Verify actual Android/Windows message and delete/archival protocol; boolean deleted flag alone is not a trusted owner Delete event.
- Enforce owner Delete at the actual authenticated boundary; stale PC/phone replays must not resurrect removed messages.
- Resolve cross-file archive/live SQLite partial failure recovery and upstream text truncation before live enablement.
- Integrate ordered current-conversation context and long-term archive search in separate qualified modules; then per-request Qwen operating guide.
- Do not enable experimental setting on owner PC before cross-client tests, backup, and explicit activation approval.

This is a Stage B test PASS, not a full long-term memory feature release.
