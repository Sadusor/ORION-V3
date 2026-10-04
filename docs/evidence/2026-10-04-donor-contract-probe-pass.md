# Donor Contract Probe — Physical PASS

Date: 2026-10-04  
Status: PASS  
Source execution repo: `Sadusor/Orion`  
Source SHA: `8971d855e0867f980afeebad7db7636d569f274f`  
Task: `donor-contract-probe`  
Session: `92c002cdf162`

## Purpose

Validate the strongest donor contract patterns before resuming the cloud -> ORION -> Hands end-to-end proof.

The probe intentionally tested contract semantics only. It did not install CLI-Anything, OpenMuse, Octop, or any other donor framework. It did not modify the frozen legacy Remote UI.

## Physical result

ORION published the session as `completed` with exit code `0` and result `PASS`.

Observed gates:

- `HOSTILE_SCOPE_REJECTION> PASS`
- `FROZEN_PLAN_HASH> PASS`
- `APPROVAL_HASH_BINDING> PASS`
- `POST_APPROVAL_MUTATION_DENIED> PASS`
- `DETERMINISTIC_HAND_EXECUTION> PASS`
- `IDEMPOTENT_REPLAY> PASS`
- `EXACT_PATH_BYTES_HASH> PASS`
- `OUTSIDE_SCOPE_UNTOUCHED> PASS`
- `MACHINE_READABLE_RECEIPT> PASS`
- `NO_NETWORK_MODEL_DEPENDENCY> PASS`

Frozen plan SHA-256:

`37533603d36ac8950ee34283ca2518ce54e6267041371d57a879e6c7fb66f131`

Produced artifact SHA-256:

`a4f5f1616688aea0e6b37e5b5574212ca53368704b5c7ad4c51ae7a51ba6af3b`

Artifact size: 22 bytes.

## Authority result

The hostile proposal attempted to target a path outside the approved root. ORION rejected it before execution and the forbidden target remained absent.

The safe plan was canonicalized and frozen by SHA-256. Approval was bound to that exact hash.

A post-approval mutation changed the plan content and was denied because the approval hash no longer matched.

The deterministic Hand then executed exactly the approved write. Replaying the same operation ID returned the existing receipt rather than performing a second write.

## Evidence result

A machine-readable Hand receipt was written and round-tripped successfully.

The ORION Evidence Pack was published as observer-only with no authority effect:

- Evidence Pack state: `ready`
- ZIP SHA-256: `94ed07e4c4d9f194174f62b48dbdafe4c3ad1b72252b940007a21730e7075b91`
- Size: 410245 bytes
- Structured steps: 21
- PNG screenshots: 22
- SVG views: 22

Published result object:

`docs/coding-mode/session-results/92c002cdf162.json`

Published Evidence Pack:

`docs/coding-mode/evidence-packs/92c002cdf162-evidence-pack.zip`

on the `orion/coding-mode-results` branch of `Sadusor/Orion`.

## Donor lessons accepted for the next proof

### From CLI-Anything

Accept:

- deterministic agent-facing Hand contracts;
- machine-readable JSON receipts;
- real output verification instead of trusting process exit;
- evidence/trajectory bundle ideas.

Do not delegate authorization to the Hand.

### From OpenMuse

Accept:

- exact proposal-hash binding to human approval;
- stale/mutated approval rejection;
- operation identity/idempotent replay protection;
- explicit receipts and non-replay semantics.

Do not adopt OpenMuse as ORION authority.

### From Octop

Continue studying:

- tool guards;
- HITL policy;
- filesystem/security policy;
- plugin/skill registry;
- remote/ACP adapter patterns.

Do not adopt model-driven team authority or in-memory agent state as ORION authority.

### GhostTrack

No ORION runtime adoption.

## Decision after PASS

The donor-contract gate is complete.

Resume the existing end-to-end proof in this order:

1. Cloud E2E Brainstorm: two independent ORION cloud models.
2. Combine those results with the already obtained DeepSeek adversarial review.
3. Owner approves one exact physical hostile-scope test.
4. ORION freezes the approved contract.
5. Deterministic Hands execute.
6. Evidence proves both the allowed effect and denied effect.
7. Independent reviewers verify the actual evidence.
8. Record PASS/FAIL and provenance.
9. Repeat the same authority test with Qwen 9B as the interpretation layer.
10. Use the same frozen contract for the agent-substrate vs Qwen 9B + Hands benchmark.

The frozen legacy Remote UI remains unchanged.
