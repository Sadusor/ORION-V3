# M3.5 signed-plan + native filesystem fixture checkpoint — 2026-10-08

Evidence: TheHands session `d4c2652c5b89`, source commit `4cf8a45bcce732d47da45b1378aa1e5169e33ba9`.
Evidence URL: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/d4c2652c5b89.json

Physical results: 28/28 existing offline tests PASS; 1/1 fixed-action preflight PASS; signed GREEN proposal preflight PASS (execution NOT_STARTED; workspace cleanup completed). Existing native AppContainer fixture: child created and assigned to Job Object; inside read/write ALLOW; outside read/write DENY; outside sentinel unchanged; child exit 0; profile deletion HRESULT 0; disposable build cleanup PASS.

Qualification boundary: signed preflight and native AppContainer are independent checks, **not an integrated Work Hand**. Network denial inconclusive; cross-process STOP/commit and descendant safety not qualified; real ORION executor disabled. Do not count this as full M3.5 execution or Milestone 4 PASS.

Next implementation: reuse native AppContainer launcher in a narrowly constrained, owner-approved, predeclared disposable write; independently verify exact bytes, STOP and Vault ordering before claiming real execution. Keep TheHands separate as manual test transport only. No duplicate sandbox, no frozen modules edited.
