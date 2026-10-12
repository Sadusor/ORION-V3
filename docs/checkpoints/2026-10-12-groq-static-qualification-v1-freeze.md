# Groq Static Qualification V1 — FROZEN (2026-10-12)

- Branch: spike/windows-isolation-preflight-20261008
- Qualified source commit: 0066404882d2437ec30d392e5f9302657d040bc0
- Module: src/orion_v3/work_loop/groq_static_qualification_v1.py
- Tests: tests/test_groq_static_qualification_v1.py
- Physical TheHands evidence: https://github.com/Sadusor/TheHands-/blob/thehands-results/docs/thehands/session-results/053a87a46d32.json
- Evidence result: PASS, 9/9 unittest checks, 0.001 seconds.
- Production unchanged. No generated code executed, no provider calls.
- Gate checks shape and replayed identical outputs. It is NOT a sandbox, a full security proof, a functional verifier, or a current-request attribution proof.
- Freeze: do not edit the qualified module; add new modules for further functionality.
- Next: test isolated qualification of trusted fixture code; only execute model-produced code once an actual isolation boundary is separately verified.
